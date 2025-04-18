from enum import Enum
from enum import IntEnum

# --- Bump Level Enum ---


class BumpLevel(IntEnum):
    MAJOR = 0
    MINOR = 1
    PATCH = 2

    def __str__(self) -> str:
        return self.name.lower()

# --- Merge Strategy Enum ---


class MergeStrategy(str, Enum):
    AUTO = "auto"              # Detect if HEAD is merge, then show only commits of feature branch
    ALWAYS = "always"          # Always use <last_tag>..HEAD (alle Commits)
    MERGE_ONLY = "merge_only"  # Nur Feature-Branch aus aktuellem Merge


# --- Levels as List ---

DEFAULT_LEVELS = list(BumpLevel)


# --- Default Keywords for Conventional Commits ---

DEFAULT_BUMP_KEYWORDS = {
    BumpLevel.MAJOR: ["BREAKING CHANGE"],
    BumpLevel.MINOR: ["feat:"],
    BumpLevel.PATCH: [
        "fix:",
        "perf:",
        "refactor:",
        "docs:",
        "style:",
        "chore:",
        "test:",
        "ci:",
        "build:"
    ]
}


# --- Default SemVer Pattern (named groups!) ---

DEFAULT_VERSION_PATTERN = (
    r'^v?(?P<major>0|[1-9]\d*)\.'
    r'(?P<minor>0|[1-9]\d*)\.'
    r'(?P<patch>0|[1-9]\d*)'
    r'(?:-(?P<prerelease>'
    r'(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)'
    r'(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?'
    r'(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$'
)
