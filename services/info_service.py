import logging
import os

import unidata_blocks
from character_encoding_utils import gb2312, big5, shiftjis, ksx1001

import configs
from configs import path_define
from utils import fs_util

logger = logging.getLogger('info-service')


def _get_unicode_char_count_infos(alphabet):
    count_map = {}
    for c in alphabet:
        code_point = ord(c)
        block = unidata_blocks.get_block_by_code_point(code_point)
        if not c.isprintable() and block.printable_count > 0:
            continue
        count = count_map.get(block.code_start, 0)
        count += 1
        count_map[block.code_start] = count
    code_starts = list(count_map.keys())
    code_starts.sort()
    return [(unidata_blocks.get_block_by_code_point(code_start), count_map[code_start]) for code_start in code_starts]


def _get_locale_char_count_map(alphabet, query_category_func):
    count_map = {}
    for c in alphabet:
        category = query_category_func(c)
        if category is not None:
            category_count = count_map.get(category, 0)
            category_count += 1
            count_map[category] = category_count
            total_count = count_map.get('total', 0)
            total_count += 1
            count_map['total'] = total_count
    return count_map


def _get_gb2312_char_count_infos(alphabet):
    count_map = _get_locale_char_count_map(alphabet, gb2312.query_category)
    return [
        ('一级汉字', count_map.get('level-1', 0), gb2312.get_level_1_count()),
        ('二级汉字', count_map.get('level-2', 0), gb2312.get_level_2_count()),
        ('其他字符', count_map.get('other', 0), gb2312.get_other_count()),
        ('总计', count_map.get('total', 0), gb2312.get_count()),
    ]


def _get_big5_char_count_infos(alphabet):
    count_map = _get_locale_char_count_map(alphabet, big5.query_category)
    return [
        ('常用汉字', count_map.get('level-1', 0), big5.get_level_1_count()),
        ('次常用汉字', count_map.get('level-2', 0), big5.get_level_2_count()),
        ('其他字符', count_map.get('other', 0), big5.get_other_count()),
        ('总计', count_map.get('total', 0), big5.get_count()),
    ]


def _get_shiftjis_char_count_infos(alphabet):
    count_map = _get_locale_char_count_map(alphabet, shiftjis.query_category)
    return [
        ('单字节-ASCII可打印字符', count_map.get('single-byte-ascii-printable', 0), shiftjis.get_single_byte_ascii_printable_count()),
        ('单字节-半角片假名', count_map.get('single-byte-half-width-katakana', 0), shiftjis.get_single_byte_half_width_katakana_count()),
        ('双字节-其他字符', count_map.get('double-byte-other', 0), shiftjis.get_double_byte_other_count()),
        ('双字节-汉字', count_map.get('double-byte-kanji', 0), shiftjis.get_double_byte_kanji_count()),
        ('总计', count_map.get('total', 0) - count_map.get('single-byte-ascii-control', 0), shiftjis.get_count() - shiftjis.get_single_byte_ascii_control_count()),
    ]


def _get_ksx1001_char_count_infos(alphabet):
    count_map = _get_locale_char_count_map(alphabet, ksx1001.query_category)
    return [
        ('谚文音节', count_map.get('syllable', 0), ksx1001.get_syllable_count()),
        ('汉字', count_map.get('hanja', 0), ksx1001.get_hanja_count()),
        ('其他字符', count_map.get('other', 0), ksx1001.get_other_count()),
        ('总计', count_map.get('total', 0), ksx1001.get_count()),
    ]


def _write_unicode_char_count_infos_table(file, infos):
    file.write('| 区块范围 | 区块名称 | 区块含义 | 完成数 | 缺失数 | 进度 |\n')
    file.write('|---|---|---|---:|---:|---:|\n')
    for block, count in infos:
        code_point_range = f'{block.code_start:04X} ~ {block.code_end:04X}'
        name = block.name
        name_zh_cn = block.name_localized('zh-cn') or ''
        total = block.printable_count
        lack = total - count if total > 0 else 0
        progress = count / total if total > 0 else 1
        finished_emoji = '🚩' if progress == 1 else '🚧'
        file.write(f'| {code_point_range} | {name} | {name_zh_cn} | {count} / {total} | {lack} | {progress:.2%} {finished_emoji} |\n')


