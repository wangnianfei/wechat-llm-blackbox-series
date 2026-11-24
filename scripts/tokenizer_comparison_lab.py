#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tokenizer Comparison & Design Levers Lab (Questions 1, 2, 3, 4)
1. BPE vs. WordPiece vs. Unigram LM live training & score comparison
2. 243 Valid UTF-8 Bytes vs. 13 RFC-3629 Forbidden Bytes in ds13b
3. Vocabulary Size scaling (32k -> 256k): Embedding Parameter Share vs. Attention FLOPs
4. The 3 Levers of Tokenization: Merge Budget (Gate Cutoff), Corpus Mix, and Pre-tokenizer Rules
"""

import json
import csv
from pathlib import Path
from tokenizers import Tokenizer, models, trainers, pre_tokenizers

LAB_DIR = Path("/Users/wangnianfei/w2v_lab")
TOK_PATH = LAB_DIR / "ds13b" / "tokenizer.json"

def bytes_to_unicode():
    bs = (
        list(range(ord("!"), ord("~") + 1))
        + list(range(ord("¡"), ord("¬") + 1))
        + list(range(ord("®"), ord("ÿ") + 1))
    )
    cs = bs[:]
    n = 0
    for b in range(256):
        if b not in bs:
            bs.append(b)
            cs.append(256 + n)
            n += 1
    return {b: chr(c) for b, c in zip(bs, cs)}

def run_experiment():
    with open(TOK_PATH, "r", encoding="utf-8") as f:
        ds_tok = json.load(f)

    b2u = bytes_to_unicode()
    u2b = {v: k for k, v in b2u.items()}
    vocab = ds_tok["model"]["vocab"]
    merges = [tuple(m.split(" ")) if isinstance(m, str) else tuple(m) for m in ds_tok["model"]["merges"]]
    merge_rank = {pair: idx + 1 for idx, pair in enumerate(merges)}

    # =========================================================================
    # 1. Verify Question 3: 243 Valid UTF-8 Bytes vs 13 Illegal UTF-8 Bytes
    # =========================================================================
    print("=" * 72)
    print("[实验 1] 验证 243 个初始字节 vs. 13 个 UTF-8 禁用字节 (RFC 3629)")
    print("=" * 72)
    id2tok = {v: k for k, v in vocab.items()}
    init_bytes = sorted([u2b[id2tok[i]] for i in range(243)])
    missing_13 = [b for b in range(256) if b not in init_bytes]
    print(f"ds13b 初始词表 (ID 0..242) 字节数: {len(init_bytes)} 个")
    print(f"缺失并补在末尾 (ID 32000..32012) 的 13 个字节: {[f'0x{b:02X}' for b in missing_13]}")
    print("RFC 3629 UTF-8 标准解释:")
    print("  - 0xC0, 0xC1 (2个): 过长编码前缀 (Overlong 2-byte prefix)，UTF-8 严禁出现")
    print("  - 0xF5..0xF7 (3个): 超过 U+10FFFF 上限的 4 字节前缀，UTF-8 严禁出现")
    print("  - 0xF8..0xFD (6个): 废除的 5/6 字节前缀，UTF-8 严禁出现")
    print("  - 0xFE, 0xFF (2个): BOM 字节序标记，UTF-8 严禁出现")
    print("  => 结论: 任何合法的 UTF-8 文本最多只能出现 256 - 13 = 243 种字节！")

    # =========================================================================
    # 2. Question 1: BPE vs WordPiece vs Unigram Controlled Experiment
    # =========================================================================
    print("\n" + "=" * 72)
    print("[实验 2] 三大主流算法同场竞技：BPE vs. WordPiece vs. Unigram LM")
    print("=" * 72)

    # Construct a controlled corpus where functional words ('我','在','了','一','个','的','是','有')
    # appear across many sentences, while semantic words ('苹果','商店','公司','手机') co-occur tightly.
    corpus_sentences = (
        ["我在苹果商店吃了一个苹果"] * 12
        + ["我在商店买了一个苹果手机"] * 18
        + ["他在苹果公司工作了一年"] * 15
        + ["我有一个苹果和一部手机"] * 15
        + ["我在这里吃了一顿饭"] * 35
        + ["我在家里看了一本书"] * 35
        + ["我在学校上了一节课"] * 35
        + ["我是学生，我有很多书"] * 30
        + ["他在这里买了一个面包"] * 25
        + ["她在哪里看了一个电影"] * 25
    )

    # Calculate single-char counts and adjacent pair counts for exact BPE vs WordPiece math
    char_counts = {}
    pair_counts = {}
    for s in corpus_sentences:
        for ch in s:
            char_counts[ch] = char_counts.get(ch, 0) + 1
        for i in range(len(s) - 1):
            p = (s[i], s[i + 1])
            pair_counts[p] = pair_counts.get(p, 0) + 1

    focus_pairs = [
        ("我", "在", "高频虚词搭配"),
        ("了", "一", "高频虚词搭配"),
        ("一", "个", "高频量词搭配"),
        ("苹", "果", "紧密语义实体"),
        ("商", "店", "紧密语义实体"),
        ("手", "机", "紧密语义实体"),
        ("公", "司", "紧密语义实体"),
        ("苹", "果", "紧密语义实体"),
    ]
    seen = set()
    algo_rows = []
    # Rank all pairs in corpus by BPE count and by WordPiece likelihood score
    all_bpe_ranked = sorted(pair_counts.items(), key=lambda x: -x[1])
    all_wp_ranked = sorted(
        pair_counts.items(),
        key=lambda x: -(x[1] / (char_counts[x[0][0]] * char_counts[x[0][1]])),
    )
    bpe_rank_map = {k: i + 1 for i, (k, _) in enumerate(all_bpe_ranked)}
    wp_rank_map = {k: i + 1 for i, (k, _) in enumerate(all_wp_ranked)}

    print(f"{'词对':<6} | {'类型':<10} | {'Count(A)':<8} | {'Count(B)':<8} | {'共现Count(AB)':<12} | {'BPE排名':<7} | {'WordPiece互信息分':<16} | {'WP排名':<6}")
    print("-" * 92)
    for a, b, ptype in focus_pairs:
        if (a, b) in seen:
            continue
        seen.add((a, b))
        ca, cb, cab = char_counts[a], char_counts[b], pair_counts[(a, b)]
        wp_score = cab / (ca * cb)
        br = bpe_rank_map[(a, b)]
        wr = wp_rank_map[(a, b)]
        print(f"{a+b:<6} | {ptype:<10} | {ca:<8} | {cb:<8} | {cab:<13} | #{br:<6} | {wp_score:<16.5f} | #{wr:<6}")
        algo_rows.append({
            "pair": a + b,
            "pair_type": ptype,
            "count_a": ca,
            "count_b": cb,
            "cooccur_count": cab,
            "bpe_score": cab,
            "bpe_rank": br,
            "wp_score": round(wp_score * 1000, 4), # scaled x1000 for readable plotting
            "wp_rank": wr,
        })

    with open(LAB_DIR / "algo_comparison_results.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(algo_rows[0].keys()))
        writer.writeheader()
        writer.writerows(algo_rows)

    # Also compare the 3 algorithms with exact merge rules on the same 7-merge budget:
    # 1) BPE (Top-7 merges by raw count Count(AB))
    test_sent = "我在苹果商店吃了一个苹果"
    n_base_chars = len(char_counts)
    target_vocab = n_base_chars + 7  # allow exactly 7 multi-char words beyond base characters

    tok_bpe = Tokenizer(models.BPE())
    trainer_bpe = trainers.BpeTrainer(vocab_size=target_vocab, min_frequency=1)
    tok_bpe.train_from_iterator(corpus_sentences, trainer=trainer_bpe)

    # 2) True Google WordPiece (Top-7 merges by Mutual Information Count(AB)/[Count(A)*Count(B)], min_count >= 15)
    def run_true_wordpiece(sentences, test_s, num_merges=7, min_cooccur=15):
        seqs = [list(s) for s in sentences]
        t_seq = list(test_s)
        for _ in range(num_merges):
            c_tok = {}
            c_pair = {}
            for seq in seqs:
                for tok in seq:
                    c_tok[tok] = c_tok.get(tok, 0) + 1
                for i in range(len(seq) - 1):
                    p = (seq[i], seq[i + 1])
                    c_pair[p] = c_pair.get(p, 0) + 1
            best_p, best_score = None, -1.0
            for p, cab in c_pair.items():
                if cab < min_cooccur:
                    continue
                score = cab / (c_tok[p[0]] * c_tok[p[1]])
                if score > best_score:
                    best_score = score
                    best_p = p
            if best_p is None:
                break
            def apply_m(seq, pair):
                out, i = [], 0
                while i < len(seq):
                    if i < len(seq) - 1 and (seq[i], seq[i + 1]) == pair:
                        out.append(seq[i] + seq[i + 1])
                        i += 2
                    else:
                        out.append(seq[i])
                        i += 1
                return out
            seqs = [apply_m(seq, best_p) for seq in seqs]
            t_seq = apply_m(t_seq, best_p)
        return t_seq

    wp_tokens = run_true_wordpiece(corpus_sentences, test_sent, num_merges=7, min_cooccur=15)

    # 3) Unigram (Top-down probabilistic pruning)
    tok_uni = Tokenizer(models.Unigram())
    trainer_uni = trainers.UnigramTrainer(vocab_size=target_vocab + 1, unk_token="[UNK]", shrinking_factor=0.75)
    tok_uni.train_from_iterator(corpus_sentences, trainer=trainer_uni)

    print(f"\n[实测三种分词器在相同小词表预算 (基础单字={n_base_chars}, 仅给7个合成词名额) 下切分 '{test_sent}']:")
    print("  - BPE (自底向上·贪心频次优先)       :", tok_bpe.encode(test_sent).tokens)
    print("  - WordPiece (自底向上·互信息似然比) :", wp_tokens)
    print("  - Unigram (自顶向下·概率损失剪枝)   :", tok_uni.encode(test_sent).tokens)

    # Also test Corpus Content Shift (Tech/Code Corpus vs Shopping/Daily Corpus) with identical BPE & budget
    tech_corpus = ["我在苹果公司写代码"] * 30 + ["苹果公司的程序员吃了一个苹果"] * 20 + ["我在商店买了一个面包"] * 5
    shop_corpus = ["我在苹果商店买手机"] * 30 + ["苹果商店的顾客吃了一个苹果"] * 20 + ["我在公司写了一份报告"] * 5
    t_bpe_tech = Tokenizer(models.BPE())
    t_bpe_tech.train_from_iterator(tech_corpus, trainer=trainers.BpeTrainer(vocab_size=26, min_frequency=1))
    t_bpe_shop = Tokenizer(models.BPE())
    t_bpe_shop.train_from_iterator(shop_corpus, trainer=trainers.BpeTrainer(vocab_size=26, min_frequency=1))
    probe_sent = "我在苹果商店和苹果公司吃了一个苹果"
    print(f"\n[实测相同 BPE 算法 + 相同关门预算 (Vocab=26)，仅改变训练语料内容配比，切分 '{probe_sent}']:")
    print("  - 科技/编程语料训练出的 BPE :", t_bpe_tech.encode(probe_sent).tokens)
    print("  - 消费/日常语料训练出的 BPE :", t_bpe_shop.encode(probe_sent).tokens)

    # =========================================================================
    # 3. Question 2: Mainstream LLM Vocab Sizes & Compute/Memory Trade-off
    # =========================================================================
    print("\n" + "=" * 72)
    print("[实验 3] 词表大小不是固定 32000：算力、显存与序列长度的跷跷板效应")
    print("=" * 72)

    # Non-embedding body of ds13b (1.34647B total - 132.12M embed/lm_head = 1214.35M)
    body_1_3b = 1214.35e6
    d_1_3b = 2048
    # Non-embedding body of a 70B model (d=8192)
    body_70b = 68900.0e6
    d_70b = 8192

    vocab_sim_rows = []
    # Reference models at specific vocab sizes
    vocab_points = [
        (30522, "BERT-base (2018)", "WordPiece", 1.45),
        (32256, "DeepSeek-1.3B / LLaMA-2 (2023)", "Byte-BPE", 1.35),
        (50257, "GPT-2 / GPT-3 (2020)", "Byte-BPE", 1.25),
        (64000, "Baichuan-2 (2023)", "BPE", 1.05),
        (100256, "GPT-4 cl100k (2023)", "Byte-BPE", 0.95),
        (129280, "DeepSeek-V3 / R1 (2025)", "Byte-BPE", 0.78),
        (151936, "Qwen-2.5 (2024)", "Byte-BPE", 0.74),
        (200019, "GPT-4o o200k (2024)", "Byte-BPE", 0.70),
        (256000, "Gemma-2 / Gemma-3 (2025)", "SentencePiece BPE", 0.67),
    ]

    print(f"{'代表模型':<30} | {'词表大小 V':<10} | {'1.3B模型词表参数占比':<18} | {'70B模型词表参数占比':<17} | {'中文注意力算力相对开销'}")
    print("-" * 102)
    for v_size, m_name, algo, rel_seq_len in vocab_points:
        emb_params_1_3b = 2 * v_size * d_1_3b
        pct_1_3b = emb_params_1_3b / (body_1_3b + emb_params_1_3b) * 100.0

        emb_params_70b = 2 * v_size * d_70b
        pct_70b = emb_params_70b / (body_70b + emb_params_70b) * 100.0

        # Relative attention O(N^2) cost normalized to 32k vocab = 100%
        rel_attn_cost = (rel_seq_len / 1.35) ** 2 * 100.0
        print(f"{m_name:<30} | {v_size:<10,d} | {pct_1_3b:>16.2f}% | {pct_70b:>15.2f}% | {rel_attn_cost:>16.1f}%")
        vocab_sim_rows.append({
            "vocab_size": v_size,
            "model_name": m_name,
            "algorithm": algo,
            "emb_params_1_3b_M": round(emb_params_1_3b / 1e6, 1),
            "pct_1_3b": round(pct_1_3b, 2),
            "pct_70b": round(pct_70b, 2),
            "rel_zh_tokens_per_char": rel_seq_len,
            "rel_attention_flops_pct": round(rel_attn_cost, 1),
        })

    with open(LAB_DIR / "llm_vocab_landscape.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(vocab_sim_rows[0].keys()))
        writer.writeheader()
        writer.writerows(vocab_sim_rows)

    # =========================================================================
    # 4. Question 4: Gate-Closing Cutoff Simulation on real ds13b
    # =========================================================================
    print("\n" + "=" * 72)
    print("[实验 4] 关门设定（总合并轮次 K）对《我在苹果商店吃了一个苹果》的实测影响")
    print("=" * 72)

    def bpe_at_cutoff(text, max_rank):
        raw_bytes = text.encode("utf-8")
        seq = [b2u[b] for b in raw_bytes]
        while len(seq) >= 2:
            best_pair = None
            best_r = float("inf")
            for i in range(len(seq) - 1):
                p = (seq[i], seq[i + 1])
                r = merge_rank.get(p, float("inf"))
                if r <= max_rank and r < best_r:
                    best_r = r
                    best_pair = p
            if best_pair is None:
                break
            new_seq = []
            i = 0
            while i < len(seq):
                if i < len(seq) - 1 and (seq[i], seq[i + 1]) == best_pair:
                    new_seq.append(seq[i] + seq[i + 1])
                    i += 2
                else:
                    new_seq.append(seq[i])
                    i += 1
            seq = new_seq
        readable = []
        for tok in seq:
            b_arr = bytes([u2b[c] for c in tok])
            try:
                readable.append(b_arr.decode("utf-8"))
            except UnicodeDecodeError:
                readable.append("<0x" + b_arr.hex() + ">")
        return readable

    cutoffs = [
        (0, "243 (0轮合并：纯UTF-8字节)"),
        (1000, "1,243 (仅合出高频单字: 我/在/了/一/个)"),
        (3000, "3,243 (合出'一个'、'果'、'商'，生僻字仍碎裂)"),
        (6000, "6,243 (合出'店'、'吃'，仅剩'苹'未成型)"),
        (16800, "17,043 ('了一个'成型，'苹'刚拼好单字)"),
        (17000, "17,243 ('苹果'正式合体为1个词元)"),
        (31757, "32,000 ('我在'合体，但'商店'在关门前落选)"),
    ]

    cutoff_rows = []
    for max_r, desc in cutoffs:
        toks = bpe_at_cutoff(test_sent, max_r)
        joined = " | ".join(toks)
        print(f"关门轮次 K={max_r:<6,d} ({desc:<34}) -> [{len(toks):2d} 个token]: {joined}")
        cutoff_rows.append({
            "max_merge_rank": max_r,
            "vocab_size": max_r + 243,
            "stage_desc": desc,
            "token_count": len(toks),
            "segmentation": joined,
        })

    with open(LAB_DIR / "cutoff_and_corpus_effect.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(cutoff_rows[0].keys()))
        writer.writeheader()
        writer.writerows(cutoff_rows)

if __name__ == "__main__":
    run_experiment()
