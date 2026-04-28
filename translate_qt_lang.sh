#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./translate_qt_lang.sh [src_lang] [target_lang]
# Example:
#   ./translate_qt_lang.sh en pt
#   ./translate_qt_lang.sh fr pt-BR
#
# This script:
# 1. extracts a Qt .qm translation file into a .ts file
# 2. leaves the .ts ready for translation with Qt Linguist or a text editor
# 3. compiles the resulting .ts back into a .qm file

ROOT="$(cd "$(dirname "$0")" && pwd)"
I18N_DIR="$ROOT/NTEGlobal/i18n"
SRC_LANG="${1:-en}"
TARGET_LANG="${2:-pt}"

SRC_QM="$I18N_DIR/lang_${SRC_LANG}.qm"
TARGET_TS="$I18N_DIR/lang_${TARGET_LANG}.ts"
TARGET_QM="$I18N_DIR/lang_${TARGET_LANG}.qm"

if [ ! -f "$SRC_QM" ]; then
  echo "Error: source QM not found: $SRC_QM"
  exit 1
fi

if ! command -v lconvert >/dev/null 2>&1; then
  echo "Error: lconvert is not installed. Install Qt tools (qttools5-dev-tools / qt5-tools)."
  exit 1
fi

if ! command -v lrelease >/dev/null 2>&1; then
  echo "Error: lrelease is not installed. Install Qt tools (qttools5-dev-tools / qt5-tools)."
  exit 1
fi

# Extract the source QM into TS
printf "Extracting %s -> %s\n" "$SRC_QM" "$TARGET_TS"
lconvert -i "$SRC_QM" -o "$TARGET_TS"

cat <<'EOF'

Extraction complete.
Next steps:
  1) Open "$TARGET_TS" with Qt Linguist (recommended) or a text editor.
  2) Translate the strings into Portuguese.
  3) Save the file and then run this script again to compile.

If you want to skip translation and just compile an existing translated TS, run:
  ./translate_qt_lang.sh "$SRC_LANG" "$TARGET_LANG"

EOF

# If the .ts file already contains translations, compile them.
if grep -q '<translation type="unfinished"/>\|<translation type="unfinished">' "$TARGET_TS"; then
  echo "TS file still has unfinished translations. Compile only after translation is complete."
  exit 0
fi

printf "Compiling %s -> %s\n" "$TARGET_TS" "$TARGET_QM"
lrelease "$TARGET_TS" -qm "$TARGET_QM"

printf "Done. Generated %s\n" "$TARGET_QM"
