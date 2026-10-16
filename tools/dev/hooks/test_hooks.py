"""Tests for the Claude Code hooks: core file only after asking, ruff after every Python change."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

HOOKS = Path(__file__).resolve().parent
RUFF = Path(sys.executable).with_name("ruff")


def run_hook(name, event, root, cwd=None):
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(root)}
    return subprocess.run(  # noqa: S603  fixed arguments, no shell
        [sys.executable, "-I", str(HOOKS / name)],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        env=env,
        cwd=cwd or root,
        timeout=60,
        check=False,
    )


@pytest.fixture
def root(tmp_path):
    (tmp_path / "brain" / "character").mkdir(parents=True)
    (tmp_path / "brain" / "character" / "kern.md").write_text("# Kern\n", encoding="utf-8")
    return tmp_path


def asks(result):
    if not result.stdout.strip():
        return False
    decision = json.loads(result.stdout)["hookSpecificOutput"]
    return decision["permissionDecision"] == "ask" and "Marvins Ja" in decision["permissionDecisionReason"]


@pytest.mark.parametrize(
    "event",
    [
        {"tool_name": "Edit", "tool_input": {"file_path": "{root}/brain/character/kern.md"}},
        {"tool_name": "Write", "tool_input": {"file_path": "{root}/brain/character/../character/kern.md"}},
        {"tool_name": "Edit", "tool_input": {"file_path": "brain/character/kern.md"}},
        {"tool_name": "Bash", "tool_input": {"command": "sed -i s/a/b/ brain/character/kern.md"}},
    ],
)
def test_changing_the_core_asks_marvin(root, event):
    event = json.loads(json.dumps(event).replace("{root}", str(root)))

    result = run_hook("kern_rueckfrage.py", event, root)

    assert result.returncode == 0
    assert asks(result)


def test_relative_path_means_the_project_even_from_another_folder(root, tmp_path_factory):
    anderswo = tmp_path_factory.mktemp("anderswo")
    event = {"tool_name": "Edit", "tool_input": {"file_path": "brain/character/kern.md"}}

    assert asks(run_hook("kern_rueckfrage.py", event, root, cwd=anderswo))


def test_relative_path_counts_from_the_session_folder(root):
    event = {"cwd": str(root / "brain"), "tool_name": "Edit", "tool_input": {"file_path": "character/kern.md"}}

    assert asks(run_hook("kern_rueckfrage.py", event, root))


@pytest.mark.parametrize(
    "event",
    [
        {"tool_name": "Edit", "tool_input": {"file_path": "{root}/brain/wissen.py"}},
        {"tool_name": "Bash", "tool_input": {"command": "ls brain"}},
        {"tool_name": "Write", "tool_input": {}},
    ],
)
def test_other_files_pass_without_asking(root, event):
    event = json.loads(json.dumps(event).replace("{root}", str(root)))

    result = run_hook("kern_rueckfrage.py", event, root)

    assert result.returncode == 0
    assert not asks(result)


def test_broken_input_does_not_block(root):
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(root)}
    result = subprocess.run(  # noqa: S603  fixed arguments, no shell
        [sys.executable, "-I", str(HOOKS / "kern_rueckfrage.py")],
        input="kein json",
        capture_output=True,
        text=True,
        env=env,
        timeout=60,
        check=False,
    )

    assert result.returncode == 0 and result.stdout == ""


@pytest.fixture
def ruff_root(tmp_path):
    assert RUFF.exists(), "ruff fehlt neben dem Python der Testumgebung (.venv einrichten)"  # no silent skip
    (tmp_path / ".venv" / "bin").mkdir(parents=True)
    (tmp_path / ".venv" / "bin" / "ruff").symlink_to(RUFF)
    return tmp_path


def edit_event(path):
    return {"tool_name": "Edit", "tool_input": {"file_path": str(path)}}


def test_ruff_formats_a_clean_file_and_stays_quiet(ruff_root):
    datei = ruff_root / "gut.py"
    datei.write_text("x=1\n", encoding="utf-8")

    result = run_hook("ruff_nach_aenderung.py", edit_event(datei), ruff_root)

    assert result.returncode == 0
    assert datei.read_text(encoding="utf-8") == "x = 1\n"


def test_ruff_reports_lint_errors_back_to_claude(ruff_root):
    datei = ruff_root / "schlecht.py"
    datei.write_text("import os\n", encoding="utf-8")

    result = run_hook("ruff_nach_aenderung.py", edit_event(datei), ruff_root)

    assert result.returncode == 2
    assert "schlecht.py" in result.stderr and "F401" in result.stderr


def test_ruff_ignores_other_files_and_files_outside_the_project(ruff_root, tmp_path_factory):
    text = ruff_root / "skript"  # no .py: ruff would lint it as Python if the hook passed it on
    text.write_text("import os\n", encoding="utf-8")
    draussen = tmp_path_factory.mktemp("draussen") / "fremd.py"
    draussen.write_text("import os\n", encoding="utf-8")

    for datei in (text, draussen):
        result = run_hook("ruff_nach_aenderung.py", edit_event(datei), ruff_root)
        assert result.returncode == 0
    assert draussen.read_text(encoding="utf-8") == "import os\n"
