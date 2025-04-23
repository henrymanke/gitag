import os
import re
import logging
from datetime import datetime
from typing import Optional
from gitag.config import DEFAULT_LEVELS, BumpLevel

logger = logging.getLogger(__name__)


class ChangelogWriter:
    def __init__(self, path: str = "CHANGELOG.md", include_date: bool = True, mode: str = "append"):
        self.path = path
        self.include_date = include_date
        self.mode = mode  # 'append' or 'overwrite'

    def _generate_entry(self, tag: str, categorized_commits: dict[str, list[str]]) -> str:
        lines = []

        # Entry header
        header = f"## {tag}"
        if self.include_date:
            header += f" - {datetime.today().strftime('%Y-%m-%d')}"
        lines.append(header)
        lines.append("")

        if not categorized_commits:
            lines.append("- No changes detected.")
        else:
            for level in DEFAULT_LEVELS:
                commits = categorized_commits.get(str(level), [])
                if commits:
                    lines.append(f"### {level.name.capitalize()} Changes")
                    lines.append("")
                    for commit in commits:
                        lines.append(f"- {commit}")
                    lines.append("")  # Blank line between sections

        return "\n".join(lines).strip()

    def _generate_toc(self, entries: list[tuple[str, dict[str, list[str]]]]) -> str:
        toc = ["# 📘 Changelog Overview", ""]
        toc.append("| Version | Date | Major | Minor | Patch |")
        toc.append("|:---------:|:------:|:--------:|:--------:|:--------:|")

        for tag, categorized_commits in entries:
            date = datetime.today().strftime("%Y-%m-%d")
            heading = f"{tag} - {date}"
            anchor = heading.lower().replace(" ", "-")
            anchor = re.sub(r"[^\w\-]", "", anchor)  # remove special characters except dashes

            major = len(categorized_commits.get(str(BumpLevel.MAJOR), []))
            minor = len(categorized_commits.get(str(BumpLevel.MINOR), []))
            patch = len(categorized_commits.get(str(BumpLevel.PATCH), []))

            toc.append(f"| [{tag}](#{anchor}) | {date} | {major} | {minor} | {patch} |")

        toc.append("")
        return "\n".join(toc)

    def write(self, tag: str, categorized_commits: dict[str, list[str]]):
        new_entry = self._generate_entry(tag, categorized_commits)

        entries = [(tag, categorized_commits)]
        existing_body = ""

        if os.path.exists(self.path) and self.mode == "append":
            with open(self.path, "r") as f:
                content = f.read()

            toc_pattern = r"(# 📘 Changelog Overview\n(?:\|.*\n)+\n?)"
            content = re.sub(toc_pattern, "", content, flags=re.MULTILINE).strip()

            blocks = [b for b in content.split("\n---\n") if b.strip()]
            for block in blocks:

                match = re.search(r"##\s+([^\s-]+)", block)
                if match:
                    prev_tag = match.group(1).strip()
                    if prev_tag != tag:
                        entries.append((prev_tag, {}))
                        existing_body += f"---\n\n{block.strip()}\n"

        toc = self._generate_toc(entries).strip()
        final_parts = [toc, '---', new_entry.strip()]

        if existing_body.strip():
            final_parts.append(existing_body.strip())

        final = "\n\n".join(final_parts) + "\n"

        with open(self.path, "w") as f:
            f.write(final)

        logger.info(f"📝 Changelog updated at {self.path}")
