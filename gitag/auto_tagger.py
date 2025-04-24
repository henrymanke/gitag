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
        self.merge_strategy = merge_strategy

        self.versioning = VersionManager(config_path)
        self.repo = GitRepo(
            debug=self.debug,
            include_merges=self.include_merges,
            merge_strategy=self.merge_strategy or self.versioning.merge_strategy or MergeStrategy.AUTO,
        )
        self.changelog_writer = ChangelogWriter()

    def run(self, dry_run: bool = False, since_tag: str = None):
        tag_base = since_tag or self.repo.get_latest_tag()
        if not tag_base:
            logger.info("ℹ️ No previous tag found. Starting from 0.0.0 (virtual)")
            tag_base = None

        commits = self.repo.get_commit_messages(since_tag=tag_base)
        if not commits:
            logger.warning("❌ No new commits found.")
            return

        bump_level = self.versioning.determine_bump(commits)
        new_tag = self.versioning.bump_version(
            current_version=self.versioning.get_default_version() if not tag_base else tag_base,
            level=bump_level,
            pre=self.pre,
            build=self.build,
        )

        self._log_version_summary(new_tag, bump_level)

        if self.write_changelog:
            categorized = self.versioning.categorize_commits(commits)
            self.changelog_writer.write(tag=new_tag, categorized_commits=categorized)

        if dry_run:
            logger.info("🚫 Dry run enabled – skipping tag creation.")
            return

        if self.repo.create_tag(new_tag, self.push):
            logger.info(f"✅ Tag {new_tag} created" + (" and pushed." if self.push else "."))
        else:
            logger.info(f"ℹ️ Tag {new_tag} already exists.")

    def _log_version_summary(self, tag: str, level: str):
        parts = []
        if self.pre:
            parts.append(f"pre={self.pre}")
        if self.build:
            parts.append(f"build={self.build}")
        suffix = f" ({level}-release {' '.join(parts)})" if parts else f" ({level}-release)"
        logger.info(f"🆕 New version: {tag}{suffix}")
