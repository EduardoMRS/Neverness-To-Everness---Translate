#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
PY="$ROOT/unpack_locale_pak.py"

usage() {
  cat <<'EOD'
Usage:
  ./translate_locale.sh extract <locale>
  ./translate_locale.sh pack <locale> [translation_file]
  ./translate_locale.sh list

Examples:
  ./translate_locale.sh extract pt-BR
  ./translate_locale.sh pack pt-BR
  ./translate_locale.sh pack pt-BR /path/to/translated_strings.txt

This script simplifies locale translation flow:
  - extract strings from a locale .pak
  - edit the generated strings_combined.txt
  - repack the locale using the same file
EOD
}

if [ $# -lt 1 ]; then
  usage
  exit 1
fi

case "$1" in
  list)
    python3 "$PY" list
    ;;
  extract)
    if [ $# -ne 2 ]; then
      usage
      exit 1
    fi
    python3 "$PY" extract "$2"
    ;;
  pack)
    if [ $# -eq 2 ]; then
      python3 "$PY" pack "$2"
    elif [ $# -eq 3 ]; then
      python3 "$PY" pack "$2" "$3"
    else
      usage
      exit 1
    fi
    ;;
  *)
    usage
    exit 1
    ;;
esac