def _write_locale_char_count_infos_table(file, infos):
    file.write('| 区块名称 | 完成数 | 缺失数 | 进度 |\n')
    file.write('|---|---:|---:|---:|\n')
    for name, count, total in infos:
        lack = total - count
        progress = count / total
        finished_emoji = '🚩' if progress == 1 else '🚧'
        file.write(f'| {name} | {count} / {total} | {lack} | {progress:.2%} {finished_emoji} |\n')


def _get_width_mode_display_name(width_mode):
    if width_mode == 'monospaced':
        return '等宽模式'
    else:  # proportional
        return '比例模式'


def make_info_file(font_config, width_mode, alphabet):
    fs_util.make_dirs_if_not_exists(path_define.outputs_dir)
    info_file_path = os.path.join(path_define.outputs_dir, font_config.get_info_file_name(width_mode))
    with open(info_file_path, 'w', encoding='utf-8') as file:
        file.write(f'# {configs.font_name} {font_config.px}px {_get_width_mode_display_name(width_mode)}\n')
        file.write('\n')
        file.write('## 基本信息\n')
        file.write('\n')
        file.write('| 属性 | 值 |\n')
        file.write('|---|---|\n')
        file.write(f'| 版本号 | {configs.font_version} |\n')
        file.write(f'| 行高 | {font_config.px if width_mode == "monospaced" else font_config.display_line_height_px}px |\n')
        file.write(f'| 字符总数 | {len(alphabet)} |\n')
        file.write('\n')
        file.write('## Unicode 字符分布\n')
        file.write('\n')
        _write_unicode_char_count_infos_table(file, _get_unicode_char_count_infos(alphabet))
        file.write('\n')
        file.write('## GB2312 字符分布\n')
        file.write('\n')
        file.write('简体中文参考字符集。统计范围不包含 ASCII。\n')
        file.write('\n')
        _write_locale_char_count_infos_table(file, _get_gb2312_char_count_infos(alphabet))
        file.write('\n')
        file.write('## Big5 字符分布\n')
        file.write('\n')
        file.write('繁体中文参考字符集。统计范围不包含 ASCII。\n')
        file.write('\n')
        _write_locale_char_count_infos_table(file, _get_big5_char_count_infos(alphabet))
        file.write('\n')
        file.write('## Shift-JIS 字符分布\n')
        file.write('\n')
        file.write('日语参考字符集。\n')
        file.write('\n')
        _write_locale_char_count_infos_table(file, _get_shiftjis_char_count_infos(alphabet))
        file.write('\n')
        file.write('## KS-X-1001 字符分布\n')
        file.write('\n')
        file.write('韩语参考字符集。统计范围不包含 ASCII。\n')
        file.write('\n')
        _write_locale_char_count_infos_table(file, _get_ksx1001_char_count_infos(alphabet))
    logger.info(f'make {info_file_path}')


def make_alphabet_txt_file(font_config, width_mode, alphabet):
    fs_util.make_dirs_if_not_exists(path_define.outputs_dir)
    txt_file_path = os.path.join(path_define.outputs_dir, font_config.get_alphabet_txt_file_name(width_mode))
    with open(txt_file_path, 'w', encoding='utf-8') as file:
        file.write(''.join(alphabet))
    logger.info(f'make {txt_file_path}')


def read_alphabet_txt_file(font_config, width_mode):
    txt_file_path = os.path.join(path_define.outputs_dir, font_config.get_alphabet_txt_file_name(width_mode))
    with open(txt_file_path, 'r', encoding='utf-8') as file:
        text = file.read()
    alphabet = list(text)
    alphabet.sort()
    return alphabet
