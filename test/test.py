import unittest
import os
import sys

import provable_claims

TEST_DIR = os.path.dirname(os.path.realpath(__file__)) + "/"


def init_config(cli=["provable_claims.py"]):
    sys.argv = cli
    return provable_claims.Config()


class TestConfig(unittest.TestCase):
    def test_args_from_file(self):
        config = init_config(
            ["provable_claims.py", "--config_path", TEST_DIR+".config"])
        self.assertEqual(len(config.at("exclude_pattern")), 1)
        self.assertEqual(config.at("exclude_pattern")[0], "excluded.md")

    def test_args_from_cli(self):
        config = init_config(
            ["provable_claims.py", "--config_path", TEST_DIR+".config",
             "--exclude_pattern", "<none>"])
        self.assertEqual(len(config.at("exclude_pattern")), 1)
        self.assertEqual(config.at("exclude_pattern")[0], "<none>")


if __name__ == '__main__':
    unittest.main()
