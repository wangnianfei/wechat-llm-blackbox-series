#!/usr/bin/env python3
"""深度解剖 DeepSeek (ds13b) 的 32,256 个 Token 词表与 BPE 合并树。

功能：
1. 解析 ds13b/tokenizer.json 的 vocab (32,000)、merges (31,757) 与 added_tokens (22)，
   并结合 pytorch_model.bin 的 embed_tokens.weight (32,256 x 2048)。
2. 导出完整词表 CSV: /Users/wangnianfei/w2v_lab/deepseek_vocab_full.csv
3. 统计词表结构、中文单字/多字词分布、BPE 合并族谱树（如「我在苹果商店吃了一个苹果」）。
4. 绘制 4 联高清教学图: /Users/wangnianfei/w2v_lab/deepseek_token_anatomy.png
"""
import csv
import json
import os
import re
import shutil
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

HERE = '/Users/wangnianfei/w2v_lab'
MODEL_DIR = os.path.join(HERE, 'ds13b')
CSV_OUT = os.path.join(HERE, 'deepseek_vocab_full.csv')
FIG_OUT = os.path.join(HERE, 'deepseek_token_anatomy.png')
ARTIFACT_FIG = '/Users/wangnianfei/.gemini/antigravity-cli/brain/7df9fa42-c6c1-4c6e-9579-7c305768922e/deepseek_token_anatomy.png'


def bytes_to_unicode():
    bs = (list(range(ord('!'), ord('~') + 1)) +
          list(range(ord('¡'), ord('¬') + 1)) +
          list(range(ord('®'), ord('ÿ') + 1)))
    cs = bs[:]
    n = 0
    for b in range(2**8):
        if b not in bs:
            bs.append(b)
            cs.append(2**8 + n)
            n += 1
    cs = [chr(n) for n in cs]
    return dict(zip(bs, cs))


B2U = bytes_to_unicode()
U2B = {v: k for k, v in B2U.items()}


def raw_to_bytes_and_text(raw, tid):
    if raw is None:
        return b'', '<UNUSED_GHOST_PAD>', False
    if tid >= 32013:
        b = raw.encode('utf-8')
        return b, raw, True
    try:
        b = bytes([U2B[c] for c in raw])
        txt = b.decode('utf-8')
        return b, txt, True
    except UnicodeDecodeError:
        b = bytes([U2B.get(c, 0) for c in raw])
        hex_str = ''.join(f'\\x{x:02x}' for x in b)
        return b, f'<bytes:{hex_str}>', False


def safe_csv_text(txt):
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in txt):
        return ''.join(
            f'\\x{ord(ch):02x}' if (ord(ch) < 32 or ord(ch) == 127) else ch
            for ch in txt
        )
    return txt


RE_CJK = re.compile(r'^[\u4e00-\u9fff]+$')
RE_CJK_ANY = re.compile(r'[\u4e00-\u9fff]')
RE_ASCII_ALPHA = re.compile(r'^[ ]?[A-Za-z]+$')
RE_CODE_IDENT = re.compile(r'^[ \t]*[A-Za-z_][A-Za-z0-9_]*$')
RE_WS = re.compile(r'^[ \t\r\n]+$')
RE_DIGIT = re.compile(r'^[0-9]+$')


def classify_token(tid, raw, txt, valid_utf8):
    if tid >= 32022:
        return '8_GPU对齐空位 (Ghost Pad)'
    if tid >= 32013:
        return '7_特殊控制符 (Special)'
    if tid <= 242 or (32000 <= tid <= 32012):
        if RE_DIGIT.match(txt):
            return '6_数字 (Digit)'
        return '1_基础单字节 (Base Byte)'
    if not valid_utf8:
        return '1_UTF8残片字节 (Sub-char Bytes)'
    stripped = txt.strip()
    if RE_WS.match(txt):
        return '5_缩进与空白 (Whitespace)'
    if RE_CJK.match(stripped) and len(stripped) == 1:
        return '3_中文单字 (CJK 1-char)'
    if RE_CJK.match(stripped) and len(stripped) >= 2:
        return '4_中文多字词组 (CJK Phrase)'
    if RE_CJK_ANY.search(txt):
        return '4_中文含标点/空格 (CJK Mixed)'
    if RE_ASCII_ALPHA.match(txt) or RE_CODE_IDENT.match(txt):
        return '2_英文与代码词根 (EN/Code Word)'
    return '5_代码符号与运算符 (Code/Punct)'


