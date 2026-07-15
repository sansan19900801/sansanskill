#!/usr/bin/env python3
"""Validate atom counts, integrity, routes, and generated knowledge packs."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ATOM_FILE = ROOT / "知识库" / "原子库" / "cases.jsonl"
SOURCE_TYPES = {
    "反馈圈": "反馈圈",
    "收款圈": "收款圈",
    "咨询圈": "咨询圈",
    "生活圈": "生活圈",
    "认知圈": "三重天朋友圈",
    "方法圈": "三重天朋友圈",
    "发售圈": "三重天朋友圈",
    "圈层背书圈": "三重天朋友圈",
}
BASELINE_ORIGINAL = {"反馈圈": 13, "收款圈": 7, "咨询圈": 1, "生活圈": 4, "认知圈": 11, "方法圈": 2, "发售圈": 1, "圈层背书圈": 1}


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def fail(message: str, errors: list[str]) -> None:
    errors.append(message)


def main() -> int:
    errors: list[str] = []
    atoms = [json.loads(line) for line in ATOM_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
    source_dir = ROOT / "sources" / "朋友圈案例原文"
    expected_original: Counter[str] = Counter()
    for path in source_dir.glob("*.md"):
        original_type = next((name for name in SOURCE_TYPES if path.name.startswith(name)), None)
        if not original_type:
            fail(f"无法识别原文分类：{path.name}", errors)
            continue
        expected_original[original_type] += len(re.findall(r"^## 案例\s+\d+｜", path.read_text(encoding="utf-8"), re.M))
    expected_route: Counter[str] = Counter()
    for original_type, count in expected_original.items():
        expected_route[SOURCE_TYPES[original_type]] += count

    ids = [atom["id"] for atom in atoms]
    if len(atoms) != sum(expected_original.values()):
        fail(f"原子总数应与原文一致：原文{sum(expected_original.values())}，原子{len(atoms)}", errors)
    if len(ids) != len(set(ids)):
        fail("存在重复原子ID", errors)
    if Counter(a["original_type"] for a in atoms) != expected_original:
        fail(f"原始分类数量不正确：{Counter(a['original_type'] for a in atoms)}", errors)
    if Counter(a["route_type"] for a in atoms) != expected_route:
        fail(f"路由分类数量不正确：{Counter(a['route_type'] for a in atoms)}", errors)
    for original_type, baseline in BASELINE_ORIGINAL.items():
        if expected_original[original_type] < baseline:
            fail(f"{original_type} 少于已确认基线{baseline}条，实际{expected_original[original_type]}条", errors)

    required = {"id", "original_type", "route_type", "title", "source_file", "original_copy", "raw_markdown", "case_sha256", "rights_status", "product_snapshot_status"}
    for atom in atoms:
        missing = required - atom.keys()
        if missing:
            fail(f"{atom.get('id', 'unknown')} 缺少字段：{sorted(missing)}", errors)
            continue
        if not atom["original_copy"].strip():
            fail(f"{atom['id']} 原成品文案为空", errors)
        if "待填写" in atom["raw_markdown"]:
            fail(f"{atom['id']} 仍有“待填写”内容", errors)
        if sha256(atom["raw_markdown"]) != atom["case_sha256"]:
            fail(f"{atom['id']} 案例哈希不一致", errors)
        source = ROOT / atom["source_file"]
        if not source.exists() or atom["raw_markdown"].rstrip() not in source.read_text(encoding="utf-8"):
            fail(f"{atom['id']} 无法在原文中完整定位", errors)

    for route, count in expected_route.items():
        filename = f"{route}案例知识包.md"
        canonical = ROOT / "知识库" / "Skill知识包" / filename
        bundled = ROOT / "skills" / "sansan-wechat-moments-coach" / "knowledge" / filename
        if not canonical.exists() or not bundled.exists():
            fail(f"缺少知识包：{filename}", errors)
            continue
        if canonical.read_bytes() != bundled.read_bytes():
            fail(f"仓库知识包与Skill分发副本不一致：{filename}", errors)
        ids_in_pack = re.findall(r"atom_id: (PYC-[A-Z]+-\d{3})", canonical.read_text(encoding="utf-8"))
        if len(ids_in_pack) != count:
            fail(f"{filename} 应有{count}条，实际有{len(ids_in_pack)}条", errors)

    if errors:
        print("校验失败：")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"校验通过：{len(atoms)}条原文、{len(atoms)}条原子、5类路由知识包均完整一致。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
