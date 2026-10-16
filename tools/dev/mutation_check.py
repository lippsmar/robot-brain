"""Checks that the tests notice deliberate bugs ("mutations").

Each mutation replaces one piece of code in a temporary copy of the repository and runs
the matching test file. A mutation that the tests do not notice "survives" and points to
a missing test. The working copy is never changed.

Usage: python tools/dev/mutation_check.py [mutations.json]
"""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LIST = ROOT / "brain" / "tests" / "mutations.json"
COPY = ("brain", "schemas", "pyproject.toml")


def run_tests(work, test_file):
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-x", "-q", "-p", "no:cacheprovider", test_file],
        cwd=work,
        capture_output=True,
        text=True,
        check=False,
    )


def main(list_path):
    mutations = json.loads(Path(list_path).read_text(encoding="utf-8"))
    survivors = 0
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        for name in COPY:
            source = ROOT / name
            if source.is_dir():
                shutil.copytree(source, work / name, ignore=shutil.ignore_patterns("__pycache__"))
            else:
                shutil.copy(source, work / name)
        # Without this baseline, a test file that fails anyway would make every mutation look "caught".
        for test_file in sorted({mutation["test"] for mutation in mutations}):
            if run_tests(work, test_file).returncode != 0:
                print(f"BASIS ROT {test_file}: schlägt schon ohne eingebauten Fehler fehl, Prüfung abgebrochen")
                return 2
        for mutation in mutations:
            file = work / mutation["file"]
            original = file.read_text(encoding="utf-8")
            if original.count(mutation["old"]) != 1:
                print(f"FEHLT    {mutation['file']}: Stelle nicht eindeutig gefunden: {mutation['old'][:60]}")
                survivors += 1
                continue
            file.write_text(original.replace(mutation["old"], mutation["new"]), encoding="utf-8")
            result = run_tests(work, mutation["test"])
            file.write_text(original, encoding="utf-8")
            caught = result.returncode != 0
            survivors += not caught
            print(f"{'ERKANNT ' if caught else 'UEBERLEBT'} {mutation['why']}")
    print(f"{len(mutations)} Fehler eingebaut, {survivors} nicht erkannt")
    return 1 if survivors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_LIST))
