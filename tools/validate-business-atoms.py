#!/usr/bin/env python3
"""Validate generated business atoms and their public knowledge pack."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ATOM_FILE = ROOT / "知识库" / "原子库" / "business-atoms.jsonl"
PACK = ROOT / "知识库" / "Skill知识包" / "商业诊断案例知识包.md"
SKILL_PACK = ROOT / "skills" / "sansan-business-diagnosis" / "references" / "business-case-pack.md"


def main() -> int:
    errors: list[str] = []
    if not ATOM_FILE.exists():
        errors.append("缺少 business-atoms.jsonl")
        atoms = []
    else:
        atoms = [json.loads(line) for line in ATOM_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
    ids = [item["id"] for item in atoms]
    if len(ids) != len(set(ids)):
        errors.append("商业原子ID重复")
    for item in atoms:
        if item["publishable"] and item["rights_status"] not in {"owned", "authorized"}:
            errors.append(f"{item['id']} 无公开权利")
        if not item["applicable_conditions"] or not item["counter_conditions"]:
            errors.append(f"{item['id']} 缺少适用或不适用条件")
        source = ROOT / item["source_file"]
        if not source.exists():
            errors.append(f"{item['id']} 的来源文件不存在：{item['source_file']}")
    if not PACK.exists() or not SKILL_PACK.exists():
        errors.append("商业诊断知识包未生成")
    elif PACK.read_text(encoding="utf-8") != SKILL_PACK.read_text(encoding="utf-8"):
        errors.append("仓库知识包与Skill分发副本不一致")
    if errors:
        print("商业原子校验失败：")
        for error in errors:
            print(f"- {error}")
        return 1
    public_count = sum(1 for item in atoms if item["publishable"] and item["status"] == "active")
    print(f"商业原子校验通过：{len(atoms)}条原子，{public_count}条公开。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
