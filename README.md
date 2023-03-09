# ProvableClaims [WIP]
[![ci-python-unittest](https://github.com/CapyRobot/ProvableClaims/actions/workflows/py_unittest.yml/badge.svg)](https://github.com/CapyRobot/ProvableClaims/actions/workflows/py_unittest.yml)
[![provable_claims](https://github.com/CapyRobot/ProvableClaims/actions/workflows/provable_claims.yml/badge.svg)](https://github.com/CapyRobot/ProvableClaims/actions/workflows/provable_claims.yml)

**A tool to match claims to proofs in a codebase.**

As a project grows, some level of duplicate information is inevitable. Test doubles and mocks are created to mimic the behavior of large modules, function declarations and docs are separated from implementation, usage examples are added to docs, API call side-effects are documented in a separate file, etc.

Managing this duplication and ensuring these different sources of information are in sync can be very challenging. It is common to see projects with a checklist of places that must be manually checked and updated for code reviews. Some paradigms such as [Docs as Code](https://www.writethedocs.org/guide/docs-as-code/) help, but the process is still error-prone. If a function is renamed, how to ensure an associated example in a markdown file is updated in the same commit?

**ProvableClaims** provides a way of linking places of the codebase that should change together or, at least, be reviewed together. It allows the developer to add links within the codebase and define policies for each link. A policy could be defined, for example, as linked sections shall be changed in the same git commit.

The presence of the tags also tells developers that changes in certain locations could require changes somewhere else as well - `Ctrl+Shift+F {cli_args}`.

## Example

For example, consider a code file that defines CLI parameters for an application and another user guide file that documents such parameters. ProvableClaims could link the code block that defines the parameters to the associated documentation section.

```python
# @ my_app.py
...
parser = argparse.ArgumentParser()
# @linked_tag{cli_args:span_begin}
# Please update all related links of id `cli_args`
parser.add_argument("arg1", help="arg1 description")
parser.add_argument("arg2", help="arg2 description")
# @linked_tag{cli_args:span_end}
args = parser.parse_args()
```

```md
<!-- @ user_guide.md -->
...
Supported CLI parameters:
<!-- @linked_tag{cli_args:span_begin} -->
* arg1 - arg1 description
* arg2 - arg2 description
<!-- @linked_tag{cli_args:span_end} -->
```

The policy could be defined, for example, as both linked sections shall be changed in the same git commit. Then, the tool can be used to automatically enforce the policy within an automated test.

## Usage

Tags can be placed anywhere in the codebase with the syntax `@linked_tag{group_id:tag_type:policy_type}`.
* `group_id` - all tags with the same id are linked. Policies are then applied for groups of linked tags.
* `tag_type` - tags can have two types:
  - Span, which is composed of two instances of `@linked_tag` in the same file; the first of type `span_begin` and the second of type `span_end`. All content between these two tags is relevant for evaluating policies.
  - `entire_file`, which specifies that the entire content of the file is relevant for evaluating policies.
* `policy_type` (optional, default=`all_policy`) - tags can be of type *listener*, *talker*, or *both*, which specifies if the content of the tag is expected to change when other liked tags' content changes.
  - `listener_policy` - when the content of another linked tag changes, the content of this tag is expected to change.
  - `talker_policy` - when the content of this tag changes, the content of linked *listener* tags is expected to change.
  - `all_policy` implements both `listener_policy` and `talker_policy`.

```
TODO - CLI
```

### Configuration

```
TODO
```

### CLI

```
TODO
```

## Examples

```
TODO
```

## Contributing

Contributions and feature requests are always welcome!

Please enquire about the changes you want to make before committing significant time to it. If not doing so, there is always a chance the change may be rejected.
