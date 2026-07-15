#!/usr/bin/env python3
"""Generate the five route-specific knowledge packs from cases.jsonl."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ATOM_FILE = ROOT / "知识库" / "原子库" / "cases.jsonl"
CANONICAL_DIR = ROOT / "知识库" / "Skill知识包"
SKILL_DIR = ROOT / "skills" / "sansan-wechat-moments-coach" / "knowledge"
ROUTE_ORDER = ["反馈圈", "收款圈", "咨询圈", "生活圈", "三重天朋友圈"]


def load_atoms() -> list[dict]:
    return [json.loads(line) for line in ATOM_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]


def render_pack(route: str, atoms: list[dict]) -> str:
    lines = [
        f"# {route}案例知识包",
        "",
        "> 本文件由原子库自动生成。案例只用于学习结构、判断和表达，不得把案例事实当成使用者事实。",
        "> 案例中的姓名、产品、价格、时间、收入和结果默认都是历史案例信息，禁止自动复用。",
        "",
        f"共 {len(atoms)} 个完整案例。",
        "",
    ]
    for atom in atoms:
        lines.extend([
            f"<!-- atom_id: {atom['id']} | original_type: {atom['original_type']} | rights_status: {atom['rights_status']} -->",
            atom["raw_markdown"].rstrip(),
            "",
            "---",
            "",
        ])
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for atom in load_atoms():
        grouped[atom["route_type"]].append(atom)

    CANONICAL_DIR.mkdir(parents=True, exist_ok=True)
    SKILL_DIR.mkdir(parents=True, exist_ok=True)
    expected = {f"{route}案例知识包.md" for route in ROUTE_ORDER}
    for directory in (CANONICAL_DIR, SKILL_DIR):
        for old in directory.glob("*案例知识包.md"):
            if old.name not in expected:
                old.unlink()

    for route in ROUTE_ORDER:
        atoms = sorted(grouped[route], key=lambda x: (x["original_type"], x["case_number"]))
        content = render_pack(route, atoms)
        filename = f"{route}案例知识包.md"
        (CANONICAL_DIR / filename).write_text(content, encoding="utf-8")
        (SKILL_DIR / filename).write_text(content, encoding="utf-8")
        print(f"{route}: {len(atoms)} 条")


if __name__ == "__main__":
    main()

