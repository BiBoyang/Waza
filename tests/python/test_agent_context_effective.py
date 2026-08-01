import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills" / "health" / "scripts" / "check_agent_context.py"
CANONICAL_PIPE_HOOK = (
    ROOT / "skills" / "health" / "scripts" / "block-pipe-to-shell.py"
)


def run_context(project: Path, home: Path) -> str:
    env = os.environ.copy()
    env["HOME"] = str(home)
    result = subprocess.run(
        [sys.executable, "-I", str(SCRIPT), str(project), "deep"],
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def write_skill(path: Path, name: str, body: str = "same body") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\nname: {name}\n---\n\n{body}\n", encoding="utf-8")


def complete_claude_floor(home: Path) -> dict[str, object]:
    hook = home / "hooks" / "block-pipe-to-shell.py"
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_bytes(CANONICAL_PIPE_HOOK.read_bytes())
    return {
        "permissions": {
            "deny": [
                "Read(~/.ssh/**)",
                "Read(~/.aws/**)",
                "Read(~/.gnupg/**)",
                "Read(~/.config/gh/**)",
                "Read(**/.env*)",
                "Read(**/*credentials*)",
                "Read(**/secrets/**)",
                "Bash(ssh:*)",
                "Bash(scp:*)",
                "Bash(nc:*)",
                "Bash(git reset --hard:*)",
            ]
        },
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "Bash",
                    "hooks": [
                        {
                            "type": "command",
                            "command": "python3 ~/hooks/block-pipe-to-shell.py",
                        }
                    ],
                }
            ]
        },
    }


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlink support required")
def test_effective_permissions_aliases_and_path_context_are_reported(tmp_path: Path):
    project = tmp_path / "project"
    home = tmp_path / "home"
    project.mkdir()
    agents = project / "AGENTS.md"
    agents.write_text("# Guide\n\n## Git Safety\n\n## Verification\n", encoding="utf-8")
    (project / "CLAUDE.md").symlink_to("AGENTS.md")

    global_settings = complete_claude_floor(home)
    write_json(home / ".claude" / "settings.json", global_settings)
    write_json(
        project / ".claude" / "settings.local.json",
        {"permissions": {"allow": ["Read(//Users/example/**)"]}},
    )

    rules = project / ".claude" / "rules"
    rules.mkdir(parents=True)
    (rules / "one.md").write_text(
        '---\npaths:\n  - "project.yml"\n  - "Sources/**"\n---\nalpha beta\n',
        encoding="utf-8",
    )
    (rules / "two.md").write_text(
        '---\npaths:\n  - "project.yml"\n---\ngamma delta epsilon\n',
        encoding="utf-8",
    )
    (rules / "one-alias.md").symlink_to("one.md")

    write_skill(home / ".agents" / "skills" / "demo" / "SKILL.md", "demo")
    write_skill(home / ".codex" / "skills" / "demo" / "SKILL.md", "demo")

    output = run_context(project, home)

    assert "claude_aliases_agents: yes" in output
    instruction_files = output.split("instruction_files:\n", 1)[1].split(
        "instruction_findings:", 1
    )[0]
    assert instruction_files == "  AGENTS.md\n"
    assert "AGENTS.md and CLAUDE.md both contain substantial guidance" not in output
    assert "configured_sensitive_deny_floor_complete: yes" in output
    assert "broad_read_allow_present: yes" in output
    assert "permission_findings:\n  (none)" in output
    assert "path_scoped_rule_files: 2" in output
    assert "selector=project.yml files=2" in output
    assert "duplicate_skill_names: 1" in output
    assert "demo: kind=exact-copy" in output


def test_missing_global_deny_categories_remain_visible(tmp_path: Path):
    project = tmp_path / "project"
    home = tmp_path / "home"
    project.mkdir()
    (project / "AGENTS.md").write_text("# Guide\n", encoding="utf-8")
    write_json(home / ".claude" / "settings.json", {"permissions": {"deny": []}})

    output = run_context(project, home)

    assert "configured_sensitive_deny_floor_complete: no" in output
    assert "deny_ssh_directory: no" in output
    assert "deny_pipe_to_shell: no" in output
    assert "configured global + shared project + local project deny floor is incomplete" in output


def test_shared_and_local_project_settings_are_merged_into_effective_permissions(
    tmp_path: Path,
):
    project = tmp_path / "project"
    home = tmp_path / "home"
    project.mkdir()
    (project / "AGENTS.md").write_text("# Guide\n", encoding="utf-8")
    write_json(project / ".claude" / "settings.json", complete_claude_floor(home))
    write_json(
        project / ".claude" / "settings.local.json",
        {"permissions": {"allow": ["Read(//Users/example/**)"]}},
    )

    output = run_context(project, home)

    assert "shared_project_settings_json: yes" in output
    assert "local_project_settings_json: yes" in output
    assert "shared_deny_count: 11" in output
    assert "local_allow_count: 1" in output
    assert "configured_sensitive_deny_floor_complete: yes" in output
    assert "broad_read_allow_present: yes" in output
    assert "permission_findings:\n  (none)" in output


