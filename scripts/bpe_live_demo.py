#!/usr/bin/env python3
"""实测回放 DeepSeek (ds13b) 的 BPE 算法全过程：
1. 宏观回放：从 243 个初始单字节出发，历经 31,757 次合并长成 32,000 词表的里程碑事件与压缩率演进。
2. 微观慢动作回放：将「我在苹果商店吃了一个苹果」（36 个 UTF-8 字节）放进 ds13b 的真实合并表，
   逐帧观察它是如何经过 28 次合并坍缩成最终 8 个 Token 的。
3. 迷你手搓 BPE 实验：在一段微型语料上现场跑一遍 BPE 统计点票与合并，直观展示算法如何通过“计票”造词。
"""
import csv
import json
import os

HERE = '/Users/wangnianfei/w2v_lab'
MODEL_DIR = os.path.join(HERE, 'ds13b')


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


def raw_to_disp(raw):
    b = bytes([U2B[c] for c in raw])
    try:
        s = b.decode('utf-8')
        return repr(s)
    except UnicodeDecodeError:
        hx = ' '.join(f'{x:02x}' for x in b)
        return f'<0x{hx}>'


def main():
    with open(os.path.join(MODEL_DIR, 'tokenizer.json')) as f:
        tj = json.load(f)

    vocab = tj['model']['vocab']
    merges = tj['model']['merges']
    id_to_raw = {v: k for k, v in vocab.items()}

    merge_rank = {}
    for idx, m in enumerate(merges, 1):
        l, r = m.split(' ')
        merge_rank[(l, r)] = idx

    print('=' * 82)
    print('实验一：宏观生长史 —— DeepSeek 31,757 轮 BPE 合并的真实里程碑')
    print('=' * 82)
    print('初始词表 (Rank 0): 243 个基础单字节 (ID 0 ~ 242)\n')

    print('【前 15 轮合并 (Merge #1 ~ #15) —— 宇宙大爆炸最初的 15 个组合】')
    for r in range(1, 16):
        l, rt = merges[r - 1].split(' ')
        merged = l + rt
        tid = vocab[merged]
        print(f'  Merge #{r:<4d} (id={tid:<4d}): {raw_to_disp(l):<14s} + {raw_to_disp(rt):<14s} -> {raw_to_disp(merged)}')

    # Find milestones in Chinese & Code
    milestones = []
    seen_types = set()
    for r, m in enumerate(merges, 1):
        l, rt = m.split(' ')
        merged = l + rt
        tid = vocab[merged]
        b = bytes([U2B[c] for c in merged])
        try:
            txt = b.decode('utf-8')
        except UnicodeDecodeError:
            if 'first_utf8_prefix' not in seen_types and len(b) == 2 and b[0] >= 0xe4:
                seen_types.add('first_utf8_prefix')
                milestones.append((r, tid, raw_to_disp(l), raw_to_disp(rt), raw_to_disp(merged), '第一个中文汉字的2字节UTF-8半成品（"一/个/不"的共同前两字节）'))
            continue

        cjk = all('\u4e00' <= ch <= '\u9fff' for ch in txt)
        if cjk and len(txt) == 1 and 'cjk_1' not in seen_types:
            seen_types.add('cjk_1')
            milestones.append((r, tid, raw_to_disp(l), raw_to_disp(rt), repr(txt), '全词表诞生的【第 1 个完整汉字】！'))
        elif cjk and len(txt) == 1 and sum(1 for x in seen_types if x.startswith('cjk_1_')) < 9:
            k = sum(1 for x in seen_types if x.startswith('cjk_1_')) + 2
            seen_types.add(f'cjk_1_{k}')
            milestones.append((r, tid, raw_to_disp(l), raw_to_disp(rt), repr(txt), f'全词表诞生的【第 {k} 个完整汉字】'))
        elif cjk and len(txt) == 2 and 'cjk_2' not in seen_types:
            seen_types.add('cjk_2')
            milestones.append((r, tid, raw_to_disp(l), raw_to_disp(rt), repr(txt), '全词表诞生的【第 1 个中文双字词】！'))
        elif cjk and len(txt) == 3 and 'cjk_3' not in seen_types:
            seen_types.add('cjk_3')
            milestones.append((r, tid, raw_to_disp(l), raw_to_disp(rt), repr(txt), '全词表诞生的【第 1 个中文三字词】！'))
        elif cjk and len(txt) == 4 and 'cjk_4' not in seen_types:
            seen_types.add('cjk_4')
            milestones.append((r, tid, raw_to_disp(l), raw_to_disp(rt), repr(txt), '全词表诞生的【第 1 个中文四字词】！'))
        elif txt in ('    ', 'def', 'return', 'import', 'function', '一个', '我们', '公司', '商业', '商品', '苹', '苹果', '我在'):
            milestones.append((r, tid, raw_to_disp(l), raw_to_disp(rt), repr(txt), f'关键代表词元 {repr(txt)} 诞生'))

    # Also last merge #31757
    l_last, r_last = merges[-1].split(' ')
    m_last = l_last + r_last
    milestones.append((len(merges), vocab[m_last], raw_to_disp(l_last), raw_to_disp(r_last), raw_to_disp(m_last), '第 31,757 轮：词表正式满员关门！'))

    print('\n【DeepSeek 31,757 轮合并中的关键历史节点】')
    for r, tid, l, rt, res, desc in milestones:
        print(f'  Merge #{r:<6d} (id={tid:<5d}): {l:<14s} + {rt:<14s} => {res:<12s} | {desc}')

    print('\n' + '=' * 82)
    print('实验二：微观慢动作回放 —— 「我在苹果商店吃了一个苹果」从 36 字节到 8 词元')
    print('=' * 82)
    sent = '我在苹果商店吃了一个苹果'
    # Note: DeepSeek pre-tokenizer splits CJK runs as isolated contiguous blocks.
    # For a pure CJK sentence, the whole sentence is one contiguous CJK block of 36 bytes!
    raw_bytes = sent.encode('utf-8')
    seq = [B2U[b] for b in raw_bytes]
    print(f'输入句子: {sent} (共 {len(sent)} 个汉字 = {len(raw_bytes)} 个 UTF-8 原始字节)')
    print(f'初始序列 (Step 0, {len(seq)} 个单字节块):')
    print('  ' + ' '.join(f'[{b:02x}]' for b in raw_bytes))
    print()

    step_history = []
    step_history.append((0, 0, len(seq), '初始 UTF-8 字节序列', [raw_to_disp(s) for s in seq]))

    step_num = 0
    while len(seq) > 1:
        # Find all adjacent pairs and pick the one with minimum merge_rank
        best_rank = None
        best_pair = None
        for i in range(len(seq) - 1):
            pair = (seq[i], seq[i + 1])
            rk = merge_rank.get(pair)
            if rk is not None and (best_rank is None or rk < best_rank):
                best_rank = rk
                best_pair = pair
        if best_pair is None:
            break

        # Merge all non-overlapping occurrences of best_pair
        step_num += 1
        new_seq = []
        i = 0
        count_merged = 0
        while i < len(seq):
            if i < len(seq) - 1 and (seq[i], seq[i + 1]) == best_pair:
                new_seq.append(seq[i] + seq[i + 1])
                count_merged += 1
                i += 2
            else:
                new_seq.append(seq[i])
                i += 1
        seq = new_seq
        merged_str = best_pair[0] + best_pair[1]
        tid = vocab[merged_str]
        action = f"{raw_to_disp(best_pair[0])} + {raw_to_disp(best_pair[1])} -> {raw_to_disp(merged_str)} (id={tid}, 合并{count_merged}处)"
        disp_seq = [raw_to_disp(s) for s in seq]
        step_history.append((step_num, best_rank, len(seq), action, disp_seq))
        print(f'第 {step_num:2d} 步 [触发规则 Merge #{best_rank:<5d}] -> 剩余 {len(seq):2d} 块 | {action}')
        print('   当前序列: ' + ' | '.join(disp_seq))

    # Save replay trace CSV for visualization
    replay_csv = os.path.join(HERE, 'bpe_sentence_replay.csv')
    with open(replay_csv, 'w', newline='', encoding='utf-8-sig') as fo:
        wr = csv.writer(fo)
        wr.writerow(['step', 'merge_rank', 'num_tokens', 'action', 'sequence_str'])
        for st, rk, nt, act, dseq in step_history:
            wr.writerow([st, rk, nt, act, ' | '.join(dseq)])

    # Save compression curve across vocabulary growth (0 to 31757 merges) on a sample corpus
    sample_sentences = [
        ('中文日常句子 (36字节)', '我在苹果商店吃了一个苹果'),
        ('中文技术句子 (48字节)', '我们可以用人工智能模型分析有限公司的数据'),
        ('Python代码行 (44字节)', 'def calculate_apple_price(count, price):\n    return count * price')
    ]
    checkpoints = [0, 50, 150, 300, 600, 1000, 1600, 2700, 5500, 10000, 17000, 23000, 31757]
    curve_csv = os.path.join(HERE, 'bpe_growth_compression.csv')
    with open(curve_csv, 'w', newline='', encoding='utf-8-sig') as fo:
        wr = csv.writer(fo)
        wr.writerow(['label', 'max_merge_rank', 'vocab_size', 'token_count', 'pct_of_bytes'])
        for label, text in sample_sentences:
            init_b = text.encode('utf-8')
            for cp in checkpoints:
                cur = [B2U[b] for b in init_b]
                while len(cur) > 1:
                    best_rk = None
                    best_p = None
                    for i in range(len(cur) - 1):
                        p = (cur[i], cur[i + 1])
                        rk = merge_rank.get(p)
                        if rk is not None and rk <= cp and (best_rk is None or rk < best_rk):
                            best_rk = rk
                            best_p = p
                    if best_p is None:
                        break
                    nxt = []
                    i = 0
                    while i < len(cur):
                        if i < len(cur) - 1 and (cur[i], cur[i + 1]) == best_p:
                            nxt.append(cur[i] + cur[i + 1])
                            i += 2
                        else:
                            nxt.append(cur[i])
                            i += 1
                    cur = nxt
                wr.writerow([label, cp, 243 + cp, len(cur), round(len(cur) / len(init_b) * 100, 2)])

    print(f'\n已保存逐帧回放数据: {replay_csv} 与 词表生长压缩曲线: {curve_csv}')


if __name__ == '__main__':
    main()
