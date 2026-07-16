#!/usr/bin/env python3
"""Validate the multi-skill registry, references, and routing test contract."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
REGISTRY = SKILLS / "sansan" / "references" / "route-registry.md"
TESTS = ROOT / "tests" / "router-cases.md"
DIAGNOSIS_TESTS = ROOT / "tests" / "diagnosis-cases.md"
STATE_TESTS = ROOT / "tests" / "state-cases.md"


def main() -> int:
    errors: list[str] = []
    skill_dirs = sorted(path for path in SKILLS.iterdir() if path.is_dir())
    names: set[str] = set()

    for directory in skill_dirs:
        skill_file = directory / "SKILL.md"
        if not skill_file.exists():
            errors.append(f"{directory.name} 缺少SKILL.md")
            continue
        text = skill_file.read_text(encoding="utf-8")
        match = re.search(r"^name:\s*([^\n]+)$", text, re.M)
        if not match:
            errors.append(f"{directory.name} 缺少name")
        elif match.group(1).strip() != directory.name:
            errors.append(f"{directory.name} 的name不一致：{match.group(1).strip()}")
        names.add(directory.name)
        if "TODO" in text:
            errors.append(f"{directory.name} 仍包含TODO")
        for ref in re.findall(r"\]\((references/[^)]+)\)", text):
            if not (directory / ref).exists():
                errors.append(f"{directory.name} 缺少引用：{ref}")

    registry_text = REGISTRY.read_text(encoding="utf-8")
    ready = set(re.findall(r"\| `([^`]+)` \| ready \|", registry_text))
    missing = ready - names
    if missing:
        errors.append(f"注册为ready但目录不存在：{sorted(missing)}")

    router_text = (SKILLS / "sansan" / "SKILL.md").read_text(encoding="utf-8")
    routed = set(re.findall(r"`(sansan(?:-[a-z0-9-]+)?)`", router_text)) - {"sansan"}
    undeclared = routed - ready
    if undeclared:
        errors.append(f"总入口引用了未ready能力：{sorted(undeclared)}")

    test_text = TESTS.read_text(encoding="utf-8")
    case_count = len(re.findall(r"^\|\s*\d+\s*\|", test_text, re.M))
    if case_count < 30:
        errors.append(f"路由测试少于30条：{case_count}")

    diagnosis_test_text = DIAGNOSIS_TESTS.read_text(encoding="utf-8") if DIAGNOSIS_TESTS.exists() else ""
    diagnosis_case_count = len(re.findall(r"^\|\s*\d+\s*\|", diagnosis_test_text, re.M))
    if diagnosis_case_count < 20:
        errors.append(f"商业诊断测试少于20条：{diagnosis_case_count}")

    diagnosis_dir = SKILLS / "sansan-business-diagnosis"
    required_diagnosis_files = [
        diagnosis_dir / "SKILL.md",
        diagnosis_dir / "references" / "consultation-mode.md",
        diagnosis_dir / "references" / "health-check-mode.md",
        diagnosis_dir / "references" / "business-dimensions.md",
        diagnosis_dir / "references" / "signal-tracking.md",
        diagnosis_dir / "references" / "report-template.md",
        diagnosis_dir / "references" / "atom-intake.md",
        diagnosis_dir / "references" / "business-case-pack.md",
    ]
    for path in required_diagnosis_files:
        if not path.exists():
            errors.append(f"商业诊断缺少文件：{path.relative_to(ROOT)}")

    updater_dir = SKILLS / "sansan-update"
    for path in [updater_dir / "SKILL.md", updater_dir / "agents" / "openai.yaml"]:
        if not path.exists():
            errors.append(f"系统更新器缺少文件：{path.relative_to(ROOT)}")

    state_test_text = STATE_TESTS.read_text(encoding="utf-8") if STATE_TESTS.exists() else ""
    state_case_count = len(re.findall(r"^\|\s*\d+\s*\|", state_test_text, re.M))
    if state_case_count < 15:
        errors.append(f"本地状态测试少于15条：{state_case_count}")

    required_state_files = [
        SKILLS / "sansan-save" / "SKILL.md",
        SKILLS / "sansan-save" / "agents" / "openai.yaml",
        SKILLS / "sansan-save" / "references" / "record-schema.md",
        SKILLS / "sansan-save" / "scripts" / "record_store.py",
        SKILLS / "sansan-restore" / "SKILL.md",
        SKILLS / "sansan-restore" / "agents" / "openai.yaml",
        SKILLS / "sansan-restore" / "references" / "restore-view.md",
        SKILLS / "sansan-report" / "SKILL.md",
        SKILLS / "sansan-report" / "agents" / "openai.yaml",
        SKILLS / "sansan-report" / "references" / "report-schema.md",
    ]
    for path in required_state_files:
        if not path.exists():
            errors.append(f"本地状态系统缺少文件：{path.relative_to(ROOT)}")

    if errors:
        print("系统校验失败：")
        for error in errors:
            print(f"- {error}")
        return 1

    print(
        f"系统校验通过：{len(names)}个Skill、{len(ready)}个ready专项、"
        f"{case_count}条路由测试、{diagnosis_case_count}条商业诊断测试、"
        f"{state_case_count}条本地状态测试。"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
