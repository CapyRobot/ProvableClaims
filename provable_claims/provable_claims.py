# MIT License
#
# Copyright (c) 2023 Eduardo Rocha
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import re
import mmap
import fnmatch
import json
import argparse


class Config:
    """
    This module initializes the script configuration.
    1. config = default values
    2. override values with configuration file
    3. override values with cli args
    """

    def __init__(self):
        """
        """
        self._config = Config.__default()
        config_path = self._config["config_path"]

        cli_args = Config.__read_cli_args()
        if cli_args.config_path:
            config_path = cli_args.config_path

        # try to read config file if any
        # override default values with config file values
        self.__read_file(config_path)

        # override current values with CLI values
        for arg in cli_args.__dict__:
            if getattr(cli_args, arg):
                self._config[arg] = getattr(cli_args, arg)

    def __read_cli_args():
        """
        """
        def is_iterable(obj):
            try:
                _ = iter(obj)
                return True
            except TypeError:
                return False

        parser = argparse.ArgumentParser(
            description='ProvableClaims; a CLI tool for matching proofs and claims.')
        for parameter in Config.__parameters():
            if is_iterable(parameter["type"]()) and "subtype" in parameter.keys():
                parser.add_argument(
                    "--" + parameter["name"], nargs='+', type=parameter["subtype"], help=parameter["description"])
            else:
                parser.add_argument(
                    "--" + parameter["name"], type=parameter["type"], help=parameter["description"])
        return parser.parse_args()

    def __read_file(self, config_path):
        try:
            with open(config_path, "r") as f:
                file_config = json.load(f)
                for key in file_config.keys():
                    if key not in self._config:
                        print(
                            f"WARN: key \"{key}\" from config file is not an input parameter. Ignoring it.")
                self._config.update(file_config)
        except FileNotFoundError:
            print(
                f"WARN: config file @ \"{config_path}\" does not exist. Using default config + CLI args.")
        except:
            print(
                f"ERROR: failure to parse config file @ \"{config_path}\".\n")
            raise

    def __parameters():
        return [
            {
                "name": "config_path",
                "default": "./.provable_claims",
                "type": str,
                "description": "Config file path; default='./.provable_claims'",
            },
            {
                "name": "directory",
                "default": "./",
                "type": str,
                "description": "Only files within this directory are searched; default='./'",
            },
            {
                "name": "output_report",
                "default": None,
                "type": str,
                "description": "Path for generated output report; default=None",
            },
            {
                "name": "include_pattern",
                "default": ["*"],
                "type": list,
                "subtype": str,
                "description": "List of patterns for including files; Unix shell-style wildcards; default=['*']",
            },
            {
                "name": "exclude_pattern",
                "default": [],
                "type": list,
                "subtype": str,
                "description": "List of patterns to exclude files; Unix shell-style wildcards; default=[]",
            },
        ]

    def __default():
        default_config = {}
        for parameter in Config.__parameters():
            default_config[parameter["name"]] = parameter["default"]
        return default_config

    def at(self, key):
        return self._config[key]

    def print(self):
        print(json.dumps(self._config, sort_keys=True, indent=4))


def get_all_files_in_directory(root_dir):
    """
    """
    file_list = []
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            file_list.append(file_path)
    return file_list


def filter_files_of_interest(file_list, include_patterns, exclude_patterns):
    """
    """
    filtered_files = [f for f in file_list if os.path.isfile(f)]
    # filter for files that match 'include_patterns'
    filtered_files = [f for f in file_list if any(
        fnmatch.fnmatch(f, pattern) for pattern in include_patterns)]
    # remove the files that match 'exclude_patterns'
    filtered_files = [f for f in filtered_files if not any(
        fnmatch.fnmatch(f, pattern) for pattern in exclude_patterns)]
    return filtered_files


class TagResults:
    def __init__(self, id: str):
        self.id = id
        self.claims: list[str] = []
        self.proofs: list[str] = []

    def create_error_logs(self):
        def red(text):
            return '\033[31m' + text + '\033[0m'

        def yellow(text):
            return '\033[33m' + text + '\033[0m'

        error = ""
        warning = ""
        if not self.claims:
            error += red("ERROR") + f": a proof without a claim;\n"
        elif not self.proofs:
            error += red("ERROR") + f": a claim without a proof;\n"
        if len(self.claims) > 1:
            warning += yellow(" WARN") + f": multiple claims with same id;\n"
        if len(self.proofs) > 1:
            warning += yellow(" WARN") + f": multiple proofs with same id;\n"
        occurrences_log = ""
        for claim in self.claims:
            occurrences_log += f"\tClaim @ {claim}\n"
        for proof in self.proofs:
            occurrences_log += f"\tProof @ {proof}\n"
        return error, warning, occurrences_log

    def is_incomplete(self):
        if not self.claims:
            return True
        elif not self.proofs:
            return True
        return False


