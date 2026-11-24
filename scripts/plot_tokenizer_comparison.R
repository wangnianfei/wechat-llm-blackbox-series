#!/usr/bin/env Rscript
suppressPackageStartupMessages({
  library(ggplot2)
  library(ragg)
  library(patchwork)
  library(scales)
})

algo_df <- read.csv("/Users/wangnianfei/w2v_lab/algo_comparison_results.csv", stringsAsFactors = FALSE)
vocab_df <- read.csv("/Users/wangnianfei/w2v_lab/llm_vocab_landscape.csv", stringsAsFactors = FALSE)

font_family <- "PingFang SC"

base_theme <- theme_minimal(base_family = font_family, base_size = 11) +
  theme(
    plot.background = element_rect(fill = "#FBF8F3", color = NA),
    panel.background = element_rect(fill = "#FBF8F3", color = NA),
    panel.grid.major = element_line(color = "#E6DEC8", linewidth = 0.4),
    panel.grid.minor = element_blank(),
    plot.title = element_text(face = "bold", size = 13, color = "#1F1F1F", margin = margin(b = 4)),
    plot.subtitle = element_text(size = 9.5, color = "#5A534A", margin = margin(b = 10)),
    axis.title = element_text(face = "bold", size = 10, color = "#333333"),
    axis.text = element_text(size = 9.2, color = "#333333"),
    legend.position = "top"
  )

# Panel A: BPE Raw Frequency vs WordPiece Mutual Information Score
algo_long <- rbind(
  data.frame(
    pair = algo_df$pair,
    pair_type = algo_df$pair_type,
    metric = "BPE 合并指标：共现绝对频次 Count(A,B)",
    val = algo_df$bpe_score,
    rank_label = paste0("#", algo_df$bpe_rank, " (", algo_df$bpe_score, "次)")
  ),
  data.frame(
    pair = algo_df$pair,
    pair_type = algo_df$pair_type,
    metric = "WordPiece 合并指标：互信息分 Count(AB)/[Count(A)Count(B)] ×1000",
    val = algo_df$wp_score,
    rank_label = paste0("#", algo_df$wp_rank, " (", sprintf("%.1f", algo_df$wp_score), ")")
  )
)
algo_long$pair <- factor(algo_long$pair, levels = rev(c("我在", "了一", "一个", "苹果", "商店", "手机", "公司")))

p1 <- ggplot(algo_long, aes(x = val, y = pair, fill = pair_type)) +
  geom_col(width = 0.62, alpha = 0.92) +
  geom_text(aes(label = rank_label), hjust = -0.08, family = font_family, size = 3.1, fontface = "bold", color = "#2B2B2B") +
  facet_wrap(~metric, scales = "free_x", ncol = 2) +
  scale_fill_manual(
    name = "词对性质：",
    values = c("高频虚词搭配" = "#D55E00", "高频量词搭配" = "#E69F00", "紧密语义实体" = "#0072B2")
  ) +
  scale_x_continuous(expand = expansion(mult = c(0, 0.30))) +
  labs(
    title = "A. 算法流派之争：为什么 BPE 优先合并“我在/了一”，而 WordPiece 优先合并“苹果/商店”？",
    subtitle = "BPE 只看共现绝对次数（高频单字占尽便宜）；WordPiece 除以单字频次乘积，优先合并“彼此唯一绑定”的实体词",
    x = "算法合并评分（数值越高越优先合并）",
    y = "候选相邻字对"
  ) +
  base_theme +
  theme(
    strip.text = element_text(face = "bold", size = 10, color = "#1F1F1F"),
    legend.margin = margin(b = -4)
  )

# Panel B: Vocabulary Size Trade-off (Embedding Parameter Share vs Attention FLOPs)
vocab_df$short_label <- c(
  "BERT (30.5k)",
  "ds13b / LLaMA-2 (32.3k)",
  "GPT-2/3 (50.3k)",
  "Baichuan-2 (64k)",
  "GPT-4 (100.3k)",
  "DeepSeek-V3/R1 (129.3k)",
  "Qwen-2.5 (151.9k)",
  "GPT-4o (200k)",
  "Gemma-2/3 (256k)"
)
vocab_df$lbl_y <- vocab_df$pct_1_3b + c(-6.2, 6.8, -6.5, 6.8, -6.8, -7.2, 6.8, 6.8, 6.8)
vocab_df$lbl_x <- vocab_df$vocab_size / 1000 + c(-1, 3, 1, 2, -1, -2, 2, 0, -4)