def test_absent_claude_settings_make_deny_floor_not_applicable(tmp_path: Path):
    project = tmp_path / "project"
    home = tmp_path / "home"
    project.mkdir()
    (project / "AGENTS.md").write_text("# Guide\n", encoding="utf-8")

    output = run_context(project, home)

    assert "configured_sensitive_deny_floor_complete: not_applicable" in output
    assert "deny floor is incomplete" not in output
    assert "permission_findings:\n  (none)" in output


def test_malformed_shared_settings_are_reported(tmp_path: Path):
    project = tmp_path / "project"
    home = tmp_path / "home"
    project.mkdir()
    (project / "AGENTS.md").write_text("# Guide\n", encoding="utf-8")
    shared = project / ".claude" / "settings.json"
    shared.parent.mkdir()
    shared.write_text("{not-json\n", encoding="utf-8")

    output = run_context(project, home)

    assert "shared: settings.json: invalid JSON at line 1" in output
    assert "claude_status: WARN" in output


def test_substring_lookalikes_and_missing_hook_handler_do_not_false_pass(
    tmp_path: Path,
):
    project = tmp_path / "project"
    home = tmp_path / "home"
    project.mkdir()
    (project / "AGENTS.md").write_text("# Guide\n", encoding="utf-8")
    write_json(
        home / ".claude" / "settings.json",
        {
            "permissions": {
                "deny": [
                    "Read(docs/.ssh-warning.md)",
                    "Read(docs/.ssh/**)",
                    "Read(docs/.awsome.md)",
                    "Read(docs/.aws/**)",
                    "Read(docs/credential-policy.md)",
                    "Bash(echo ssh scp nc git reset --hard)",
                ]
            },
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "NotBash",
                        "hooks": [
                            {
                                "type": "command",
                                "command": "bash ~/hooks/missing-pipe-to-shell.sh",
                            }
                        ],
                    }
                ]
            },
        },
    )

    output = run_context(project, home)

    assert "configured_sensitive_deny_floor_complete: no" in output
    assert "pretool_pipe_to_shell_hook: no" in output
    assert "deny_ssh_directory: no" in output
    assert "deny_outbound_shell: no" in output
    assert "deny_git_reset_hard: no" in output


def test_existing_but_noop_pipe_hook_does_not_false_pass(tmp_path: Path):
    project = tmp_path / "project"
    home = tmp_path / "home"
    project.mkdir()
    (project / "AGENTS.md").write_text("# Guide\n", encoding="utf-8")
    settings = complete_claude_floor(home)
    (home / "hooks" / "block-pipe-to-shell.py").write_text(
        "#!/bin/bash\nexit 0\n",
        encoding="utf-8",
    )
    write_json(home / ".claude" / "settings.json", settings)

    output = run_context(project, home)

    assert "pretool_pipe_to_shell_hook: no" in output
    assert "deny_pipe_to_shell: no" in output
    assert "configured_sensitive_deny_floor_complete: no" in output


def test_misleading_hook_comments_and_disconnected_exit_do_not_false_pass(
    tmp_path: Path,
):
    project = tmp_path / "project"
    home = tmp_path / "home"
    project.mkdir()
    (project / "AGENTS.md").write_text("# Guide\n", encoding="utf-8")
    settings = complete_claude_floor(home)
    (home / "hooks" / "block-pipe-to-shell.py").write_text(
        "#!/bin/bash\n"
        "# tool_input command curl wget [|] bash exit 2\n"
        "command=unrelated\n"
        "exit 2\n",
        encoding="utf-8",
    )
    write_json(home / ".claude" / "settings.json", settings)

    output = run_context(project, home)

    assert "pretool_pipe_to_shell_hook: no" in output
    assert "deny_pipe_to_shell: no" in output


def test_unreachable_canonical_words_do_not_false_pass(tmp_path: Path):
    project = tmp_path / "project"
    home = tmp_path / "home"
    project.mkdir()
    (project / "AGENTS.md").write_text("# Guide\n", encoding="utf-8")
    settings = complete_claude_floor(home)
    (home / "hooks" / "block-pipe-to-shell.py").write_text(
        "#!/bin/bash\n"
        "if false && test -n 'tool_input command curl wget [|] bash'; then\n"
        "  exit 2\n"
        "fi\n"
        "exit 0\n",
        encoding="utf-8",
    )
    write_json(home / ".claude" / "settings.json", settings)

    output = run_context(project, home)

    assert "pretool_pipe_to_shell_hook: no" in output
    assert "deny_pipe_to_shell: no" in output


