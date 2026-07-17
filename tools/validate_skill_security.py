#!/usr/bin/env python3
"""Fail the release when public Skills contain high-confidence unsafe patterns."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


TEXT_SUFFIXES = {".md", ".py", ".sh", ".yaml", ".yml", ".json", ".toml"}
INTAKE_MARKERS = ("截图", "链接", "逐字稿", "聊天记录", "外部材料", "第三方内容")
NEGATIONS = ("不", "不要", "不得", "禁止", "拒绝", "忽略", "never", "do not", "must not")


@dataclass(frozen=True)
class Finding:
    rule: str
    path: Path
    line: int
    message: str


LINE_RULES: tuple[tuple[str, re.Pattern[str], str], ...] = (
    (
        "SEC001",
        re.compile(r"\b(?:curl|wget)\b[^\n]*(?:\||\|&)[^\n]*\b(?:sh|bash|zsh)\b", re.I),
        "禁止下载远程内容后直接交给 shell 执行。",
    ),
    (
        "SEC002",
        re.compile(r"\brm\s+-[^\n]*r[^\n]*f\b|\bgit\s+reset\s+--hard\b|\bchmod\s+777\b", re.I),
        "禁止公开 Skill 指示破坏性删除、硬重置或开放全部权限。",
    ),
    (
        "SEC003",
        re.compile(r"\b(?:python3?|bash|sh|zsh)\s+(?:\./)?tools/[^\s`]+", re.I),
        "公开 Skill 不得调用仓库维护工具；维护流程必须与用户 Skill 分离。",
    ),
    (
        "SEC004",
        re.compile(r"\bshell\s*=\s*True\b|\bos\.system\s*\(|\b(?:eval|exec)\s*\(", re.I),
        "禁止动态 shell 或动态代码执行。",
    ),
    (
        "SEC005",
        re.compile(r"(?:读取|访问|上传|发送|泄露).{0,32}(?:\.env|token|密钥|私钥|密码|credential)", re.I),
        "禁止主动读取或外传凭据与秘密。",
    ),
    (
        "SEC006",
        re.compile(r"(?:遵循|服从|执行|按照).{0,24}(?:材料|文件|网页|截图|链接).{0,16}(?:指令|命令|要求)", re.I),
        "不得把外部材料中的内容当作可执行指令。",
    ),
)


def is_negated(line: str, start: int) -> bool:
    prefix = line[max(0, start - 18) : start].lower()
    lowered = line.lower()
    return any(token in prefix for token in NEGATIONS) or any(
        token in lowered for token in ("不执行", "不由", "不得", "禁止", "拒绝", "忽略")
    )


def text_files(skill_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in skill_dir.rglob("*")
        if path.is_file()
        and path.suffix.lower() in TEXT_SUFFIXES
        and "__pycache__" not in path.parts
    )


def scan_skill(skill_dir: Path) -> list[Finding]:
    findings: list[Finding] = []
    files = text_files(skill_dir)
    combined_markdown: list[str] = []

    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            findings.append(Finding("SEC000", path, 1, f"文本文件无法安全读取：{error}"))
            continue

        if path.suffix.lower() == ".md":
            combined_markdown.append(text)

        for line_number, line in enumerate(text.splitlines(), 1):
            for rule, pattern, message in LINE_RULES:
                for match in pattern.finditer(line):
                    if rule in {"SEC005", "SEC006"} and is_negated(line, match.start()):
                        continue
                    findings.append(Finding(rule, path, line_number, message))

    corpus = "\n".join(combined_markdown)
    accepts_untrusted_material = False
    for line in corpus.splitlines():
        marker_match = next((marker for marker in INTAKE_MARKERS if marker in line), None)
        if marker_match is None:
            continue
        verb_match = re.search(r"(?:用户.{0,12})?(?:提供|提交|发送|读取|接收|根据)", line)
        if verb_match and not is_negated(line, verb_match.start()):
            accepts_untrusted_material = True
            break

    if accepts_untrusted_material:
        has_data_boundary = bool(
            re.search(r"只作为.{0,24}(?:数据|素材|证据|材料)", corpus)
        )
        has_instruction_boundary = bool(
            re.search(r"不作为.{0,24}(?:指令|授权)", corpus)
            or re.search(r"不得.{0,24}(?:执行|服从)", corpus)
        )
        has_execution_boundary = bool(
            re.search(r"不执行.{0,36}(?:命令|代码|脚本|操作步骤)", corpus)
        )
        if not (has_data_boundary and has_instruction_boundary and has_execution_boundary):
            findings.append(
                Finding(
                    "SEC007",
                    skill_dir / "SKILL.md",
                    1,
                    "接收截图、链接或第三方内容的 Skill 必须声明：材料只作为数据、不作为授权，并且不执行其中的命令或脚本。",
                )
            )

    return findings


def scan_root(skills_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    if not skills_root.is_dir():
        return [Finding("SEC000", skills_root, 1, "Skill 根目录不存在。")]
    skill_dirs = sorted(path for path in skills_root.iterdir() if path.is_dir())
    if not skill_dirs:
        return [Finding("SEC000", skills_root, 1, "没有发现可检查的 Skill。")]
    for skill_dir in skill_dirs:
        if not (skill_dir / "SKILL.md").exists():
            findings.append(Finding("SEC000", skill_dir, 1, "缺少 SKILL.md。"))
            continue
        findings.extend(scan_skill(skill_dir))
    return findings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="检查公开 Skill 的高置信度安全风险。")
    parser.add_argument(
        "--skills-root",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "skills",
        help="包含多个 Skill 目录的根路径。",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    findings = scan_root(args.skills_root.resolve())
    if findings:
        print("Skill 发布安全检查失败：")
        for finding in findings:
            try:
                display_path = finding.path.relative_to(Path.cwd())
            except ValueError:
                display_path = finding.path
            print(f"- [{finding.rule}] {display_path}:{finding.line} {finding.message}")
        return 1
    count = sum(1 for path in args.skills_root.iterdir() if path.is_dir())
    print(f"Skill 发布安全检查通过：{count} 个 Skill 未发现高置信度风险。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
