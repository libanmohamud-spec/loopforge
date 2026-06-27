#!/usr/bin/env python3
"""
verify.py - the stop condition for the patch loop.

A patch is "done" when execution proves four things:

    1. the PoC reproduces on the unpatched code   (the finding is real)
    2. the patch applies cleanly
    3. the PoC no longer reproduces after the patch (it is actually fixed)
    4. the project's tests still pass               (nothing was broken)

Unlike the threat-model verifier, this one cannot work from a static artifact.
A PATCH_RESULT.json the agent writes by hand can claim anything. So this
verifier generates the evidence itself, by running the PoC and the tests
before and after applying the patch in an isolated copy of the project. The
agent cannot fake a result it did not produce.

Usage:
    python3 verify.py <patch-file> [--project DIR]

    --project DIR   path to the project to patch. Defaults to the bundled
                    example project next to this verifier. The project must
                    contain loop.config.json with "poc" and "tests" commands,
                    or you may pass --poc / --tests to override.

Exit code:
    0  all four conditions hold - the loop may close
    1  one or more conditions failed - keep iterating
    2  the patch file or project could not be read

The verifier runs the project's PoC and test commands. Run it where you are
willing to execute that code - a container or sandbox, not blindly on a
workstation. It never runs anything the project config did not declare.

Dependencies: Python 3.8+ standard library, plus `git` on PATH.
"""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_PROJECT = HERE / "examples" / "project"

# PoC convention: exit 0 means the vulnerability REPRODUCED.
POC_REPRODUCED = 0


class Finding:
    def __init__(self, code, message):
        self.code = code
        self.message = message

    def line(self):
        return f"  BLOCK  {self.code:18} {self.message}"


def run(cmd, cwd):
    """Run a shell command string in cwd; return (exit_code, combined_output)."""
    proc = subprocess.run(
        cmd, cwd=cwd, shell=True, capture_output=True, text=True, timeout=120
    )
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def load_config(project: Path, poc_override, tests_override):
    poc, tests = poc_override, tests_override
    cfg_path = project / "loop.config.json"
    if cfg_path.exists():
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        poc = poc or cfg.get("poc")
        tests = tests or cfg.get("tests")
    return poc, tests


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("patch")
    ap.add_argument("--project", default=str(DEFAULT_PROJECT))
    ap.add_argument("--poc")
    ap.add_argument("--tests")
    args = ap.parse_args()

    patch_file = Path(args.patch).resolve()
    project = Path(args.project).resolve()

    if not patch_file.exists():
        print(f"error: patch file not found: {patch_file}", file=sys.stderr)
        return 2
    if not project.is_dir():
        print(f"error: project directory not found: {project}", file=sys.stderr)
        return 2

    poc, tests = load_config(project, args.poc, args.tests)
    if not poc or not tests:
        print(
            "error: project needs loop.config.json with 'poc' and 'tests', "
            "or pass --poc and --tests",
            file=sys.stderr,
        )
        return 2

    findings = []
    evidence = {"patch": patch_file.name, "project": project.name}

    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / "work"
        shutil.copytree(project, work)
        run(
            "git init -q && git add -A && "
            "git -c user.email=ci@loopforge -c user.name=loopforge commit -qm base",
            work,
        )

        code, _out = run(poc, work)
        evidence["poc_before_exit"] = code
        if code != POC_REPRODUCED:
            findings.append(
                Finding(
                    "PT-NO-REPRO",
                    "PoC does not reproduce on the unpatched project; the finding is "
                    "invalid or already fixed, so there is nothing to verify",
                )
            )
            return report(findings, evidence)

        code, _out = run(tests, work)
        evidence["tests_before_exit"] = code
        if code != 0:
            findings.append(
                Finding(
                    "PT-BASELINE-TESTS",
                    "tests fail on the unpatched project; fix the baseline before "
                    "verifying a patch",
                )
            )
            return report(findings, evidence)

        code, out = run(f'git apply --whitespace=nowarn "{patch_file}"', work)
        evidence["patch_applied"] = code == 0
        if code != 0:
            findings.append(
                Finding(
                    "PT-APPLY-FAILED",
                    f"patch does not apply cleanly: {out.splitlines()[0] if out else 'git apply failed'}",
                )
            )
            return report(findings, evidence)

        code, _out = run(poc, work)
        evidence["poc_after_exit"] = code
        if code == POC_REPRODUCED:
            findings.append(
                Finding(
                    "PT-NO-FIX",
                    "PoC still reproduces after the patch; the vulnerability is not fixed",
                )
            )

        code, _out = run(tests, work)
        evidence["tests_after_exit"] = code
        if code != 0:
            findings.append(
                Finding(
                    "PT-BREAKS-TESTS",
                    "tests fail after the patch; the fix breaks existing behaviour",
                )
            )

    return report(findings, evidence)


def report(findings, evidence) -> int:
    print("\npatch verify")
    print("  " + "  ".join(f"{k}={v}" for k, v in evidence.items()))
    print("")
    if not findings:
        print("  no blocking findings.")
    else:
        for finding in findings:
            print(finding.line())
    print("")
    if findings:
        print(f"  RESULT: BLOCKED ({len(findings)} blocking) -- loop stays open")
        return 1
    print("  RESULT: PASS -- reproduced before, fixed after, tests green -- loop may close")
    return 0


if __name__ == "__main__":
    sys.exit(main())