def main():
    with open(os.path.join(MODEL_DIR, 'tokenizer.json')) as f:
        tj = json.load(f)

    vocab = tj['model']['vocab']
    merges = tj['model']['merges']
    added = tj.get('added_tokens', [])

    id_to_raw = {v: k for k, v in vocab.items()}
    for a in added:
        id_to_raw[a['id']] = a['content']

    # Build merge map: merged_raw -> (rank, left_raw, right_raw)
    merge_map = {}
    for rank, m in enumerate(merges, 1):
        l, r = m.split(' ')
        merge_map[l + r] = (rank, l, r)

    # Load model embedding weights
    m = AutoModelForCausalLM.from_pretrained(
        MODEL_DIR, torch_dtype=torch.bfloat16, low_cpu_mem_usage=True)
    E = m.model.embed_tokens.weight.detach().float()
    norms = torch.norm(E, dim=1).numpy()
    vocab_size_cfg = E.shape[0]  # 32256

    rows = []
    cat_counts = {}
    cjk_phrases = []

    for tid in range(vocab_size_cfg):
        raw = id_to_raw.get(tid)
        b, txt, valid_utf8 = raw_to_bytes_and_text(raw, tid)
        cat = classify_token(tid, raw, txt, valid_utf8)
        cat_counts[cat] = cat_counts.get(cat, 0) + 1

        minfo = merge_map.get(raw) if raw else None
        if minfo:
            rank, l_raw, r_raw = minfo
            _, l_txt, _ = raw_to_bytes_and_text(l_raw, -1)
            _, r_txt, _ = raw_to_bytes_and_text(r_raw, -1)
            merge_Formula = f'{l_txt} + {r_txt}'
        else:
            rank, l_txt, r_txt, merge_Formula = '', '', '', ''

        char_len = len(txt) if valid_utf8 and tid < 32022 else 0
        byte_len = len(b)
        l2 = float(norms[tid])

        rows.append({
            'token_id': tid,
            'raw_bpe_token': safe_csv_text(raw) if raw is not None else '',
            'decoded_text': safe_csv_text(txt),
            'valid_utf8': int(valid_utf8),
            'char_len': char_len,
            'byte_len': byte_len,
            'category': cat,
            'merge_rank': rank,
            'merge_left': safe_csv_text(l_txt),
            'merge_right': safe_csv_text(r_txt),
            'merge_formula': safe_csv_text(merge_Formula),
            'embed_l2_norm': round(l2, 5),
        })

        if cat == '4_中文多字词组 (CJK Phrase)':
            cjk_phrases.append((tid, rank, txt.strip(), len(txt.strip()), l_txt, r_txt, l2))

    # Write CSV
    fieldnames = [
        'token_id', 'raw_bpe_token', 'decoded_text', 'valid_utf8',
        'char_len', 'byte_len', 'category', 'merge_rank',
        'merge_left', 'merge_right', 'merge_formula', 'embed_l2_norm'
    ]
    with open(CSV_OUT, 'w', newline='', encoding='utf-8-sig') as fo:
        wr = csv.DictWriter(fo, fieldnames=fieldnames)
        wr.writeheader()
        wr.writerows(rows)

    print(f'=== 已导出全量词表 CSV: {CSV_OUT} ({len(rows)} 行) ===')
    print('\n--- 1. 词表总体账本 ---')
    for k in sorted(cat_counts.keys()):
        print(f'  {k:34s}: {cat_counts[k]:6d} ({cat_counts[k]/32256*100:5.2f}%)')

    print(f'\n--- 2. 中文多字词组统计 (共 {len(cjk_phrases)} 个) ---')
    len_dist = {}
    for _, _, w, l, _, _, _ in cjk_phrases:
        len_dist[l] = len_dist.get(l, 0) + 1
    for l in sorted(len_dist.keys()):
        examples = [w for _, _, w, wl, _, _, _ in cjk_phrases if wl == l][:15]
        print(f'  {l}字词: {len_dist[l]:5d} 个 | 示例(按频率/合并顺序最靠前): {examples}')

    print('\n--- 3. 「我」「商」「店」「苹」「果」家族在词表中的真实分布 ---')
    for prefix in ['我', '商', '店', '苹', '果', '公']:
        fam = [r for r in rows if r['valid_utf8'] and r['decoded_text'].strip().startswith(prefix) and r['token_id'] < 32000]
        print(f'  以「{prefix}」开头的词元 ({len(fam)} 个):')
        for r in fam[:15]:
            print(f"    id={r['token_id']:5d} (merge #{str(r['merge_rank']):5s}) : {repr(r['decoded_text']):10s} <- {r['merge_formula']} (L2={r['embed_l2_norm']:.3f})")

    print('\n--- 4. Embedding L2 范数与 Token ID (频率排名) 的关系 ---')
    bins = [(0, 242, 'Base Bytes (0-242)'),
            (243, 2000, 'Top 极高频词 (243-2000)'),
            (2001, 10000, '高频词 (2001-10000)'),
            (10001, 20000, '中频词 (10001-20000)'),
            (20001, 31999, '低频长尾词 (20001-31999)'),
            (32013, 32021, '特殊控制符 (32013-32021)'),
            (32022, 32255, 'GPU对齐幽灵空位 (32022-32255)')]
    for lo, hi, label in bins:
        sub = norms[lo:hi+1]
        print(f'  {label:32s}: mean L2 = {sub.mean():.4f}, std = {sub.std():.4f}, min = {sub.min():.4f}, max = {sub.max():.4f}')

    # Trace BPE merge tree for any word
    def trace_tree(raw_tok, depth=0):
        _, txt, valid = raw_to_bytes_and_text(raw_tok, -1)
        tid = vocab.get(raw_tok, -1)
        minfo = merge_map.get(raw_tok)
        indent = '  ' * depth
        if not minfo:
            b = bytes([U2B[c] for c in raw_tok])
            print(f"{indent}└─ 原子字节 {repr(raw_tok)} (byte 0x{b.hex()}, id={tid})")
            return
        rank, l, r = minfo
        disp = txt if valid else f"UTF8局部字节({ b_hex(raw_tok) })"
        print(f"{indent}├─ [id={tid}, Merge #{rank}] {repr(disp)}")
        trace_tree(l, depth + 1)
        trace_tree(r, depth + 1)

    def b_hex(raw_tok):
        return ' '.join(f'0x{U2B[c]:02x}' for c in raw_tok)

    print('\n--- 5. 「我在」「苹果」「商」「店」的 BPE 字节级合并族谱树 ---')
    for target in ['我在', '苹果', '公司', '一个', '商', '店']:
        tid = AutoTokenizer.from_pretrained(MODEL_DIR).encode(target, add_special_tokens=False)[0]
        print(f'\n[词元: {target} (token_id={tid})]')
        trace_tree(id_to_raw[tid])


if __name__ == '__main__':
    main()
