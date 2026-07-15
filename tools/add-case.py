#!/usr/bin/env python3
"""Append a structured case skeleton to the selected Markdown source file."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "sources" / "朋友圈案例原文"
TYPE_FILES = {
    "反馈圈": "反馈圈模板与案例.md",
    "收款圈": "收款圈模板与案例.md",
    "咨询圈": "咨询圈模板与案例.md",
    "生活圈": "生活圈模板与案例.md",
    "认知圈": "认知圈模板与案例.md",
    "方法圈": "方法圈模板与案例.md",
    "发售圈": "发售圈模板与案例.md",
    "圈层背书圈": "圈层背书圈模板与案例.md",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="新增一条朋友圈案例模板")
    parser.add_argument("--type", required=True, choices=TYPE_FILES.keys())
    parser.add_argument("--title", required=True)
    args = parser.parse_args()

    path = SOURCE_DIR / TYPE_FILES[args.type]
    text = path.read_text(encoding="utf-8").rstrip()
    numbers = [int(n) for n in re.findall(r"^## 案例\s+(\d+)｜", text, re.M)]
    next_number = max(numbers, default=0) + 1
    skeleton = f"""

## 案例 {next_number:02d}｜{args.title}

### 案例类型

- 主类型：{args.type}
- 适用场景：待填写

### 使用者提供的案例事实

- 待填写

### 证据状态

- 待填写

### 原成品文案

待填写

### 可复用结构

1. 待填写

### 标题公式

- 待填写

### 这条文案有效的原因

- 待填写

### 风险与使用边界

- 待填写

### AI 生成时需要提取的变量

- 待填写
"""
    path.write_text(text + skeleton, encoding="utf-8")
    print(f"已追加案例 {next_number:02d}：{path}")
    print("请填写所有“待填写”内容，再运行 ./tools/build-release.sh。")


if __name__ == "__main__":
    main()

