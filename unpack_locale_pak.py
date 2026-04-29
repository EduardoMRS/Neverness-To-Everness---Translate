#!/usr/bin/env python3
import argparse
import os
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOCALE_DIR = ROOT / 'NTEGlobal' / 'locales'
OUTPUT_DIR = ROOT / 'NTEGlobal' / 'locales_extracted'
MIN_STRING_LENGTH = 6


def list_locales():
    if not LOCALE_DIR.exists():
        raise FileNotFoundError(f'Locale directory not found: {LOCALE_DIR}')
    return sorted([p.name for p in LOCALE_DIR.glob('*.pak')])


def run_strings_tool(pak_path, utf16=False):
    if not shutil.which('strings'):
        return None
    cmd = ['strings', '-a', '-n', str(MIN_STRING_LENGTH)]
    if utf16:
        cmd.extend(['-e', 'l'])
    cmd.append(str(pak_path))
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.splitlines()
    except subprocess.CalledProcessError:
        return None


def is_candidate_string(s: str, min_len: int = MIN_STRING_LENGTH) -> bool:
    if len(s.strip()) < min_len:
        return False
    if not re.search(r'[A-Za-zÀ-ÖØ-öø-ÿ0-9]', s):
        return False
    if re.fullmatch(r'[^A-Za-zÀ-ÖØ-öø-ÿ0-9]+', s):
        return False
    if s.strip().startswith('<') and s.strip().endswith('>'):
        return False
    return True


def extract_strings_from_bytes(data, min_len=MIN_STRING_LENGTH):
    printable = set()
    current = []
    for byte in data:
        if 32 <= byte <= 126:
            current.append(chr(byte))
        else:
            if current:
                s = ''.join(current)
                if is_candidate_string(s, min_len=min_len):
                    printable.add(s)
            current = []
    if current:
        s = ''.join(current)
        if is_candidate_string(s, min_len=min_len):
            printable.add(s)
    return sorted(printable)


def extract_utf16le_strings(data, min_len=MIN_STRING_LENGTH):
    printable = set()
    cur = []
    for i in range(0, len(data) - 1, 2):
        lo = data[i]
        hi = data[i + 1]
        if hi == 0 and 32 <= lo <= 126:
            cur.append(chr(lo))
        else:
            if cur:
                s = ''.join(cur)
                if is_candidate_string(s, min_len=min_len):
                    printable.add(s)
            cur = []
    if cur:
        s = ''.join(cur)
        if is_candidate_string(s, min_len=min_len):
            printable.add(s)
    return sorted(printable)


def extract_locale(pak_name, output_dir=None, force=False):
    pak_path = LOCALE_DIR / pak_name
    if not pak_path.exists():
        raise FileNotFoundError(f'Locale package not found: {pak_path}')
    output_dir = Path(output_dir or OUTPUT_DIR / pak_name.replace('.pak', ''))
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f'Extracting locale strings from {pak_path} -> {output_dir}')

    utf8_strings = run_strings_tool(pak_path, utf16=False)
    utf16_strings = run_strings_tool(pak_path, utf16=True)

    if utf8_strings is None or utf16_strings is None:
        print('Warning: `strings` utility not available or failed. Falling back to internal extraction.')
        data = pak_path.read_bytes()
        utf8_strings = extract_strings_from_bytes(data)
        utf16_strings = extract_utf16le_strings(data)
    else:
        utf8_strings = [line for line in utf8_strings if len(line.strip()) >= MIN_STRING_LENGTH]
        utf16_strings = [line for line in utf16_strings if len(line.strip()) >= MIN_STRING_LENGTH]

    utf8_out = output_dir / 'strings.txt'
    utf16_out = output_dir / 'strings_utf16le.txt'
    combined_out = output_dir / 'strings_combined.txt'

    utf8_unique = sorted(dict.fromkeys(utf8_strings))
    utf16_unique = sorted(dict.fromkeys(utf16_strings))
    combined = sorted(dict.fromkeys(utf8_unique + utf16_unique))

    utf8_out.write_text('\n'.join(utf8_unique), encoding='utf-8')
    utf16_out.write_text('\n'.join(utf16_unique), encoding='utf-8')
    combined_out.write_text('\n'.join(combined), encoding='utf-8')

    print(f'Wrote {len(utf8_unique)} UTF-8 strings, {len(utf16_unique)} UTF-16LE strings, {len(combined)} total unique strings.')
    return combined_out


def compare_locales(base_locale, target_locale, output_dir=None):
    base_file = OUTPUT_DIR / base_locale.replace('.pak', '') / 'strings_combined.txt'
    target_file = OUTPUT_DIR / target_locale.replace('.pak', '') / 'strings_combined.txt'
    if not base_file.exists() or not target_file.exists():
        raise FileNotFoundError('You must extract both locales first using the extract command.')
    base = set(line.strip() for line in base_file.read_text(encoding='utf-8').splitlines() if line.strip())
    target = set(line.strip() for line in target_file.read_text(encoding='utf-8').splitlines() if line.strip())
    missing = sorted(base - target)
    extra = sorted(target - base)
    print(f'Base locale: {base_locale} ({len(base)} strings)')
    print(f'Target locale: {target_locale} ({len(target)} strings)')
    print(f'Missing in {target_locale}: {len(missing)}')
    print(f'Extra in {target_locale}: {len(extra)}')
    if missing:
        out_dir = Path(output_dir or OUTPUT_DIR)
        out_dir.mkdir(parents=True, exist_ok=True)
        diff_file = out_dir / f'missing_{target_locale.replace(".pak","")}_vs_{base_locale.replace(".pak","")}.txt'
        diff_file.write_text('\n'.join(missing), encoding='utf-8')
        print(f'Wrote missing strings to {diff_file}')
    if extra:
        out_dir = Path(output_dir or OUTPUT_DIR)
        diff_file = out_dir / f'extra_{target_locale.replace(".pak","")}_vs_{base_locale.replace(".pak","")}.txt'
        diff_file.write_text('\n'.join(extra), encoding='utf-8')
        print(f'Wrote extra strings to {diff_file}')


