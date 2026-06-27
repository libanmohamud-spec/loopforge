import unittest

import app


class TestApp(unittest.TestCase):
    def test_run_cmd_returns_zero_for_simple_input(self) -> None:
        self.assertEqual(app.run_cmd("safe"), 0)


if __name__ == "__main__":
    unittest.main()
