#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKILL_NAME="sansan-wechat-moments-coach"

python3 "$ROOT/tools/build-atom-library.py"
python3 "$ROOT/tools/build-skill-packs.py"
python3 "$ROOT/tools/validate-library.py"

VALIDATOR="${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py"
if [[ -f "$VALIDATOR" ]]; then
  if python3 -c "import yaml" >/dev/null 2>&1; then
    python3 "$VALIDATOR" "$ROOT/skills/$SKILL_NAME"
  else
    echo "提示：当前Python缺少PyYAML，已完成知识库校验，但跳过官方Skill结构校验。"
    echo "如需启用，请运行：python3 -m pip install PyYAML"
  fi
else
  echo "提示：未找到官方 quick_validate.py，已跳过 Skill 结构校验。"
fi

mkdir -p "$ROOT/dist"
rm -f "$ROOT/dist/$SKILL_NAME.zip"
(
  cd "$ROOT/skills"
  zip -qr "$ROOT/dist/$SKILL_NAME.zip" "$SKILL_NAME" -x "*/.DS_Store" "*/__pycache__/*"
)

echo "构建完成：$ROOT/dist/$SKILL_NAME.zip"
