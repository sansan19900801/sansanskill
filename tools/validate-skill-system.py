#!/usr/bin/env python3
"""Validate the multi-skill registry, references, and routing test contract."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
REGISTRY = SKILLS / "sansan-business-router" / "references" / "route-registry.md"
TESTS = ROOT / "tests" / "router-cases.md"


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

    router_text = (SKILLS / "sansan-business-router" / "SKILL.md").read_text(encoding="utf-8")
    routed = set(re.findall(r"`(sansan-[a-z0-9-]+)`", router_text)) - {"sansan-business-router"}
    undeclared = routed - ready
    if undeclared:
        errors.append(f"总入口引用了未ready能力：{sorted(undeclared)}")

    test_text = TESTS.read_text(encoding="utf-8")
    case_count = len(re.findall(r"^\|\s*\d+\s*\|", test_text, re.M))
    if case_count < 30:
        errors.append(f"路由测试少于30条：{case_count}")

    if errors:
        print("系统校验失败：")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"系统校验通过：{len(names)}个Skill、{len(ready)}个ready专项、{case_count}条路由测试。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
