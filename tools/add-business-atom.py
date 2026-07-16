#!/usr/bin/env python3
"""Append a fill-in template for a new business atom."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "sources" / "商业原子原文"
CONFIG = {
    "principle": ("SS-PRINCIPLE", "三三商业观点.md"),
    "case": ("SS-CASE", "真实诊断案例.md"),
    "experiment": ("SS-EXP", "业务实验与复盘.md"),
    "external-model": ("EXT-MODEL", "外部方法论.md"),
}


def next_id(prefix: str) -> str:
    pattern = re.compile(rf"^## {re.escape(prefix)}-(\d+)｜", re.M)
    numbers: list[int] = []
    for path in SOURCE_DIR.glob("*.md"):
        numbers.extend(int(value) for value in pattern.findall(path.read_text(encoding="utf-8")))
    return f"{prefix}-{max(numbers, default=0) + 1:03d}"


def template(atom_id: str, title: str, atom_type: str) -> str:
    rights = "external-reference" if atom_type == "external-model" else "unknown"
    return f'''\n\n## {atom_id}｜{title}\n\n### atom_type\n\n{atom_type}\n\n### knowledge\n\n[待填写]\n\n### original\n\n[待填写完整原文或能够支撑判断的原始片段]\n\n### source_platform\n\n[待填写]\n\n### source_author\n\n[待填写]\n\n### source_url\n\n[无链接时填写“无公开链接”]\n\n### source_date\n\n[未知时填写“未知”]\n\n### upstream_atom_id\n\n[没有则填写“无”]\n\n### source_file\n\n[待填写]\n\n### source_heading\n\n[待填写]\n\n### applicable_conditions\n\n- [待填写]\n\n### counter_conditions\n\n- [待填写]\n\n### evidence_level\n\n[待填写]\n\n### rights_status\n\n{rights}\n\n### publishable\n\nfalse\n\n### linked_skills\n\n- sansan-business-diagnosis\n\n### status\n\ndraft\n\n### tags\n\n- [待填写]\n'''


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", required=True, choices=CONFIG)
    parser.add_argument("--title", required=True)
    args = parser.parse_args()
    prefix, filename = CONFIG[args.type]
    atom_id = next_id(prefix)
    path = SOURCE_DIR / filename
    with path.open("a", encoding="utf-8") as handle:
        handle.write(template(atom_id, args.title.strip(), args.type))
    print(f"已新增模板 {atom_id}：{path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
