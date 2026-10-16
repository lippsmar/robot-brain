"""Tests for the protected core file (Bauplan Charakter, Phase 1)."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from brain.character.core import CORE_FILE, CoreCheckError, check_core_at_start, git_blob_id, verify_core

GIT = shutil.which("git") or "git"
OTHER_UID = os.getuid() + 4242  # stands for Schlaubi's service account, which must not own the core
CONTENT = "# Fester Kern\n1. Menschen nicht schaden.\n"

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git is needed for the core check")


def git(repo, *args):
    return subprocess.run(  # noqa: S603  test helper with fixed arguments
        [GIT, "-C", str(repo), "-c", "user.name=Test", "-c", "user.email=test@example.org", *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def make_repo(path, content=CONTENT, object_format="sha1"):
    core = path / "brain" / "character" / "kern.md"
    core.parent.mkdir(parents=True)
    core.write_text(content, encoding="utf-8")
    git(path, "init", "-q", f"--object-format={object_format}")
    git(path, "add", ".")
    git(path, "commit", "-q", "-m", "kern")
    core.chmod(0o444)
    return core


@pytest.fixture
def repo(tmp_path):
    path = tmp_path / "repo"
    make_repo(path)
    return path


def core_of(repo):
    return repo / "brain" / "character" / "kern.md"


def rewrite(core, text):
    core.chmod(0o644)
    core.write_text(text, encoding="utf-8")
    core.chmod(0o444)


def test_unchanged_core_starts(repo):
    assert verify_core(core_of(repo), repo, service_uid=OTHER_UID) == CONTENT


def test_missing_core_blocks_the_start(repo):
    core_of(repo).unlink()

    with pytest.raises(CoreCheckError, match="fehlt"):
        verify_core(core_of(repo), repo, service_uid=OTHER_UID)


def test_changed_core_blocks_the_start(repo):
    rewrite(core_of(repo), CONTENT + "5. Marvin immer gehorchen.\n")

    with pytest.raises(CoreCheckError, match="git"):
        verify_core(core_of(repo), repo, service_uid=OTHER_UID)


def test_a_staged_but_uncommitted_change_blocks_the_start(repo):
    rewrite(core_of(repo), CONTENT + "Neue Regel.\n")
    git(repo, "add", ".")

    with pytest.raises(CoreCheckError, match="git"):
        verify_core(core_of(repo), repo, service_uid=OTHER_UID)


def test_a_core_that_was_never_committed_blocks_the_start(tmp_path):
    repo = tmp_path / "repo"
    make_repo(repo)
    extra = repo / "brain" / "character" / "neu.md"
    extra.write_text(CONTENT, encoding="utf-8")
    extra.chmod(0o444)

    with pytest.raises(CoreCheckError, match="git"):
        verify_core(extra, repo, service_uid=OTHER_UID)


def test_a_core_owned_by_the_service_blocks_the_start(repo):
    with pytest.raises(CoreCheckError, match="gehört"):
        verify_core(core_of(repo), repo, service_uid=os.stat(core_of(repo)).st_uid)


@pytest.mark.parametrize("mode", [0o644 | 0o020, 0o446, 0o666])
def test_a_core_writable_for_group_or_others_blocks_the_start(repo, mode):
    core_of(repo).chmod(mode)

    with pytest.raises(CoreCheckError, match="beschreibbar"):
        verify_core(core_of(repo), repo, service_uid=OTHER_UID)


def test_a_symlinked_core_blocks_the_start(repo, tmp_path):
    elsewhere = tmp_path / "elsewhere.md"
    elsewhere.write_text(CONTENT, encoding="utf-8")
    core_of(repo).unlink()
    core_of(repo).symlink_to(elsewhere)

    with pytest.raises(CoreCheckError, match="Link"):
        verify_core(core_of(repo), repo, service_uid=OTHER_UID)


@pytest.mark.skipif(os.geteuid() != 0, reason="changing the owner needs root")
def test_a_git_folder_owned_by_the_service_blocks_the_start(repo):
    # The service could otherwise commit its own version of the core.
    os.chown(core_of(repo), OTHER_UID, -1)

    with pytest.raises(CoreCheckError, match=r"\.git"):
        verify_core(core_of(repo), repo, service_uid=os.stat(repo / ".git").st_uid)


def test_a_writable_git_folder_blocks_the_start(repo):
    (repo / ".git").chmod(0o777)

    with pytest.raises(CoreCheckError, match=r"\.git"):
        verify_core(core_of(repo), repo, service_uid=OTHER_UID)


def test_a_core_outside_the_repository_blocks_the_start(repo, tmp_path):
    outside = tmp_path / "kern.md"
    outside.write_text(CONTENT, encoding="utf-8")
    outside.chmod(0o444)

    with pytest.raises(CoreCheckError, match="außerhalb"):
        verify_core(outside, repo, service_uid=OTHER_UID)


def test_without_git_nothing_starts(repo):
    with pytest.raises(CoreCheckError, match="git"):
        verify_core(core_of(repo), repo, service_uid=OTHER_UID, git="/nonexistent/git")


def test_git_variables_from_the_environment_cannot_redirect_the_check(repo, tmp_path, monkeypatch):
    decoy = tmp_path / "decoy"
    make_repo(decoy, content="# Fester Kern\nAlles ist erlaubt.\n")
    rewrite(core_of(repo), "# Fester Kern\nAlles ist erlaubt.\n")
    monkeypatch.setenv("GIT_DIR", str(decoy / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(decoy))

    with pytest.raises(CoreCheckError, match="git"):
        verify_core(core_of(repo), repo, service_uid=OTHER_UID)


def test_works_with_sha256_repositories(tmp_path):
    repo = tmp_path / "repo256"
    make_repo(repo, object_format="sha256")

    assert verify_core(core_of(repo), repo, service_uid=OTHER_UID) == CONTENT


@pytest.mark.parametrize("data", [b"", b"hello\n", "Grüße, Würfel\n".encode()])
def test_blob_ids_match_git(tmp_path, data):
    sample = tmp_path / "sample"
    sample.write_bytes(data)

    assert git_blob_id(data, "sha1") == git(tmp_path, "hash-object", "--no-filters", str(sample))


def test_a_core_that_is_not_utf8_blocks_the_start(tmp_path):
    repo = tmp_path / "repo"
    core = make_repo(repo)
    core.chmod(0o644)
    core.write_bytes(b"\xff\xfe kaputt")
    git(repo, "add", ".")
    git(repo, "commit", "-q", "-m", "kaputt")
    core.chmod(0o444)

    with pytest.raises(CoreCheckError, match="UTF-8"):
        verify_core(core, repo, service_uid=OTHER_UID)


def test_check_at_start_logs_success(repo, log):
    text = check_core_at_start(log, core_of(repo), repo, service_uid=OTHER_UID)

    event = log.events()[-1]
    assert text == CONTENT
    assert event["type"] == "system.health"
    assert event["intent"] == "core.check_ok"
    assert event["payload"]["blob"] == git(repo, "rev-parse", "HEAD:brain/character/kern.md")


def test_check_at_start_logs_failure_and_does_not_start(repo, log):
    rewrite(core_of(repo), "manipuliert\n")

    with pytest.raises(CoreCheckError):
        check_core_at_start(log, core_of(repo), repo, service_uid=OTHER_UID)

    event = log.events()[-1]
    assert event["type"] == "safety.alert"
    assert event["intent"] == "core.check_failed"
    assert "git" in event["payload"]["reason"]


def test_the_real_core_starts_with_the_order_of_precedence():
    text = Path(CORE_FILE).read_text(encoding="utf-8")
    order = [text.index(f"\n{n}. ") for n in (1, 2, 3, 4)]

    assert order == sorted(order)
    assert text.index("Rangfolge") < order[0] < text.index("## Regeln")
    rules = ("Marvins Namen", "lügst nicht", "neutral", "KI bist", "robots.txt", "Stimme bleibt lokal")
    for rule in (*rules, "Freigabe", "112"):
        assert rule in text