p2 <- ggplot(vocab_df, aes(x = vocab_size / 1000)) +
  geom_line(aes(y = pct_1_3b, color = "1.3B 小模型词表参数占比 (%) [如 ds13b]"), linewidth = 1.2) +
  geom_point(aes(y = pct_1_3b, color = "1.3B 小模型词表参数占比 (%) [如 ds13b]"), size = 2.8) +
  geom_line(aes(y = pct_70b, color = "70B 大模型词表参数占比 (%)"), linewidth = 1.1, linetype = "dashed") +
  geom_point(aes(y = pct_70b, color = "70B 大模型词表参数占比 (%)"), size = 2.4) +
  geom_line(aes(y = rel_attention_flops_pct, color = "中文自注意力 O(N²) 相对算力开销 (%)"), linewidth = 1.2) +
  geom_point(aes(y = rel_attention_flops_pct, color = "中文自注意力 O(N²) 相对算力开销 (%)"), size = 2.8) +
  geom_text(
    aes(x = lbl_x, y = lbl_y, label = short_label),
    family = font_family, size = 2.85, fontface = "bold", color = "#2B2B2B"
  ) +
  scale_color_manual(
    name = "算力与参数跷跷板指标：",
    values = c(
      "1.3B 小模型词表参数占比 (%) [如 ds13b]" = "#C0392B",
      "70B 大模型词表参数占比 (%)" = "#7F8C8D",
      "中文自注意力 O(N²) 相对算力开销 (%)" = "#0072B2"
    )
  ) +
  scale_x_continuous(breaks = seq(30, 260, by = 30), limits = c(18, 272), labels = function(x) paste0(x, "k")) +
  scale_y_continuous(limits = c(0, 122), breaks = seq(0, 120, by = 20), labels = function(y) paste0(y, "%")) +
  labs(
    title = "B. 词表规模的算力跷跷板：为什么小模型守着 32k，而现代大模型（DeepSeek-V3/Qwen/GPT-4o）扩充到 128k~256k？",
    subtitle = "词表越大 -> 句子切出的 token 越少，注意力 O(N²) 推理算力大幅下降（蓝线↓）；但小模型装大词表会被 Embedding 矩阵吃掉近半参数（红线↑）",
    x = "词表总规模 Vocab Size（千个 Token）",
    y = "参数占比 / 相对注意力算力百分比 (%)"
  ) +
  base_theme +
  theme(legend.margin = margin(b = -4))

combined <- (p1 / p2) +
  plot_layout(heights = c(1.0, 1.12)) +
  plot_annotation(
    title = "大模型分词器（Tokenizer）设计全景：算法流派、词表容量与关门铁律",
    subtitle = "基于本地 DeepSeek-Coder-1.3B (ds13b) 权重结构与 HuggingFace Tokenizers 实测对比",
    caption = "数据：ds13b/tokenizer.json 实测与主流开源模型公开参数；绘图代码为本次独立编写，采用 PlotCase 简洁风格。",
    theme = theme(
      plot.background = element_rect(fill = "#FBF8F3", color = NA),
      plot.title = element_text(family = font_family, face = "bold", size = 15, color = "#1F1F1F"),
      plot.subtitle = element_text(family = font_family, size = 10.5, color = "#5A534A"),
      plot.caption = element_text(family = font_family, size = 8.5, color = "#7A7267", hjust = 0)
    )
  )

out_png <- "/Users/wangnianfei/w2v_lab/tokenizer_design_tradeoffs.png"
agg_png(out_png, width = 12.8, height = 9.6, units = "in", res = 300)
print(combined)
invisible(dev.off())
cat("Saved plot to:", out_png, "\n")
