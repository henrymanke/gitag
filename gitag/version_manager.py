import logging
import re
import tomllib
from pathlib import Path
from typing import Callable, Optional

from gitag.config import DEFAULT_LEVELS, DEFAULT_VERSION_PATTERN, BumpLevel, MergeStrategy
from gitag.config_validator import validate_config

logger = logging.getLogger(__name__)


class VersionManager:
    def __init__(self, config_path: Optional[str] = None):
        self._config = {}
        self.prefix = ""
        self.suffix = ""
        self.patterns = {}
        self.merge_strategy = MergeStrategy.AUTO

        config_path = config_path or "pyproject.toml"
        self.load_config_from_pyproject(config_path)

    def load_config_from_pyproject(self, config_path: str):
        config: dict = {}

        # Load default configuration
        defaults_path = Path(__file__).parent.parent / "default_pyproject.toml"
        if defaults_path.exists():
            with open(defaults_path, "rb") as file:
                default_config = tomllib.load(file)
                config.update(default_config.get("tool", {}).get("gitag", {}))
        else:
            logger.warning(f"⚠️ Default config {defaults_path} not found.")

        # Load user configuration
        pyproject_path = Path(config_path)
        if pyproject_path.exists():
            with open(pyproject_path, "rb") as f:
                try:
                    user_config = tomllib.load(f)
                    user_tool_config = user_config.get("tool", {}).get("gitag", {})
                    config.update(user_tool_config)
                except Exception as e:
                    logger.error(f"❌ Error loading {config_path}: {e}")
        else:
            logger.warning(f"⚠️ User config {config_path} not found, using defaults.")

        # Apply basic settings
        self.pattern = config.get("version_pattern", DEFAULT_VERSION_PATTERN)
        self.prefix = config.get("prefix", "")
        self.suffix = config.get("suffix", "")

        # Load regex patterns for bump strategy (or fallback on DEFAULT_BUMP_KEYWORDS)
        raw_patterns = config.get("patterns")
        if isinstance(raw_patterns, dict):
            self.patterns = raw_patterns
        else:
            if raw_patterns is not None:
                logger.error(
                    f"❌ Invalid 'patterns' config: expected table, got {type(raw_patterns).__name__}"
                )
            # Fallback auf DEFAULT_BUMP_KEYWORDS aus gitag.config
            from gitag.config import DEFAULT_BUMP_KEYWORDS

            self.patterns = {
                level.name.lower(): patterns
                for level, patterns in DEFAULT_BUMP_KEYWORDS.items()
            }
            logger.info("⚠️ Using default bump-patterns from DEFAULT_BUMP_KEYWORDS")

        # Merge strategy
        self.merge_strategy = MergeStrategy(config.get("merge_strategy", "auto").lower())

        # Set bump strategy
        self.strategy = self.regex_bump_strategy

        # Validate configuration
        validation_errors = validate_config(config)
        if validation_errors:
            logger.warning("⚠️ Configuration issues detected:")
            for error in validation_errors:
                logger.warning(f" - {error}")

    def regex_bump_strategy(self, msg: str) -> BumpLevel:
        msg = msg.strip()
        # Check in the order MAJOR (0), MINOR (1), PATCH (2)
        for level in sorted(BumpLevel, key=lambda lvl: lvl.value):
            for pattern in self.patterns.get(level.name.lower(), []):
                try:
                    # Case-sensitive regex match (inline (?i) still works)
                    if re.search(pattern, msg):
                        return level
                except re.error as e:
                    # Invalid regex → as simple substring check
                    logger.error(f"❌ Invalid regex '{pattern}': {e}")
                    if pattern and pattern in msg:
                        return level
        # No pattern match → Patch
        return BumpLevel.PATCH

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
        categorized = {str(level): [] for level in DEFAULT_LEVELS}
        for msg in commits:
            level = self.strategy(msg)
            categorized[str(level)].append(msg)
        return categorized

    def get_default_version(self) -> str:
        return f"{self.prefix}0.0.0{self.suffix}"

    @property
    def pattern(self) -> str:
        return self._config.get("pattern", DEFAULT_VERSION_PATTERN)

    @pattern.setter
    def pattern(self, value: str):
        self._config["pattern"] = value

    @property
    def strategy(self) -> Callable[[str], BumpLevel]:
        return self._config.get("strategy")

    @strategy.setter
    def strategy(self, value: Callable[[str], BumpLevel]):
        self._config["strategy"] = value
