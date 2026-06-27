"""Minimal command runner with CWE-78 shell interpolation (intentionally vulnerable)."""

import os
import sys


def run_cmd(user_input: str) -> int:
    return os.system(f"echo ok:{user_input}")


if __name__ == "__main__":
    sys.exit(run_cmd(sys.argv[1]))