class Occurrence:
    def __init__(self, id: str, file: str, position: str):
        self.id = id
        self.file = file
        self.position = position


class REMatcher:

    def __init__(self):
        self.claim_pattern = re.compile(r'@claim{([^}]*)}'.encode())
        self.proof_pattern = re.compile(r'@proof{([^}]*)}'.encode())

    def match(self, file_list):
        claim_matches = self.__find_all_occurrences(
            file_list, self.claim_pattern)
        proof_matches = self.__find_all_occurrences(
            file_list, self.proof_pattern)
        return self.__create_results_map(claim_matches, proof_matches)

    def __find_occurrences_in_file(self, pattern: re.Pattern, filepath: str) -> list[Occurrence]:
        """
        """

        if os.path.getsize(filepath) == 0:  # empty file
            return []

        with open(filepath, 'r') as f:
            mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)

        matches = list(pattern.finditer(mm))
        if not matches:
            return []

        last_match = matches[-1].start()
        newline_map = {-1: 1}  # -1 so a failed 'rfind' maps to the first line.
        newline_re = re.compile(b'\n')
        for line_number, newline_match in enumerate(newline_re.finditer(mm), 2):
            offset = newline_match.start()
            if offset > last_match:  # stop at last match
                break
            newline_map[offset] = line_number

        for m in matches:
            # failure -> -1 maps to line 1.
            newline_offset = mm.rfind(b'\n', 0, m.start())
            line_number = newline_map[newline_offset]
            column = m.start() - max(0, newline_offset)
            yield Occurrence(m.group(1).decode(), filepath, f"{line_number}:{column}")

    def __find_all_occurrences(self, file_list, pattern) -> list[Occurrence]:
        """
        """
        occurrences = []
        for filepath in file_list:
            occurrences += self.__find_occurrences_in_file(pattern, filepath)
        return occurrences

    def __create_results_map(self, claim_matches, proof_matches):
        results_map = {}
        for match in claim_matches:
            id = match.id
            if id not in results_map.keys():
                results_map[id] = TagResults(id)
            results_map[id].claims.append(f"{match.file}:{match.position}")
        for match in proof_matches:
            id = match.id
            if id not in results_map.keys():
                results_map[id] = TagResults(id)
            results_map[id].proofs.append(f"{match.file}:{match.position}")
        return results_map


def log_results(results_map: dict):
    for id, tag_results in results_map.items():
        error, warn, occurrences_log = tag_results.create_error_logs()
        if error != "" or warn != "":
            print(error + warn, end="")
            print("\tTag id: ", id)
            print(occurrences_log)


def create_report(results_map: dict, filepath: str):
    if filepath:
        out = {"number_tags": len(results_map),
               "error_tags": [], "warn_tags": []}
        for id, tag_results in results_map.items():
            error, warn, _ = tag_results.create_error_logs()
            out[id] = {
                "claims": tag_results.claims,
                "proofs": tag_results.proofs,
            }
            if error != "":
                out["error_tags"].append(id)
            if warn != "":
                out["warn_tags"].append(warn)

        print(f"== Writing output report @ {filepath}")
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(out, f)


def run():

    config = Config()
    # TODO: print on debug mode only
    print("\n== Config:")
    config.print()
    print()

    file_list = get_all_files_in_directory(config.at("directory"))
    file_list = filter_files_of_interest(
        file_list, config.at("include_pattern"), config.at("exclude_pattern"))

    # TODO: on debug mode, print(file_list)

    matcher = REMatcher()
    results_map = matcher.match(file_list)

    log_results(results_map)
    create_report(results_map, config.at("output_report"))

    print(f"== {len(file_list)} files scanned, {len(results_map)} tag ids found.")
    for res in results_map.values():
        if res.is_incomplete():
            return 1
    print("== \033[32m" + "Looks Good To Me :)" + "\033[0m")
    return 0


if __name__ == "__main__":
    exit(run())
