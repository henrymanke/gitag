import argparse
import os
from gitag.auto_tagger import GitAutoTagger
from gitag.config import MergeStrategy


def detect_ci_context() -> tuple[str, bool, bool]:
    env = os.environ
    if "GITHUB_ACTIONS" in env:
        return ("github", env.get("GITHUB_EVENT_NAME") == "pull_request", env.get("GITHUB_REF") == "refs/heads/main")
    if "GITLAB_CI" in env:
        return ("gitlab", bool(env.get("CI_MERGE_REQUEST_ID")), env.get("CI_COMMIT_REF_NAME") == "main")
    if "CIRCLECI" in env:
        return ("circleci", bool(env.get("CIRCLE_PULL_REQUEST")), env.get("CIRCLE_BRANCH") == "main")
    if "BITBUCKET_BUILD_NUMBER" in env:
        return ("bitbucket", bool(env.get("BITBUCKET_PR_ID")), env.get("BITBUCKET_BRANCH") == "main")
    if "JENKINS_HOME" in env:
        return ("jenkins", bool(env.get("CHANGE_ID")), env.get("BRANCH_NAME") == "main")
    return ("unknown", False, False)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Automatic git tagger using commit messages.")
    parser.add_argument("--dry-run", action="store_true", help="Preview without creating a tag")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--push", action="store_true", help="Push the tag to remote")
    parser.add_argument("--since-tag", type=str, help="Compare commits since this tag")
    parser.add_argument("--changelog", action="store_true", help="Write changelog")
    parser.add_argument(
        "--merge-strategy",
        choices=[e.value for e in MergeStrategy],
        default=None,
        help="Strategy to determine which commits to include: auto, always, or merge_only",
    )
    parser.add_argument(
        "--no-merges",
        dest="include_merges",
        action="store_false",
        help="Exclude merge commits from changelog"
    )

    parser.add_argument("--config", type=str, help="Path to pyproject.toml config")
    parser.add_argument("--pre", type=str, help="Append pre-release label (e.g. alpha.1)")
    parser.add_argument("--build", type=str, help="Append build metadata (e.g. 001abc)")
    parser.add_argument("--ci", action="store_true", help="Enable CI detection mode")
    args = parser.parse_args(argv)

    if args.ci:
        ci_system, is_pr, is_main = detect_ci_context()
        print(f"ℹ️ CI mode detected ({ci_system})")
        if is_pr:
            args.dry_run = True
            print("🔁 PR detected – dry run enabled.")
        elif is_main:
            args.push = True
            print("🚀 Main branch – push enabled.")
        else:
            args.dry_run = True
            print("ℹ️ Non-main branch – dry run fallback.")

    tagger = GitAutoTagger(
        debug=args.debug,
        config_path=args.config,
        push=args.push,
        changelog=args.changelog,
        pre=args.pre,
        build=args.build,
        include_merges=args.include_merges,
        merge_strategy=MergeStrategy(args.merge_strategy or "auto"),
    )
    tagger.run(dry_run=args.dry_run, since_tag=args.since_tag)

    return 0


if __name__ == "__main__":  # pragma: no cover
    import sys
    sys.exit(main())
