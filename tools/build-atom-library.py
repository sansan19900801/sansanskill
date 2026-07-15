#!/usr/bin/env python3
"""Build the complete JSONL atom library from the Markdown source of truth."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "sources" / "朋友圈案例原文"
OUTPUT = ROOT / "知识库" / "原子库" / "cases.jsonl"
METADATA_FILE = ROOT / "知识库" / "原子库" / "case-metadata.json"

TYPE_CONFIG = {
    "反馈圈": {"prefix": "FDB", "route": "反馈圈", "goal": "证明客户使用前后的真实变化"},
    "收款圈": {"prefix": "SK", "route": "收款圈", "goal": "证明客户为什么愿意为产品付款"},
    "咨询圈": {"prefix": "ZX", "route": "咨询圈", "goal": "证明内容或业务吸引了精准咨询"},
    "生活圈": {"prefix": "SH", "route": "生活圈", "goal": "通过真实生活事件建立人物感和信任"},
    "认知圈": {"prefix": "RZ", "route": "三重天朋友圈", "goal": "表达观点并建立认知信任"},
    "方法圈": {"prefix": "FF", "route": "三重天朋友圈", "goal": "展示可复用的方法和业务过程"},
    "发售圈": {"prefix": "FS", "route": "三重天朋友圈", "goal": "承接真实产品发售"},
    "圈层背书圈": {"prefix": "QS", "route": "三重天朋友圈", "goal": "通过真实邀请或圈层事件建立信任"},
}


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def source_type(path: Path) -> str:
    for name in TYPE_CONFIG:
        if path.name.startswith(name):
            return name
    raise ValueError(f"无法从文件名识别分类：{path.name}")


def split_cases(text: str) -> list[tuple[int, str, str]]:
    matches = list(re.finditer(r"^## 案例\s+(\d+)｜(.+?)\s*$", text, re.M))
    cases = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        cases.append((int(match.group(1)), match.group(2).strip(), text[match.start():end].rstrip() + "\n"))
    return cases


def parse_sections(raw: str) -> dict[str, str]:
    matches = list(re.finditer(r"^### (.+?)\s*$", raw, re.M))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(raw)
        sections[match.group(1).strip()] = raw[match.end():end].strip()
    return sections


def first_matching(sections: dict[str, str], patterns: tuple[str, ...]) -> str:
    for key, value in sections.items():
        if any(pattern in key for pattern in patterns):
            return value
    return ""


def product_snapshot_status(raw: str) -> str:
    price_or_offer = re.search(r"(?:¥|￥|\d{2,6}\s*元|\d{2,6}块|原价|前\d+名|审核金|实战班|训练营|高手班|商业班)", raw)
    return "historical" if price_or_offer else "unknown"


def main() -> None:
    atoms = []
    seen_ids = set()
    metadata = json.loads(METADATA_FILE.read_text(encoding="utf-8")) if METADATA_FILE.exists() else {}
    for path in sorted(SOURCE_DIR.glob("*.md")):
        original_type = source_type(path)
        config = TYPE_CONFIG[original_type]
        source_text = path.read_text(encoding="utf-8")
        for case_number, title, raw in split_cases(source_text):
            atom_id = f"PYC-{config['prefix']}-{case_number:03d}"
            if atom_id in seen_ids:
                raise ValueError(f"重复编号：{atom_id}")
            seen_ids.add(atom_id)
            sections = parse_sections(raw)
            original_copy = first_matching(sections, ("原成品文案",))
            if not original_copy:
                raise ValueError(f"{atom_id} 缺少“原成品文案”")
            evidence = first_matching(sections, ("证据", "截图"))
            facts = first_matching(sections, ("使用者提供", "核心观点", "核心主张", "工作流", "方法与结果"))
            overrides = metadata.get(atom_id, {})
            rights_status = overrides.get("rights_status", "unknown")
            if rights_status not in {"owned", "authorized", "external-reference", "unknown"}:
                raise ValueError(f"{atom_id} 的 rights_status 无效：{rights_status}")
            atom = {
                "schema_version": "1.0",
                "id": atom_id,
                "status": "active",
                "original_type": original_type,
                "route_type": config["route"],
                "case_number": case_number,
                "title": title,
                "business_goal": config["goal"],
                "source_file": str(path.relative_to(ROOT)),
                "source_heading": f"案例 {case_number:02d}｜{title}",
                "source_file_sha256": sha256(source_text),
                "case_sha256": sha256(raw),
                "rights_status": rights_status,
                "publishable": bool(overrides.get("publishable", rights_status in {"owned", "authorized"})),
                "product_snapshot_status": overrides.get("product_snapshot_status", product_snapshot_status(raw)),
                "evidence_status": evidence,
                "facts": facts,
                "original_copy": original_copy,
                "sections": sections,
                "raw_markdown": raw,
                "tags": [original_type, config["route"], "朋友圈案例"],
            }
            atoms.append(atom)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    content = "".join(json.dumps(atom, ensure_ascii=False, sort_keys=True) + "\n" for atom in atoms)
    OUTPUT.write_text(content, encoding="utf-8")
    print(f"已生成 {len(atoms)} 条案例原子：{OUTPUT}")


if __name__ == "__main__":
    main()
