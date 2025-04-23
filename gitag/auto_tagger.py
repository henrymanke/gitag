import logging
from gitag.git_repo import GitRepo
from gitag.version_manager import VersionManager
from gitag.changelog_writer import ChangelogWriter
from gitag.config import MergeStrategy

logger = logging.getLogger(__name__)


class GitAutoTagger:
    def __init__(
            self,
            debug: bool = False,
            config_path=None,
            push: bool = False,
            changelog: bool = False,
            pre=None,
            build=None,
            include_merges: bool = True,
            merge_strategy: MergeStrategy = MergeStrategy.AUTO,
    ):
        self.debug = debug
        self.push = push
        self.write_changelog = changelog
        self.pre = pre
        self.build = build
        self.include_merges = include_merges
        self.merge_strategy = merge_strategy or self.versioning.merge_strategy or MergeStrategy.AUTO

        self.repo = GitRepo(debug=self.debug, include_merges=include_merges, merge_strategy=self.merge_strategy)
        self.versioning = VersionManager(config_path)
        self.changelog_writer = ChangelogWriter()

    def run(self, dry_run=False, since_tag=None):
        current_tag = since_tag or self.repo.get_latest_tag()
        if not current_tag:
            logger.info("ℹ️ No previous tag found. Using all commits.")
            current_tag = self.versioning.get_default_version()

        commits = self.repo.get_commit_messages(since_tag=current_tag)
        if not commits:
            logger.warning("❌ No new commits found.")
            return

        bump_level = self.versioning.determine_bump(commits)
        new_tag = self.versioning.bump_version(current_tag, bump_level, pre=self.pre, build=self.build)

        extra_info = []
        if self.pre:
            extra_info.append(f"pre={self.pre}")
        if self.build:
            extra_info.append(f"build={self.build}")

        info_suffix = " " + " ".join(extra_info) if extra_info else ""

        logger.info(f"🆕 New version: {new_tag} ({bump_level}-release{info_suffix})")

        if self.write_changelog:
            categorized = self.versioning.categorize_commits(commits)
            self.changelog_writer.write(tag=new_tag, categorized_commits=categorized)

        if dry_run:
            logger.info("🚫 Dry run enabled - skipping tag creation.")
            return

        if self.repo.create_tag(new_tag, self.push):
            logger.info(f"✅ Tag {new_tag} created" + (" and pushed." if self.push else "."))
        else:
            logger.info(f"ℹ️ Tag {new_tag} already exists.")
