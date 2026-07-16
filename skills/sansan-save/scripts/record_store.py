#!/usr/bin/env python3
"""Private local record store for sansanskill.

Creates append-only Markdown records and reports under ~/.sansan with safe
path segments, private permissions, deterministic listing, and JSON receipts.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import tempfile
import unicodedata
from datetime import datetime
from pathlib import Path


KINDS = {"record": "records", "report": "reports"}


def safe_segment(value: str, fallback: str) -> str:
    value = unicodedata.normalize("NFKC", value).strip()
    chars: list[str] = []
    for char in value:
        if char.isalnum() or char in {"-", "_"}:
            chars.append(char)
        else:
            chars.append("-")
    result = re.sub(r"-+", "-", "".join(chars)).strip("-_.")
    return result[:80] or fallback


def base_dir(value: str | None) -> Path:
    base = Path(value).expanduser() if value else Path.home() / ".sansan"
    return base.resolve()


def kind_dir(base: Path, kind: str) -> Path:
    return base / KINDS[kind]


def ensure_private_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path, 0o700)


def project_dir(base: Path, kind: str, project: str, create: bool = False) -> Path:
    root = kind_dir(base, kind)
    directory = root / safe_segment(project, "project")
    if create:
        ensure_private_dir(base)
        ensure_private_dir(root)
        if directory.is_symlink():
            raise SystemExit("项目目录不能是符号链接。")
        ensure_private_dir(directory)
    if directory.exists():
        root_resolved = root.resolve()
        directory_resolved = directory.resolve()
        if os.path.commonpath([str(root_resolved), str(directory_resolved)]) != str(root_resolved):
            raise SystemExit("项目目录越过本地记录根目录。")
    return directory


def parse_frontmatter(path: Path) -> dict[str, str]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}
    data: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"\'')
    return data


def files_for(base: Path, kind: str, project: str) -> list[Path]:
    directory = project_dir(base, kind, project)
    if not directory.exists() or directory.is_symlink():
        return []
    return sorted(directory.glob("*.md"), key=lambda path: path.name, reverse=True)


def file_row(path: Path, index: int) -> dict[str, object]:
    meta = parse_frontmatter(path)
    return {
        "index": index,
        "path": str(path),
        "filename": path.name,
        "timestamp": meta.get("timestamp", path.name[:15]),
        "title": meta.get("title", path.stem[16:]),
        "status": meta.get("status", "unknown"),
        "source_skill": meta.get("source_skill", ""),
    }


def write_private(path: Path, content: str) -> None:
    ensure_private_dir(path.parent)
    handle, temp_name = tempfile.mkstemp(prefix=".sansan-", suffix=".tmp", dir=path.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(content)
            if not content.endswith("\n"):
                stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temp_path, 0o600)
        os.replace(temp_path, path)
        os.chmod(path, 0o600)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def cmd_write(args: argparse.Namespace) -> int:
    base = base_dir(args.base)
    project = safe_segment(args.project, "project")
    title = safe_segment(args.title, args.kind)
    source = Path(args.content_file).expanduser()
    content = source.read_text(encoding="utf-8")
    if not content.strip():
        raise SystemExit("正文为空，拒绝写入。")

    directory = project_dir(base, args.kind, project, create=True)
    stamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    target = directory / f"{stamp}-{title}.md"
    if target.exists():
        target = directory / f"{stamp}-{title}-{secrets.token_hex(2)}.md"
    write_private(target, content)
    rows = files_for(base, args.kind, project)
    print(json.dumps({"path": str(target), "project": project, "count": len(rows)}, ensure_ascii=False))
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    base = base_dir(args.base)
    rows = [file_row(path, index) for index, path in enumerate(files_for(base, args.kind, args.project), 1)]
    print(json.dumps({"project": safe_segment(args.project, "project"), "count": len(rows), "items": rows}, ensure_ascii=False))
    return 0


def cmd_resolve(args: argparse.Namespace) -> int:
    base = base_dir(args.base)
    paths = files_for(base, "record", args.project)
    if not paths:
        print(json.dumps({"error": "not_found", "project": safe_segment(args.project, "project")}, ensure_ascii=False))
        return 2
    if args.selector == "latest":
        index = 0
    else:
        try:
            index = int(args.selector) - 1
        except ValueError:
            print(json.dumps({"error": "invalid_selector", "selector": args.selector}, ensure_ascii=False))
            return 2
        if index < 0 or index >= len(paths):
            print(json.dumps({"error": "out_of_range", "count": len(paths), "selector": args.selector}, ensure_ascii=False))
            return 2
    row = file_row(paths[index], index + 1)
    print(json.dumps(row, ensure_ascii=False))
    return 0


def cmd_projects(args: argparse.Namespace) -> int:
    root = kind_dir(base_dir(args.base), "record")
    rows: list[dict[str, str]] = []
    if root.exists():
        for directory in root.iterdir():
            if not directory.is_dir():
                continue
            paths = sorted(directory.glob("*.md"), key=lambda path: path.name, reverse=True)
            if paths:
                rows.append({"project": directory.name, "latest": paths[0].name[:15]})
    rows.sort(key=lambda item: item["latest"], reverse=True)
    print(json.dumps({"count": len(rows), "items": rows}, ensure_ascii=False))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    write = subparsers.add_parser("write")
    write.add_argument("--kind", choices=KINDS, required=True)
    write.add_argument("--project", required=True)
    write.add_argument("--title", required=True)
    write.add_argument("--content-file", required=True)
    write.add_argument("--base")
    write.set_defaults(func=cmd_write)

    listing = subparsers.add_parser("list")
    listing.add_argument("--kind", choices=KINDS, required=True)
    listing.add_argument("--project", required=True)
    listing.add_argument("--base")
    listing.set_defaults(func=cmd_list)

    resolve = subparsers.add_parser("resolve")
    resolve.add_argument("--project", required=True)
    resolve.add_argument("--selector", default="latest")
    resolve.add_argument("--base")
    resolve.set_defaults(func=cmd_resolve)

    projects = subparsers.add_parser("projects")
    projects.add_argument("--base")
    projects.set_defaults(func=cmd_projects)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