def test_wrong_matcher_does_not_enable_real_pipe_hook(tmp_path: Path):
    project = tmp_path / "project"
    home = tmp_path / "home"
    project.mkdir()
    (project / "AGENTS.md").write_text("# Guide\n", encoding="utf-8")
    settings = complete_claude_floor(home)
    settings["hooks"]["PreToolUse"][0]["matcher"] = "NotBash"
    write_json(home / ".claude" / "settings.json", settings)

    output = run_context(project, home)

    assert "pretool_pipe_to_shell_hook: no" in output
    assert "deny_pipe_to_shell: no" in output


def test_absolute_shell_interpreter_executes_real_pipe_hook(tmp_path: Path):
    project = tmp_path / "project"
    home = tmp_path / "home"
    project.mkdir()
    (project / "AGENTS.md").write_text("# Guide\n", encoding="utf-8")
    settings = complete_claude_floor(home)
    settings["hooks"]["PreToolUse"][0]["hooks"][0]["command"] = (
        "python3 ~/hooks/block-pipe-to-shell.py"
    )
    write_json(home / ".claude" / "settings.json", settings)

    output = run_context(project, home)

    assert "pretool_pipe_to_shell_hook: yes" in output
    assert "configured_sensitive_deny_floor_complete: yes" in output


@pytest.mark.parametrize(
    "suffix",
    [" || true", " | cat", " ; true", " &", " </dev/null", " 0</dev/null"],
)
def test_pipe_hook_with_trailing_shell_syntax_is_not_enforcing(
    tmp_path: Path,
    suffix: str,
):
    project = tmp_path / "project"
    home = tmp_path / "home"
    project.mkdir()
    (project / "AGENTS.md").write_text("# Guide\n", encoding="utf-8")
    settings = complete_claude_floor(home)
    settings["hooks"]["PreToolUse"][0]["hooks"][0]["command"] = (
        f"python3 -I ~/hooks/block-pipe-to-shell.py{suffix}"
    )
    write_json(home / ".claude" / "settings.json", settings)

    output = run_context(project, home)

    assert "pretool_pipe_to_shell_hook: no" in output
    assert "deny_pipe_to_shell: no" in output
    assert "configured_sensitive_deny_floor_complete: no" in output


def test_hook_path_passed_to_unrelated_command_does_not_execute(tmp_path: Path):
    project = tmp_path / "project"
    home = tmp_path / "home"
    project.mkdir()
    (project / "AGENTS.md").write_text("# Guide\n", encoding="utf-8")
    settings = complete_claude_floor(home)
    settings["hooks"]["PreToolUse"][0]["hooks"][0]["command"] = (
        "echo ~/hooks/block-pipe-to-shell.py"
    )
    write_json(home / ".claude" / "settings.json", settings)

    output = run_context(project, home)

    assert "pretool_pipe_to_shell_hook: no" in output
    assert "deny_pipe_to_shell: no" in output


def test_nonexecutable_hook_path_does_not_enable_pipe_hook(tmp_path: Path):
    project = tmp_path / "project"
    home = tmp_path / "home"
    project.mkdir()
    (project / "AGENTS.md").write_text("# Guide\n", encoding="utf-8")
    settings = complete_claude_floor(home)
    settings["hooks"]["PreToolUse"][0]["hooks"][0]["command"] = (
        "~/hooks/block-pipe-to-shell.py"
    )
    write_json(home / ".claude" / "settings.json", settings)

    output = run_context(project, home)

    assert "pretool_pipe_to_shell_hook: no" in output
    assert "deny_pipe_to_shell: no" in output


def test_codex_plugin_cache_is_not_treated_as_active_skill_routing(tmp_path: Path):
    project = tmp_path / "project"
    home = tmp_path / "home"
    project.mkdir()
    (project / "AGENTS.md").write_text("# Guide\n", encoding="utf-8")
    write_skill(home / ".codex" / "skills" / "demo" / "SKILL.md", "demo")
    write_skill(
        home
        / ".codex"
        / "plugins"
        / "cache"
        / "vendor"
        / "1.0.0"
        / "skills"
        / "demo"
        / "SKILL.md",
        "demo",
    )

    output = run_context(project, home)

    assert "skill_files_scanned: 1" in output
    assert "duplicate_skill_names: 0" in output


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlink support required")
def test_generated_plugin_mirror_is_not_a_second_direct_skill_surface(tmp_path: Path):
    project = tmp_path / "project"
    home = tmp_path / "home"
    repository = tmp_path / "waza-source"
    project.mkdir()
    (project / "AGENTS.md").write_text("# Guide\n", encoding="utf-8")
    write_skill(repository / "skills" / "check" / "SKILL.md", "check")
    write_skill(
        repository / "plugins" / "waza" / "skills" / "check" / "SKILL.md",
        "check",
    )
    skill_root = home / ".codex" / "skills"
    skill_root.mkdir(parents=True)
    (skill_root / "waza").symlink_to(repository, target_is_directory=True)

    output = run_context(project, home)

    assert "skill_files_scanned: 1" in output
    assert "duplicate_skill_names: 0" in output
