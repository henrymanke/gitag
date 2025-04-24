from gitag.config import DEFAULT_BUMP_KEYWORDS, DEFAULT_LEVELS, DEFAULT_VERSION_PATTERN, BumpLevel, MergeStrategy
import re
import logging
import tomllib
from pathlib import Path
from typing import Callable, Optional
from gitag.config_validator import validate_config

logger = logging.getLogger(__name__)


def default_bump_strategy(msg: str) -> BumpLevel:
    msg_lc = msg.lower()
    for level, keywords in DEFAULT_BUMP_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in msg_lc:
                return level
    return BumpLevel.PATCH


class VersionManager:
    def __init__(self, config_path: Optional[str] = None):
        self._config = {
            "pattern": DEFAULT_VERSION_PATTERN,
            "strategy": default_bump_strategy,
        }
        config_path = config_path or "pyproject.toml"
        self.load_config_from_pyproject(config_path)
        self.prefix = ""
        self.suffix = ""

    def load_config_from_pyproject(self, config_path: str):
        pyproject_path = Path(config_path)
        if not pyproject_path.exists():
            logger.warning("pyproject.toml not found: using defaults")
            return

        with open(pyproject_path, "rb") as f:
            try:
                config = tomllib.load(f)
            except Exception as e:
                logger.error(f"Error loading {config_path}: {e}")
                return

        tool_config = config.get("tool", {}).get("gitag", {})
        self.pattern = tool_config.get("version_pattern", self.pattern)
        self.prefix = tool_config.get("prefix", "")
        self.suffix = tool_config.get("suffix", "")

        # ✅ Always validate config if file exists
        validation_errors = validate_config(tool_config)
        if validation_errors:
            logger.warning("⚠️ Configuration issues detected:")
            for error in validation_errors:
                logger.warning(f" - {error}")

        self.merge_strategy = MergeStrategy(
            tool_config.get("merge_strategy", "auto").lower()
        )

        keywords = tool_config.get("bump_keywords", {})
        if isinstance(keywords, dict) and any(keywords.values()):
            # Warn if any invalid keys
            invalid_keys = set(keywords.keys()) - {lvl.name.lower() for lvl in DEFAULT_LEVELS}
            if invalid_keys:
                logger.warning(f"Ignoring invalid bump levels in config: {invalid_keys}")

            # Map config strings to Enum
            mapped_keywords = {
                BumpLevel[level.upper()]: values
                for level, values in keywords.items()
                if level.upper() in BumpLevel.__members__
            }

            def strategy(msg: str) -> BumpLevel:
                msg_lc = msg.lower()
                for level, keys in mapped_keywords.items():
                    for kw in keys:
                        if kw.lower() in msg_lc:
                            return level
                return BumpLevel.PATCH

            self.strategy = strategy
        else:
            logger.info("No valid bump_keywords found; using default strategy")

    def determine_bump(self, commits: list[str]) -> BumpLevel:
        if not isinstance(commits, list) or not all(isinstance(c, str) for c in commits):
            raise TypeError("commits must be a list of strings")

        best_level = BumpLevel.PATCH
        for msg in commits:
            result = self.strategy(msg)
            if result.value < best_level.value:
                best_level = result

        return best_level

    def strip_prefix_suffix(self, version: str) -> str:
        if self.prefix and version.startswith(self.prefix):
            version = version[len(self.prefix):]
        if self.suffix and version.endswith(self.suffix):
            version = version[:-len(self.suffix)]
        return version

    def bump_version(
        self, current_version: str, level: BumpLevel,
        pre: Optional[str] = None, build: Optional[str] = None
    ) -> str:

        if isinstance(level, str):
            try:
                level = BumpLevel[level.upper()]
            except KeyError:
                raise ValueError(f"Invalid bump level: {level}")

        raw_version = self.strip_prefix_suffix(current_version)
        match = re.fullmatch(self.pattern, raw_version)
        if not match:
            logger.error(f"Invalid version format: {current_version}")
            raise ValueError(f"Invalid version format: {current_version}")

        major = int(match.group("major"))
        minor = int(match.group("minor"))
        patch = int(match.group("patch"))

        if level == BumpLevel.MAJOR:
            major += 1
            minor = patch = 0
        elif level == BumpLevel.MINOR:
            minor += 1
            patch = 0
        else:
            patch += 1

        version = f"{major}.{minor}.{patch}"
        if pre:
            version += f"-{pre}"
        if build:
            version += f"+{build}"

        return f"{self.prefix}{version}{self.suffix}"

    def categorize_commits(self, commits: list[str]) -> dict[str, list[str]]:
        categorized = {str(lvl): [] for lvl in DEFAULT_LEVELS}
        for msg in commits:
            level = self.strategy(msg)
            categorized[str(level)].append(msg)
        return categorized

    def get_default_version(self) -> str:
        return f"{self.prefix}0.0.0{self.suffix}"

    @property
    def strategy(self) -> Callable[[str], BumpLevel]:
        return self._config["strategy"]

    @strategy.setter
    def strategy(self, value: Callable[[str], BumpLevel]):
        self._config["strategy"] = value

    @property
    def pattern(self) -> str:
        return self._config["pattern"]

    @pattern.setter
    def pattern(self, value: str):
        self._config["pattern"] = value
