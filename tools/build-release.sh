#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SKILL_NAMES=(
  "sansan"
  "sansan-update"
  "sansan-business-diagnosis"
  "sansan-good-question"
  "sansan-benchmark"
  "sansan-wechat-moments-coach"
  "sansan-save"
  "sansan-restore"
  "sansan-report"
)

python3 "$ROOT/tools/validate_skill_security.py"
python3 "$ROOT/tests/test_skill_security.py"
python3 "$ROOT/tools/build-atom-library.py"
python3 "$ROOT/tools/build-skill-packs.py"
python3 "$ROOT/tools/build-business-atoms.py"
python3 "$ROOT/tools/validate-library.py"
python3 "$ROOT/tools/validate-business-atoms.py"
python3 "$ROOT/tools/validate-skill-system.py"
python3 "$ROOT/tests/test_record_store.py"

VALIDATOR="${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py"
if [[ -f "$VALIDATOR" ]]; then
  if python3 -c "import yaml" >/dev/null 2>&1; then
    for skill_name in "${SKILL_NAMES[@]}"; do
      python3 "$VALIDATOR" "$ROOT/skills/$skill_name"
    done
  else
    echo "提示：当前Python缺少PyYAML，已完成知识库校验，但跳过官方Skill结构校验。"
    echo "如需启用，请运行：python3 -m pip install PyYAML"
  fi
else
  echo "提示：未找到官方 quick_validate.py，已跳过 Skill 结构校验。"
fi

mkdir -p "$ROOT/dist"
rm -f "$ROOT/dist/sansan-business-scan.zip"
rm -f "$ROOT/dist/sansan-business-router.zip"
for skill_name in "${SKILL_NAMES[@]}"; do
  rm -f "$ROOT/dist/$skill_name.zip"
  (
    cd "$ROOT/skills"
    zip -qr "$ROOT/dist/$skill_name.zip" "$skill_name" -x "*/.DS_Store" "*/__pycache__/*"
  )
done

rm -f "$ROOT/dist/sansan-ai-business-skill-system.zip"
(
  cd "$ROOT/skills"
  zip -qr "$ROOT/dist/sansan-ai-business-skill-system.zip" "${SKILL_NAMES[@]}" -x "*/.DS_Store" "*/__pycache__/*"
)

echo "构建完成：${#SKILL_NAMES[@]} 个独立Skill包 + 1个系统整包。"
