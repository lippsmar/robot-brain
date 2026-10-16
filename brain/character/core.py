"""Start guard for Schlaubi's fixed core (Bauplan Charakter, Phase 1).

The core file (`kern.md`) may only be changed by Marvin through git. Before Schlaubi starts,
`verify_core` checks that

- the file exists, is a regular file and not a link,
- it belongs to another account than Schlaubi's service and is not writable for group or others,
- the `.git` folder does not belong to the service and is not writable for group or others, so the
  service cannot commit its own version of the core,
- its bytes are exactly the version in the last commit (`HEAD`).

If anything is off, Schlaubi does not start. `check_core_at_start` writes the outcome to the
event log, where the notifier picks up a `safety.alert` and tells Marvin.
"""

import errno
import hashlib
import os
import shutil
import stat
import subprocess
from pathlib import Path

CORE_FILE = Path(__file__).with_name("kern.md")
REPO_ROOT = Path(__file__).resolve().parents[2]
_GIT_TIMEOUT_S = 10


class CoreCheckError(Exception):
    """The core is missing, changed or not protected; Schlaubi must not start."""


def git_blob_id(data, algorithm):
    """The id git gives a file with these bytes ("sha1" or "sha256" repositories)."""
    header = f"blob {len(data)}\0".encode()
    return hashlib.new(algorithm, header + data).hexdigest()


def _check_protected(info, service_uid, label):
    if info.st_uid == service_uid:
        raise CoreCheckError(f"{label} gehört dem Dienst und könnte von ihm geändert werden")
    if info.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
        raise CoreCheckError(f"{label} ist für Gruppe oder andere beschreibbar")


def _read_core(path, service_uid):
    """Open without following links and check the very file that is read."""
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    except FileNotFoundError as error:
        raise CoreCheckError(f"Kern-Datei fehlt: {path}") from error
    except OSError as error:
        if error.errno == errno.ELOOP:
            raise CoreCheckError("Kern-Datei ist ein Link, erwartet wird eine echte Datei") from error
        raise CoreCheckError(f"Kern-Datei nicht lesbar: {error.strerror}") from error
    with os.fdopen(fd, "rb") as handle:
        info = os.fstat(handle.fileno())
        if not stat.S_ISREG(info.st_mode):
            raise CoreCheckError("Kern-Datei ist keine normale Datei")
        _check_protected(info, service_uid, "Kern-Datei")
        return handle.read()


def _committed_blob_id(repo, relative, git):
    executable = shutil.which(git)
    if executable is None:
        raise CoreCheckError(f"git nicht gefunden ({git}), Kern nicht prüfbar")
    # A clean environment: variables like GIT_DIR must not point the check at another repository.
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "LC_ALL": "C", "GIT_CONFIG_NOSYSTEM": "1"}
    command = [
        executable,
        "-c",
        f"safe.directory={repo}",
        "-C",
        str(repo),
        "rev-parse",
        "--verify",
        "--quiet",
        f"HEAD:{relative.as_posix()}",
    ]
    try:
        result = subprocess.run(  # noqa: S603  fixed arguments, no shell
            command, capture_output=True, text=True, timeout=_GIT_TIMEOUT_S, env=env, check=False
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise CoreCheckError(f"git-Prüfung fehlgeschlagen: {error}") from error
    blob = result.stdout.strip()
    if result.returncode != 0 or not blob:
        raise CoreCheckError("Kern-Datei ist nicht im letzten git-Stand enthalten")
    return blob


def _verify(path, repo, service_uid, git):
    if service_uid is None:
        service_uid = os.geteuid()
    path = Path(path)
    repo = Path(repo).resolve()
    if not os.path.lexists(path):
        raise CoreCheckError(f"Kern-Datei fehlt: {path}")
    try:
        relative = path.parent.resolve().relative_to(repo) / path.name
    except ValueError as error:
        raise CoreCheckError("Kern-Datei liegt außerhalb des Repos") from error
    data = _read_core(path, service_uid)
    git_dir = repo / ".git"
    try:
        git_info = os.lstat(git_dir)
    except FileNotFoundError as error:
        raise CoreCheckError("Repo ohne .git-Ordner, Kern nicht prüfbar") from error
    if not stat.S_ISDIR(git_info.st_mode):
        raise CoreCheckError(".git ist kein Ordner, Kern nicht prüfbar")
    _check_protected(git_info, service_uid, ".git-Ordner")

    committed = _committed_blob_id(repo, relative, git)
    algorithm = "sha256" if len(committed) == 64 else "sha1"
    if git_blob_id(data, algorithm) != committed:
        raise CoreCheckError("Kern-Datei weicht vom letzten git-Stand ab")
    try:
        return data.decode("utf-8"), committed
    except UnicodeDecodeError as error:
        raise CoreCheckError("Kern-Datei ist kein gültiges UTF-8") from error


def verify_core(path=CORE_FILE, repo=REPO_ROOT, *, service_uid=None, git="git"):
    """Return the core text if it is safe to start; raise CoreCheckError otherwise.

    `service_uid` is the account Schlaubi's services run as (default: the current process).
    """
    text, _ = _verify(path, repo, service_uid, git)
    return text


def check_core_at_start(log, path=CORE_FILE, repo=REPO_ROOT, *, service_uid=None, git="git"):
    """`verify_core` plus an event: system.health when it passes, safety.alert when it fails."""
    try:
        text, blob = _verify(path, repo, service_uid, git)
    except CoreCheckError as error:
        log.append("safety.alert", {"reason": str(error)}, intent="core.check_failed", result="kein Start")
        raise
    log.append("system.health", {"blob": blob}, intent="core.check_ok", result="Kern unverändert")
    return text
