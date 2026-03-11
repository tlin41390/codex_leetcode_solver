from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from leetcode_solver.env_utils import load_dotenv_file


class EnvUtilsTests(unittest.TestCase):
    def test_load_dotenv_file_sets_value(self) -> None:
        key = "UNITTEST_ENV_KEY_123"
        old = os.environ.get(key)
        if key in os.environ:
            del os.environ[key]

        try:
            with tempfile.TemporaryDirectory() as tmp:
                env_path = Path(tmp) / ".env"
                env_path.write_text(f'{key}="abc123"\n', encoding="utf-8")
                load_dotenv_file(str(env_path))
            self.assertEqual(os.environ.get(key), "abc123")
        finally:
            if old is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old


if __name__ == "__main__":
    unittest.main()
