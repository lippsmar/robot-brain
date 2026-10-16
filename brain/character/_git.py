"""One hardened way to call git, shared by the core check and the live profile.

- Absolute path to git, fixed arguments, no shell, timeout.
- Clean environment: no GIT_DIR or similar from outside, no system or global config
  (`GIT_CONFIG_NOSYSTEM`, `GIT_CONFIG_GLOBAL=/dev/null`), HOME outside any work tree.
- No hooks, no fsmonitor, no signing, `safe.directory` only for the given repository.
"""

import os
import shutil
import subprocess

TIMEOUT_S = 10


class GitError(Exception):
    """git is missing, timed out or failed."""


def find_git(git="git"):
    executable = shutil.which(git)
    if executable is None:
        raise GitError(f"git nicht gefunden ({git})")
    return executable


def run_git(repo, *args, git="git", extra_env=None, check=True):
    """Run git in `repo`; return the completed process. With `check`, a non-zero exit raises GitError."""
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "LC_ALL": "C",
        "HOME": "/nonexistent",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
    }
    env.update(extra_env or {})
    command = [
        find_git(git),
        "-c",
        f"safe.directory={repo}",
        "-c",
        "core.hooksPath=/dev/null",
        "-c",
        "core.fsmonitor=false",
        "-c",
        "commit.gpgsign=false",
        "-C",
        str(repo),
        *args,
    ]
    try:
        result = subprocess.run(  # noqa: S603  fixed arguments, no shell
            command, capture_output=True, text=True, timeout=TIMEOUT_S, env=env, check=False
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise GitError(f"git fehlgeschlagen: {error}") from error
    if check and result.returncode != 0:
        raise GitError(f"git {args[0]} fehlgeschlagen: {result.stderr.strip()[:200]}")
    return result
