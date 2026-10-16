"""Checks that the tests notice deliberate bugs ("mutations").

Each mutation replaces one piece of code in a temporary copy of the repository and runs
the matching test file. A mutation that the tests do not notice "survives" and points to
a missing test. The working copy is never changed; the result is for the state at the start.

Several workers run in parallel, each on its own copy (default: one per usable CPU core).
With --geaendert only mutations of files changed since a git ref (default HEAD, including
uncommitted and new files) run: quick while working, the full run once per work package.
If shared files changed (test helpers, schemas, other code), the quick mode runs everything.

Usage: python tools/dev/mutation_check.py [--jobs N] [--geaendert [REF]] [mutations.json]
"""

import argparse
import json
import os
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LIST = ROOT / "brain" / "tests" / "mutations.json"
COPY = ("brain", "schemas", "pyproject.toml", "tools/social")
TIMEOUT_S = 300  # a mutation that makes the tests hang counts as caught
GIT = shutil.which("git") or "git"


def run_tests(work, test_file):
    """Return code of pytest on one test file; None if it hung past the time limit."""
    try:
        return subprocess.run(  # noqa: S603  fixed arguments, no shell
            [
                sys.executable,
                "-m",
                "pytest",
                "-x",
                "-q",
                "-p",
                "no:cacheprovider",
                f"--basetemp={work / '.pytest-tmp'}",  # parallel runs must not share pytest's temp folder
                test_file,
            ],
            cwd=work,
            capture_output=True,
            text=True,
            check=False,
            timeout=TIMEOUT_S,
        ).returncode
    except subprocess.TimeoutExpired:
        return None


def make_copy(target):
    target.mkdir()
    for name in COPY:
        source = ROOT / name
        if source.is_dir():
            shutil.copytree(source, target / name, ignore=shutil.ignore_patterns("__pycache__", ".pytest-tmp"))
        else:
            shutil.copy(source, target / name)
    return target


def _git(*args):
    return subprocess.run([GIT, "-C", str(ROOT), *args], capture_output=True, check=True).stdout  # noqa: S603


def changed_files(ref):
    """Files changed since `ref` in the working tree, plus new untracked files (exact paths, -z)."""
    diff = _git("diff", "-z", "--name-only", ref).split(b"\0")
    new = _git("ls-files", "-z", "--others", "--exclude-standard").split(b"\0")
    return {path.decode("utf-8") for path in diff + new if path}


def select_changed(mutations, list_path, ref):
    """Mutations touched by changes since `ref`, or all of them if shared files changed."""
    changed = changed_files(ref)
    covered = {m["file"] for m in mutations} | {m["test"] for m in mutations}
    relative_list = Path(list_path).resolve().relative_to(ROOT).as_posix()
    shared = sorted(
        path
        for path in changed - covered - {relative_list}
        if path.startswith(("brain/", "schemas/", "tools/social/", "pyproject.toml")) and not path.endswith(".md")
    )
    if shared:
        return mutations, f"gemeinsam genutzte Dateien geändert ({', '.join(shared[:3])}), daher alle"
    selected = [m for m in mutations if m["file"] in changed or m["test"] in changed]
    if relative_list in changed:
        try:
            before = json.loads(_git("show", f"{ref}:{relative_list}"))
        except subprocess.CalledProcessError:
            before = []
        known = {json.dumps(m, sort_keys=True) for m in before}
        selected += [m for m in mutations if json.dumps(m, sort_keys=True) not in known and m not in selected]
    return selected, f"nur geänderte Dateien und neue Einträge seit {ref}"


def mutate(work, mutation):
    """Apply one mutation in `work`, run its test file, restore."""
    file = work / mutation["file"]
    original = file.read_text(encoding="utf-8")
    if original.count(mutation["old"]) != 1:
        return "missing"
    file.write_text(original.replace(mutation["old"], mutation["new"]), encoding="utf-8")
    try:
        code = run_tests(work, mutation["test"])
    finally:
        file.write_text(original, encoding="utf-8")
    if code is None:
        return "timeout"
    return "caught" if code != 0 else "survived"


def run_parallel(items, work_dirs, task):
    """Run task(work_dir, item) for all items, one worker per copy. Errors become ("error", text)."""
    results: list = [None] * len(items)
    todo: queue.Queue = queue.Queue()
    for index, item in enumerate(items):
        todo.put((index, item))

    def worker(work):
        while True:
            try:
                index, item = todo.get_nowait()
            except queue.Empty:
                return
            try:
                results[index] = task(work, item)
            except Exception as error:  # report it instead of losing the worker
                results[index] = ("error", f"{type(error).__name__}: {error}")

    threads = [threading.Thread(target=worker, args=(work,)) for work in work_dirs]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("liste", nargs="?", default=str(DEFAULT_LIST))
    parser.add_argument("--jobs", "-j", type=int, default=os.process_cpu_count() or 1)
    parser.add_argument("--geaendert", nargs="?", const="HEAD", default=None, metavar="REF")
    args = parser.parse_args(argv)

    mutations = json.loads(Path(args.liste).read_text(encoding="utf-8"))
    if args.geaendert is not None:
        mutations, reason = select_changed(mutations, args.liste, args.geaendert)
        print(f"Schnellmodus: {reason}: {len(mutations)} Fehler")
        if not mutations:
            return 0
    jobs = max(1, min(args.jobs, len(mutations)))
    with tempfile.TemporaryDirectory() as tmp:
        targets = [Path(tmp) / f"kopie{n}" for n in range(jobs)]
        work_dirs = run_parallel(targets, targets, lambda _work, target: make_copy(target))
        if any(isinstance(work, tuple) for work in work_dirs):
            print(f"Kopie fehlgeschlagen: {[work for work in work_dirs if isinstance(work, tuple)]}")
            return 2
        # Without this baseline, a test file that fails anyway would make every mutation look "caught".
        test_files = sorted({mutation["test"] for mutation in mutations})
        baseline = run_parallel(test_files, work_dirs, run_tests)
        broken = [(test, code) for test, code in zip(test_files, baseline, strict=True) if code != 0]
        if broken:
            for test, code in broken:
                print(f"BASIS ROT {test}: schlägt schon ohne eingebauten Fehler fehl ({code}), Prüfung abgebrochen")
            return 2
        outcomes = run_parallel(mutations, work_dirs, mutate)
    survivors = 0
    for mutation, outcome in zip(mutations, outcomes, strict=True):
        if outcome == "missing":
            print(f"FEHLT    {mutation['file']}: Stelle nicht eindeutig gefunden: {mutation['old'][:60]}")
        elif isinstance(outcome, tuple):
            print(f"FEHLER   {mutation['why']}: {outcome[1]}")
        elif outcome == "timeout":
            print(f"ERKANNT  {mutation['why']} (Tests hingen, Zeitlimit {TIMEOUT_S} s)")
        else:
            print(f"{'ERKANNT ' if outcome == 'caught' else 'UEBERLEBT'} {mutation['why']}")
        survivors += outcome not in ("caught", "timeout")
    print(f"{len(mutations)} Fehler eingebaut, {survivors} nicht erkannt ({jobs} parallel)")
    return 1 if survivors else 0


if __name__ == "__main__":
    sys.exit(main())
