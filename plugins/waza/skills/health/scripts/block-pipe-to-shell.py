#!/usr/bin/env python3
"""Claude PreToolUse hook that blocks remote-download-to-shell pipelines."""

from __future__ import annotations

import json
import os
import shlex
import sys


DOWNLOADERS = {"curl", "wget"}
SHELLS = {"bash", "dash", "sh", "zsh"}
PIPE_OPERATORS = {"|", "|&"}
GROUP_OPERATORS = {"&", "&&", ";", "||"}
COMPOUND_OPENERS = {"(", "{"}
COMPOUND_CLOSERS = {")", "}"}
COMMAND_SEPARATORS = GROUP_OPERATORS | COMPOUND_OPENERS | COMPOUND_CLOSERS
CONTROL_OPENERS = {"case": "esac", "for": "done", "if": "fi", "select": "done", "until": "done", "while": "done"}
CONTROL_CLOSERS = set(CONTROL_OPENERS.values())


def command_token_names(tokens: list[str]) -> set[str]:
    """Return conservative executable candidates, including quoted wrapper payloads."""
    names: set[str] = set()
    for token in tokens:
        if token in COMMAND_SEPARATORS:
            continue
        pieces = [token]
        if any(char.isspace() for char in token):
            try:
                pieces = shlex.split(token, posix=True)
            except ValueError:
                pieces = [token]
        names.update(os.path.basename(piece) for piece in pieces if piece)
    return names


def expanded_shell_tokens(command: str) -> list[str]:
    punctuation = "(){}<>|;&"
    lexer = shlex.shlex(command, posix=True, punctuation_chars=punctuation)
    lexer.whitespace_split = True
    tokens: list[str] = []
    for token in lexer:
        if token and all(char in punctuation for char in token):
            index = 0
            while index < len(token):
                pair = token[index : index + 2]
                if pair in {"&&", "||", "|&"}:
                    tokens.append(pair)
                    index += 2
                else:
                    tokens.append(token[index])
                    index += 1
        else:
            tokens.append(token)
    return tokens


def pipeline_groups(command: str) -> list[list[list[str]]]:
    normalized = command.replace("\\\r\n", " ").replace("\\\n", " ")
    tokens = expanded_shell_tokens(normalized)
    groups: list[list[list[str]]] = []
    group: list[list[str]] = []
    segment: list[str] = []
    compound_depth = 0
    control_stack: list[str] = []
    for token in tokens:
        if token in CONTROL_OPENERS:
            control_stack.append(CONTROL_OPENERS[token])
            segment.append(token)
            continue
        if token in CONTROL_CLOSERS:
            if control_stack and control_stack[-1] == token:
                control_stack.pop()
            segment.append(token)
            continue
        if token in COMPOUND_OPENERS:
            compound_depth += 1
            segment.append(token)
            continue
        if token in COMPOUND_CLOSERS:
            compound_depth = max(0, compound_depth - 1)
            segment.append(token)
            continue
        if token in PIPE_OPERATORS:
            group.append(segment)
            segment = []
        elif token in GROUP_OPERATORS and compound_depth == 0 and not control_stack:
            group.append(segment)
            if group:
                groups.append(group)
            group = []
            segment = []
        else:
            segment.append(token)
    group.append(segment)
    if group:
        groups.append(group)
    return groups


def pipes_download_to_shell(command: str) -> bool:
    try:
        groups = pipeline_groups(command)
    except ValueError:
        return False
    for segments in groups:
        downloader_seen = False
        for segment in segments:
            names = command_token_names(segment)
            if downloader_seen and any(name in SHELLS for name in names):
                return True
            if any(name in DOWNLOADERS for name in names):
                downloader_seen = True
    return False


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError, UnicodeError):
        return 0
    if not isinstance(payload, dict):
        return 0
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return 0
    command = tool_input.get("command")
    if not isinstance(command, str) or not pipes_download_to_shell(command):
        return 0
    print(
        "Blocked: piping a remote download directly into a shell. "
        "Download to a file, review it, then run it explicitly.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
