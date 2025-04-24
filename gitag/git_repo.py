import subprocess
import os
import sys
import logging
from typing import Optional
from gitag.config import MergeStrategy

logger = logging.getLogger(__name__)


class GitRepo:
    def __init__(self, debug: bool = False,
                 include_merges: bool = False,
                 merge_strategy: MergeStrategy = MergeStrategy.AUTO
                 ):
        self.debug = debug
        self.include_merges = include_merges
        self.merge_strategy = merge_strategy

    def configure_remote(self):
        token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
        repo = os.getenv("GITHUB_REPOSITORY")
        if token and repo:
            subprocess.run(["git", "config", "user.name", "ci-bot"], check=True)
            subprocess.run(["git", "config", "user.email", "ci@localhost"], check=True)
            subprocess.run([
                "git", "remote", "set-url", "origin",
                f"https://x-access-token:{token}@github.com/{repo}"
            ], check=True)
            logger.debug("Git remote configured using CI token.")
        else:
            logger.debug("No GH_TOKEN or GITHUB_TOKEN available. Skipping git remote config.")

    def get_latest_tag(self) -> Optional[str]:
        try:
            subprocess.run(["git", "fetch", "--tags"], check=True)
            result = subprocess.run(['git', 'describe', '--tags', '--abbrev=0'],
                                    capture_output=True, text=True, check=True)
            tag = result.stdout.strip()
            logger.debug(f"Latest tag: {tag}")
            return tag
        except subprocess.CalledProcessError:
            logger.debug("No tag via describe. Trying fallback.")
            try:
                result = subprocess.run(['git', 'tag', '--sort=-creatordate'],
                                        capture_output=True, text=True, check=True)
                tags = result.stdout.strip().split('\n')
                tag = tags[0] if tags else None
                logger.debug(f"Latest tag via fallback: {tag}")
                return tag
            except subprocess.CalledProcessError:
                logger.debug("No tags found.")
                return None

    def get_commit_messages(self, since_tag: Optional[str]) -> list[str]:
        try:
            cmd = ['git', 'log', '--pretty=%s']
            if not self.include_merges:
                cmd.append('--no-merges')

            range_arg = f"{since_tag}..HEAD" if since_tag else "HEAD"

            if self.merge_strategy in (MergeStrategy.MERGE_ONLY, MergeStrategy.AUTO):
                rev_list = subprocess.run(
                    ['git', 'rev-list', '--parents', '-n', '1', 'HEAD'],
                    capture_output=True, text=True, check=True
                )
                parts = rev_list.stdout.strip().split()

                if len(parts) >= 3:
                    parent1, parent2 = parts[1], parts[2]
                    range_arg = f"{parent1}..{parent2}"
                    label = "[AUTO]" if self.merge_strategy == MergeStrategy.AUTO else "[MERGE_ONLY]"
                    logger.debug(f"{label} Using feature-only commits: {range_arg}")
                else:
                    logger.debug(
                        f"[{self.merge_strategy.value.upper()}] HEAD is not a merge commit, "
                        f"falling back to: {range_arg}"
                    )

            elif self.merge_strategy == MergeStrategy.ALWAYS:
                logger.debug(f"[ALWAYS] Using full commit range: {range_arg}")
            else:
                logger.debug(f"[UNKNOWN] Merge strategy not recognized: {self.merge_strategy}")

            cmd.append(range_arg)

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            commits = result.stdout.strip().split('\n') if result.stdout.strip() else []
            logger.debug(f"Found commits: {commits}")
            return commits

        except subprocess.CalledProcessError as e:
            logger.error("❌ Error: Failed to get commit messages.")
            if self.debug:
                logger.debug(str(e))
            sys.exit(1)

    def tag_exists(self, tag: str) -> bool:
        try:
            result = subprocess.run(['git', 'tag'], capture_output=True, text=True, check=True)
            return tag in result.stdout.strip().split('\n')
        except subprocess.CalledProcessError:
            return False

    def create_tag(self, tag: str, push: bool) -> bool:
        if self.tag_exists(tag):
            logger.warning(f"⚠️ Tag '{tag}' already exists.")
            return False
        try:
            subprocess.run(['git', 'tag', tag], check=True)
            if push:
                subprocess.run(['git', 'push', 'origin', tag], check=True)
                logger.debug(f"🚀 Pushed tag '{tag}' to origin.")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to create or push tag '{tag}': {e}")
            sys.exit(1)
