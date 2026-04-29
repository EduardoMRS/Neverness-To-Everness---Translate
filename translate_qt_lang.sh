#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   ./translate_qt_lang.sh [src_lang] [target_lang]
#   ./translate_qt_lang.sh check [target_lang]
# Example:
#   ./translate_qt_lang.sh en pt
#   ./translate_qt_lang.sh fr pt-BR
#   ./translate_qt_lang.sh check pt
#
# This script:
# 1. extracts a Qt .qm translation file into a .ts file (when needed)
# 2. checks the target .ts file for unfinished or untranslated strings
# 3. compiles the resulting .ts back into a .qm file

ROOT="$(cd "$(dirname "$0")" && pwd)"
I18N_DIR="$ROOT/NTEGlobal/i18n"

usage() {
  cat <<'EOD'
Usage:
  ./translate_qt_lang.sh [src_lang] [target_lang]
  ./translate_qt_lang.sh check [target_lang]

Examples:
  ./translate_qt_lang.sh en pt
  ./translate_qt_lang.sh fr pt-BR
  ./translate_qt_lang.sh check pt

This script:
  - extracts a Qt .qm translation file into a .ts file (if the TS does not already exist)
  - checks the target .ts file for unfinished or untranslated strings
  - compiles completed .ts files into .qm files

The check mode helps find:
  - unfinished translations
  - identical source/translation pairs
  - likely remaining English text in translations
EOD
}

check_ts_file() {
  local ts_file="$1"

  if [ ! -f "$ts_file" ]; then
    echo "Error: target TS not found: $ts_file"
    return 1
  fi

  python3 - "$ts_file" <<'PY'
import re
import sys
import pathlib
import xml.etree.ElementTree as ET

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding='utf-8')
root = ET.fromstring(text)

allowed_identical = {
    'Avatar', 'DD', 'MM', 'YYYY', 'Apple', 'Steam', 'Google', 'UID:'
}
common_phrases = [
    'Please open directory', 'Recommended version', 'Current Frequency',
    'Verification failed', 'Enter email address', 'Save changes?',
    'Settings have been modified', 'Browser', 'Speed limit applies',
    'This account is already linked', 'Email linked', 'Remember me',
    "Don't save passwords",
    'Switching servers may improve speed', 'Select your age',
    'This will not be shown publicly',
    'Outdated drivers may cause stability issues',
    'Your %1 graphics driver is below the recommended version',
    'Verification code sent to:', 'Ignore', 'Current Frequency',
    'Settings have been modified. Save changes?'
]
common_words = [
    'please', 'install', 'update', 'upgrade', 'client',
    'server', 'login', 'logout', 'password', 'email', 'account', 'user',
    'error', 'fail', 'failed', 'retry', 'cancel', 'continue', 'ok', 'yes',
    'save', 'open', 'browser', 'prompt', 'verify', 'verification',
    'success', 'support', 'help', 'select', 'setting',
    'language', 'network', 'connection', 'status', 'installing',
    'processing', 'pause', 'resume', 'play', 'next', 'back', 'exit',
    'close', 'minimize', 'maximize', 'restore', 'switch', 'version',
    'frequency', 'speed', 'limit', 'if', 'this', 'will', 'not', 'be', 'has'
]
ignore_words = {
    'login', 'game', 'steam', 'discord', 'google', 'store', 'play',
    'data', 'feedback', 'download', 'upload', 'log', 'server', 'client',
    'status'
}
phrase_pattern = re.compile(r"(" + "|".join(re.escape(p) for p in common_phrases) + ")", re.IGNORECASE)
word_pattern = re.compile(r"\b(?:" + "|".join(re.escape(w) for w in common_words) + r")\b", re.IGNORECASE)

fatal_warnings = []
english_warnings = []

for context in root.findall('context'):
    for message in context.findall('message'):
        source_element = message.find('source')
        source = ''.join(source_element.itertext() or []).strip() if source_element is not None else ''
        translation_element = message.find('translation')
        if translation_element is None:
            continue
        text = ''.join(translation_element.itertext() or []).strip()
        ttype = translation_element.get('type', '')

        if ttype == 'unfinished':
            fatal_warnings.append(('unfinished', source, text))
        elif text == '':
            fatal_warnings.append(('empty', source, text))
        elif source and text == source and source not in allowed_identical:
            fatal_warnings.append(('identical', source, text))
        else:
            matches = [m.group(0).lower() for m in word_pattern.finditer(text) if m.group(0).lower() not in ignore_words]
            if phrase_pattern.search(text) or len(matches) >= 2:
                english_warnings.append((source, text))

print(f"Checked: {path.name}")
print(f"  Unfinished/empty/identical entries: {len(fatal_warnings)}")
print(f"  Suspicious English-related translations: {len(english_warnings)}")

if fatal_warnings:
    print('\nFatal warnings:')
    for kind, source, text in fatal_warnings[:50]:
        print(f"  - {kind}: source={source!r}, translation={text!r}")
    if len(fatal_warnings) > 50:
        print(f"  ... and {len(fatal_warnings) - 50} more entries")

if english_warnings:
    print('\nSuspicious English text in translations:')
    for source, text in english_warnings[:50]:
        print(f"  - source={source!r}, translation={text!r}")
    if len(english_warnings) > 50:
        print(f"  ... and {len(english_warnings) - 50} more entries")

if fatal_warnings:
    sys.exit(1)
sys.exit(0)
PY
}

if [ $# -eq 0 ]; then
  usage
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "Error: python3 is required for TS checking."
  exit 1
fi

if [ "$1" = "check" ] || [ "$1" = "--check" ]; then
  TARGET_LANG="${2:-pt}"
  TARGET_TS="$I18N_DIR/lang_${TARGET_LANG}.ts"
  check_ts_file "$TARGET_TS"
  exit $?
fi

SRC_LANG="${1:-en}"
TARGET_LANG="${2:-pt}"

SRC_QM="$I18N_DIR/lang_${SRC_LANG}.qm"
TARGET_TS="$I18N_DIR/lang_${TARGET_LANG}.ts"
TARGET_QM="$I18N_DIR/lang_${TARGET_LANG}.qm"

if ! command -v lconvert >/dev/null 2>&1; then
  echo "Error: lconvert is not installed. Install Qt tools (qttools5-dev-tools / qt5-tools)."
  exit 1
fi

if ! command -v lrelease >/dev/null 2>&1; then
  echo "Error: lrelease is not installed. Install Qt tools (qttools5-dev-tools / qt5-tools)."
  exit 1
fi

if [ -f "$SRC_QM" ] && [ ! -f "$TARGET_TS" ]; then
  printf "Extracting %s -> %s\n" "$SRC_QM" "$TARGET_TS"
  lconvert -i "$SRC_QM" -o "$TARGET_TS"
  cat <<'EOD'

Extraction complete.
Next steps:
  1) Open "$TARGET_TS" with Qt Linguist (recommended) or a text editor.
  2) Translate the strings into Portuguese.
  3) Save the file and then run this script again to compile.

If you want to skip translation and just compile an existing translated TS, run:
  ./translate_qt_lang.sh "$SRC_LANG" "$TARGET_LANG"

EOD
fi

if [ ! -f "$TARGET_TS" ]; then
  echo "Error: neither source QM nor target TS was available."
  echo "       Place a translated TS at $TARGET_TS or provide an existing source QM file."
  exit 1
fi

check_ts_file "$TARGET_TS"

printf "Compiling %s -> %s\n" "$TARGET_TS" "$TARGET_QM"
lrelease "$TARGET_TS" -qm "$TARGET_QM"

printf "Done. Generated %s\n" "$TARGET_QM"