def load_text_lines(file_path):
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f'Translation file not found: {path}')
    return [line.rstrip('\r\n') for line in path.read_text(encoding='utf-8').splitlines()]


def pack_locale(pak_name, translation_file, output_pak=None, dry_run=False):
    pak_path = LOCALE_DIR / pak_name
    if not pak_path.exists():
        raise FileNotFoundError(f'Locale package not found: {pak_path}')

    base_extracted = OUTPUT_DIR / pak_name.replace('.pak', '') / 'strings_combined.txt'
    if not base_extracted.exists():
        raise FileNotFoundError(
            'Base extracted strings not found. Run the extract command first for the source locale.'
        )

    original_lines = load_text_lines(base_extracted)
    translated_lines = load_text_lines(translation_file)
    if len(original_lines) != len(translated_lines):
        raise ValueError(
            'Translation file must have the same number of lines as the extracted strings_combined.txt file.'
        )

    replacements = []
    for source, target in zip(original_lines, translated_lines):
        if source == target:
            continue
        source_bytes = source.encode('utf-8')
        target_bytes = target.encode('utf-8')
        if len(target_bytes) > len(source_bytes):
            raise ValueError(
                f'Translation longer than original for string {source!r}. '
                'Keep translated bytes equal or shorter than the original string.'
            )
        replacements.append((source, source_bytes, target_bytes))

    if not replacements:
        print('No translated strings found. Nothing to pack.')
        return

    replacements.sort(key=lambda item: len(item[1]), reverse=True)
    data = pak_path.read_bytes()
    stats = []

    for source, source_bytes, target_bytes in replacements:
        utf16_source = source.encode('utf-16le')
        utf16_target = target.encode('utf-16le')
        replaced = False

        if source_bytes in data:
            count = data.count(source_bytes)
            pad = target_bytes + b'\x00' * (len(source_bytes) - len(target_bytes))
            if not dry_run:
                data = data.replace(source_bytes, pad)
            stats.append((source, count, 'utf-8'))
            replaced = True

        if utf16_source in data:
            if len(utf16_target) > len(utf16_source):
                raise ValueError(
                    f'UTF-16LE translation longer than original for string {source!r}.'
                )
            count = data.count(utf16_source)
            pad = utf16_target + b'\x00' * (len(utf16_source) - len(utf16_target))
            if not dry_run:
                data = data.replace(utf16_source, pad)
            stats.append((source, count, 'utf-16le'))
            replaced = True

        if not replaced:
            print(f'Warning: original string not found in pak: {source!r}')

    if dry_run:
        print('Dry-run complete. No pak file written.')
        for source, count, encoding in stats:
            print(f'  Replaced {count} occurrence(s) of {encoding} string: {source!r}')
        return

    output_path = Path(output_pak) if output_pak else pak_path.parent / f'{pak_name.replace(".pak","")}_packed.pak'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(data)
    print(f'Packed locale file written to {output_path}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract and compare locale pak files from NTEGlobal/locales.')
    sub = parser.add_subparsers(dest='command', required=True)

    parser_list = sub.add_parser('list', help='List available locale pak files.')

    parser_extract = sub.add_parser('extract', help='Extract strings from a locale pak file.')
    parser_extract.add_argument('locale', help='Locale pak name or code (e.g. pt-BR or pt-BR.pak).')
    parser_extract.add_argument('--output', help='Output directory for extracted files.')

    parser_compare = sub.add_parser('compare', help='Compare two extracted locale packs.')
    parser_compare.add_argument('base', help='Base locale pak name or code (e.g. en-US or en-US.pak).')
    parser_compare.add_argument('target', help='Target locale pak name or code (e.g. pt-BR or pt-BR.pak).')
    parser_compare.add_argument('--output', help='Directory to write diff files.')

    parser_pack = sub.add_parser('pack', help='Pack a translated strings file back into a locale pak file.')
    parser_pack.add_argument('locale', help='Source locale pak name or code (e.g. en-US or en-US.pak).')
    parser_pack.add_argument('translation', help='Translated strings file with the same line order as extracted strings_combined.txt.')
    parser_pack.add_argument('--output', help='Output pak path for the packed locale file.')
    parser_pack.add_argument('--dry-run', action='store_true', help='Report replacements without writing the output file.')

    args = parser.parse_args()

    if args.command == 'list':
        for locale in list_locales():
            print(locale)
    elif args.command == 'extract':
        locale_name = args.locale if args.locale.endswith('.pak') else f'{args.locale}.pak'
        extract_locale(locale_name, output_dir=args.output)
    elif args.command == 'compare':
        base_name = args.base if args.base.endswith('.pak') else f'{args.base}.pak'
        target_name = args.target if args.target.endswith('.pak') else f'{args.target}.pak'
        compare_locales(base_name, target_name, output_dir=args.output)
    elif args.command == 'pack':
        locale_name = args.locale if args.locale.endswith('.pak') else f'{args.locale}.pak'
        pack_locale(locale_name, args.translation, output_pak=args.output, dry_run=args.dry_run)
