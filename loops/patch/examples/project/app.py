"""
app.py — a tiny reporting helper with a real vulnerability.

run_report() builds a shell command from caller-controlled input and runs it
with shell=True. That is a command-injection sink (CWE-78): an attacker who
controls `name` can run arbitrary commands.

The patch loop's job is to fix this without breaking run_report's behaviour
for legitimate input. The verifier proves both by execution.
"""

import subprocess
import sys


def run_report(name: str) -> str:
    # VULNERABLE: untrusted input interpolated into a shell command.
    cmd = f"echo Report for {name}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip()
