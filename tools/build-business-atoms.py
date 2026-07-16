#!/usr/bin/env python3
"""Build the business atom library and the public diagnosis knowledge pack."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "sources" / "商业原子原文"
OUTPUT = ROOT / "知识库" / "原子库" / "business-atoms.jsonl"
PACK = ROOT / "知识库" / "Skill知识包" / "商业诊断案例知识包.md"
SKILL_PACK = ROOT / "skills" / "sansan-business-diagnosis" / "references" / "business-case-pack.md"

REQUIRED = {
    "atom_type",
    "knowledge",
    "original",
    "source_platform",
    "source_author",
    "source_url",
    "source_date",
    "source_file",
    "source_heading",
    "applicable_conditions",
    "counter_conditions",
    "evidence_level",
    "rights_status",
    "publishable",
    "linked_skills",
    "status",
    "tags",
}
VALID_TYPES = {"principle", "case", "experiment", "external-model"}
VALID_RIGHTS = {"owned", "authorized", "external-reference", "unknown"}


def split_atoms(text: str) -> list[tuple[str, str, str]]:
    matches = list(re.finditer(r"^## ([A-Z0-9-]+)｜(.+?)\s*$", text, re.M))
    atoms = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        atoms.append((match.group(1), match.group(2).strip(), text[match.start():end].rstrip() + "\n"))
    return atoms


def parse_sections(raw: str) -> dict[str, str]:
    matches = list(re.finditer(r"^### ([a-z_]+)\s*$", raw, re.M))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(raw)
        sections[match.group(1)] = raw[match.end():end].strip()
    return sections


def list_values(value: str) -> list[str]:
    return [re.sub(r"^-\s*", "", line).rstrip("；").strip() for line in value.splitlines() if line.strip().startswith("-")]


def boolean(value: str, atom_id: str) -> bool:
    normalized = value.strip().lower()
    if normalized not in {"true", "false"}:
        raise ValueError(f"{atom_id} 的 publishable 必须是 true 或 false")
    return normalized == "true"


def build_atoms() -> list[dict]:
    atoms: list[dict] = []
    seen: set[str] = set()
    for path in sorted(SOURCE_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        for atom_id, title, raw in split_atoms(text):
            if atom_id in seen:
                raise ValueError(f"重复商业原子编号：{atom_id}")
            seen.add(atom_id)
            sections = parse_sections(raw)
            missing = REQUIRED - sections.keys()
            if missing:
                raise ValueError(f"{atom_id} 缺少字段：{sorted(missing)}")
            atom_type = sections["atom_type"].strip()
            rights = sections["rights_status"].strip()
            if atom_type not in VALID_TYPES:
                raise ValueError(f"{atom_id} 的 atom_type 无效：{atom_type}")
            if rights not in VALID_RIGHTS:
                raise ValueError(f"{atom_id} 的 rights_status 无效：{rights}")
            publishable = boolean(sections["publishable"], atom_id)
            if publishable and rights not in {"owned", "authorized"}:
                raise ValueError(f"{atom_id} 权利状态为 {rights}，不能公开")
            atoms.append({
                "schema_version": "1.0",
                "id": atom_id,
                "atom_type": atom_type,
                "title": title,
                "knowledge": sections["knowledge"],
                "original": sections["original"],
                "source_platform": sections["source_platform"],
                "source_author": sections["source_author"],
                "source_url": sections["source_url"],
                "source_date": sections["source_date"],
                "upstream_atom_id": sections.get("upstream_atom_id", ""),
                "source_file": sections["source_file"],
                "source_heading": sections["source_heading"],
                "source_record": str(path.relative_to(ROOT)),
                "applicable_conditions": list_values(sections["applicable_conditions"]),
                "counter_conditions": list_values(sections["counter_conditions"]),
                "evidence_level": sections["evidence_level"],
                "rights_status": rights,
                "publishable": publishable,
                "linked_skills": list_values(sections["linked_skills"]),
                "status": sections["status"].strip(),
                "tags": list_values(sections["tags"]),
            })
    return sorted(atoms, key=lambda item: item["id"])


def render_pack(atoms: list[dict]) -> str:
    public = [item for item in atoms if item["status"] == "active" and item["publishable"]]
    lines = [
        "# 三三商业诊断案例知识包",
        "",
        "> 本文件由商业原子库自动生成。原子用于辅助判断，不能当作当前用户的事实。",
        "> 使用前检查适用条件、反例边界和证据等级；单个案例不能证明普遍规律。",
        "",
        f"当前公开原子：{len(public)} 条。",
        "",
    ]
    for atom in public:
        lines.extend([
            f"## {atom['id']}｜{atom['title']}",
            "",
            f"- 类型：`{atom['atom_type']}`",
            f"- 来源：{atom['source_author']}｜{atom['source_platform']}｜{atom['source_heading']}｜{atom['source_date']}",
            f"- 上游原子：`{atom['upstream_atom_id'] or '无'}`",
            f"- 证据等级：{atom['evidence_level']}",
            "",
            "### 核心判断",
            "",
            atom["knowledge"],
            "",
            "### 原始内容",
            "",
            atom["original"],
            "",
            "### 适用条件",
            "",
            *[f"- {value}" for value in atom["applicable_conditions"]],
            "",
            "### 不适用条件",
            "",
            *[f"- {value}" for value in atom["counter_conditions"]],
            "",
            "---",
            "",
        ])
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    atoms = build_atoms()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("".join(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n" for item in atoms), encoding="utf-8")
    content = render_pack(atoms)
    PACK.parent.mkdir(parents=True, exist_ok=True)
    SKILL_PACK.parent.mkdir(parents=True, exist_ok=True)
    PACK.write_text(content, encoding="utf-8")
    SKILL_PACK.write_text(content, encoding="utf-8")
    print(f"已生成 {len(atoms)} 条商业原子，其中 {sum(1 for item in atoms if item['publishable'] and item['status'] == 'active')} 条进入公开知识包。")


if __name__ == "__main__":
    main()
