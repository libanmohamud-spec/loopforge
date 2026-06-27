"""
Behavioural tests for run_report. A patch that fixes the vulnerability but
breaks these is not a fix. The verifier runs these before and after the patch.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import run_report


class TestRunReport(unittest.TestCase):
    def test_simple_name(self):
        self.assertEqual(run_report("Q4"), "Report for Q4")

    def test_multiword_name(self):
        self.assertEqual(run_report("Quarterly Summary"), "Report for Quarterly Summary")

    def test_numeric_name(self):
        self.assertEqual(run_report("2026"), "Report for 2026")


if __name__ == "__main__":
    unittest.main()
