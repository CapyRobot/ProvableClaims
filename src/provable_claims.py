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


CONFIG_PARAMETERS = [
    {
        "name": "config_path",
        "default": ".provable_claims",
        "type": str,
        "description": "Config file path; default='.provable_claims'",
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

DEFAULT_CONFIG = {}
for parameter in CONFIG_PARAMETERS:
    DEFAULT_CONFIG[parameter["name"]] = parameter["default"]


def is_iterable(obj):
    try:
        _ = iter(obj)
        return True
    except TypeError:
        return False


def load_cli_args():
    """
    """
    parser = argparse.ArgumentParser(
        description='ProvableClaims; a CLI tool for matching proofs and claims.')
    for parameter in CONFIG_PARAMETERS:
        if is_iterable(parameter["type"]()) and "subtype" in parameter.keys():
            parser.add_argument(
                "--" + parameter["name"], nargs='+', type=parameter["subtype"], help=parameter["description"])
        else:
            parser.add_argument(
                "--" + parameter["name"], type=parameter["type"], help=parameter["description"])
    return parser.parse_args()


def load_config():
    """
    """
    config = DEFAULT_CONFIG
    config_path = config["config_path"]

    cli_args = load_cli_args()
    if cli_args.config_path:
        config_path = cli_args.config_path

    try:
        with open(config_path, "r") as f:
            file_config = json.load(f)
            for key in file_config.keys():
                if key not in config:
                    print(
                        f"WARN: key \"{key}\" from config file is not an input parameter. Ignoring it.")
            config.update(file_config)
    except FileNotFoundError:
        print(
            f"WARN: config file @ \"{config_path}\" does not exist. Using default config + CLI args.")
    except:
        print(f"ERROR: failure to parse config file @ \"{config_path}\".\n")
        raise

    for arg in cli_args.__dict__:
        if getattr(cli_args, arg):
            config[arg] = getattr(cli_args, arg)

    return config


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


class Occurrence:
    def __init__(self, id: str, file: str, position: str):
        self.id = id
        self.file = file
        self.position = position


def find_occurrences_in_file(pattern: re.Pattern, filepath: str) -> list[Occurrence]:
    """
    """

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


def find_all_occurrences(file_list, pattern) -> list[Occurrence]:
    """
    """
    occurrences = []
    for filepath in file_list:
        occurrences += find_occurrences_in_file(pattern, filepath)
    return occurrences


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


def create_results_map(claim_matches, proof_matches):
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


if __name__ == "__main__":

    config = load_config()
    print(config)

    file_list = get_all_files_in_directory(config["directory"])
    file_list = filter_files_of_interest(
        file_list, config["include_pattern"], config["exclude_pattern"])

    print(file_list)

    claim_pattern = re.compile(r'@claim{([^}]*)}'.encode())
    proof_pattern = re.compile(r'@proof{([^}]*)}'.encode())
    claim_matches = find_all_occurrences(file_list, claim_pattern)
    proof_matches = find_all_occurrences(file_list, proof_pattern)

    print(claim_matches)
    print(proof_matches)

    results_map = create_results_map(claim_matches, proof_matches)

    print(results_map)
    log_results(results_map)

    for res in results_map.values():
        if res.is_incomplete():
            exit(1)

    print(f"== {len(file_list)} files scanned, {len(results_map)} tag ids found.")
    print("== \033[32m" + "Looks Good To Me :)" + "\033[0m")
