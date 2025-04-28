from gitag.config import BumpLevel
from typing import Any


def validate_config(config: dict[str, Any]) -> list[str]:
    errors = []

    if "prefix" in config and not isinstance(config["prefix"], str):
        errors.append("prefix must be a string")

    if "suffix" in config and not isinstance(config["suffix"], str):
        errors.append("suffix must be a string")

    if "version_pattern" in config and not isinstance(config["version_pattern"], str):
        errors.append("version_pattern must be a string")

    if "patterns" in config:
        patterns = config["patterns"]
        if not isinstance(patterns, dict):
            errors.append("patterns must be a dictionary")
        else:
            for key, val in patterns.items():
                if key.upper() not in BumpLevel.__members__:
                    errors.append(f"Invalid bump level: '{key}'")
                if not isinstance(val, list) or not all(isinstance(v, str) for v in val):
                    errors.append(f"Values for patterns['{key}'] must be a list of strings")

    return errors
