#!/usr/bin/env Rscript
# 数据：本机 ds13b (deepseek-coder-1.3b-base) 实测导出的 bpe_sentence_replay.csv 与 bpe_growth_compression.csv；绘图代码为本次独立编写，采用 PlotCase 简洁风格与项目 Warm Editorial 配色。

suppressPackageStartupMessages({
  library(ggplot2)
  library(ragg)
  library(patchwork)
  library(scales)
})

replay_path <- "/Users/wangnianfei/w2v_lab/bpe_sentence_replay.csv"
curve_path  <- "/Users/wangnianfei/w2v_lab/bpe_growth_compression.csv"
fig_out     <- "/Users/wangnianfei/w2v_lab/bpe_merging_process.png"
art_out     <- "/Users/wangnianfei/.gemini/antigravity-cli/brain/7df9fa42-c6c1-4c6e-9579-7c305768922e/bpe_merging_process.png"

COL_WHITE <- "#FFFFFF"
COL_INK   <- "#1C1917"
COL_MUTED <- "#57534E"
COL_PINE  <- "#1B5E55"
COL_TERRA <- "#C2412D"
COL_OCHRE <- "#B07219"
COL_PLUM  <- "#6D4C67"
COL_STONE <- "#A8A29E"
FONT_FAM  <- "PingFang SC"

theme_ed <- function(base_size = 12.5) {
  theme_minimal(base_size = base_size, base_family = FONT_FAM) +
    theme(
      plot.background  = element_rect(fill = COL_WHITE, color = NA),
      panel.background = element_rect(fill = COL_WHITE, color = NA),
      panel.grid.major = element_line(color = "#EDE8DE", linewidth = 0.45),
      panel.grid.minor = element_blank(),
      axis.text        = element_text(color = COL_INK, size = base_size - 1),
      axis.title       = element_text(color = COL_INK, face = "bold", size = base_size),
      plot.title       = element_text(color = COL_INK, face = "bold", size = base_size + 2, margin = margin(b = 3)),
      plot.subtitle    = element_text(color = COL_MUTED, size = base_size - 1.5, margin = margin(b = 8)),
      plot.margin      = margin(10, 16, 10, 12)
    )
}

rep_df <- read.csv(replay_path, stringsAsFactors = FALSE)
rep_df$phase <- ifelse(rep_df$step == 0, "0_初始36个UTF-8字节",
  ifelse(rep_df$step %in% c(5, 7, 8, 10, 11, 14, 17, 18, 19, 21), "2_拼出完整汉字",
  ifelse(rep_df$step %in% c(13, 20, 22, 23), "3_字合体为多字词组", "1_两字节拼成UTF-8半字残片")))

phase_cols <- c(
  "0_初始36个UTF-8字节"      = COL_STONE,
  "1_两字节拼成UTF-8半字残片" = COL_OCHRE,
  "2_拼出完整汉字"           = COL_PINE,
  "3_字合体为多字词组"       = COL_TERRA
)

ann_steps <- data.frame(
  step       = c(0,    1,    5,    11,   13,   19,   20,   21,   22,   23),
  num_tokens = c(36,   34,   30,   24,   21,   13,   12,   10,   8,    7),
  lbl_x      = c(1.2,  4.2,  8.5,  7.2,  14.8, 13.5, 11.2, 22.8, 22.6, 18.8),
  lbl_y      = c(27.5, 37.8, 34.0, 17.5, 27.8, 10.8, 4.2,  18.5, 11.8, 2.2),
  lbl = c(
    "Step 0: 36个原始字节\n[e6][88][91]...[9c]",
    "Step 1 (Merge #56):\n0xe4+0xb8 合成「一/个」前两字节",
    "Step 5 (Merge #261):\n合出本句第1个汉字「一」",
    "Step 11 (Merge #606):\n合出「一/在/了/个/我」5个高频字",
    "Step 13 (Merge #1362):\n跨字合出「一个」(此时果/商/店/苹还没拼成字!)",
    "Step 19 (Merge #5190):\n合出「果」「商」「吃」「店」",
    "Step 20 (Merge #13314):\n合出3字词「了一个」(此时「苹」仍是字节残片!)",
    "Step 21 (Merge #16731):\n两个「苹」单字终于拼成!",
    "Step 22 (Merge #16902):\n仅隔171轮，苹+果 瞬间合为「苹果」",
    "Step 23 (Merge #22856):\n我+在 合为「我在」，终局定格为 7 个词元!"
  ),
  stringsAsFactors = FALSE
)

p1 <- ggplot(rep_df, aes(x = step, y = num_tokens)) +
  geom_area(fill = "#F5F2EB", alpha = 0.7) +
  geom_line(color = COL_INK, linewidth = 1.05) +
  geom_point(aes(color = phase), size = 3.6) +
  geom_segment(data = ann_steps,
               aes(x = lbl_x, y = lbl_y, xend = step, yend = num_tokens),
               color = COL_MUTED, linewidth = 0.6, linetype = "dotted") +
  geom_label(data = ann_steps,
             aes(x = lbl_x, y = lbl_y, label = lbl),
             family = FONT_FAM, size = 2.95, fontface = "bold", color = COL_INK,
             fill = alpha(COL_WHITE, 0.95), linewidth = 0.25, label.padding = unit(0.2, "lines")) +
  scale_color_manual(values = phase_cols, labels = c(
    "0_初始36个UTF-8字节"      = "初始字节 (36块)",
    "1_两字节拼成UTF-8半字残片" = "阶段①: 字节拼成半字残片",
    "2_拼出完整汉字"           = "阶段②: 第3字节补齐成汉字",
    "3_字合体为多字词组"       = "阶段③: 汉字跨界合为多字词组"
  )) +
  scale_x_continuous(limits = c(-0.5, 25.8), breaks = 0:23) +
  scale_y_continuous(limits = c(0, 41), breaks = seq(0, 36, 6)) +
  labs(
    title = "A. 微观慢动作回放：「我在苹果商店吃了一个苹果」从 36 个 UTF-8 字节坍缩为 7 个 Token 的全部 23 步",
    subtitle = "颠覆直觉的真相：不是“先拼完所有单字再拼词”——「一个」和「了一个」都已经合体了，「苹」居然还停留在 UTF-8 字节残片！",
    x = "本句触发的 BPE 合并步数 (Step 0 → Step 23，按 Merge Rank 从小到大依次执行)",
    y = "当前序列剩余词元 (Token) 块数"
  ) +
  theme_ed() +
  theme(legend.position = "top", legend.title = element_blank(),
        legend.text = element_text(size = 11, face = "bold", color = COL_INK))

# Panel B: Vocabulary Growth Compression Curve & Milestones
cur_df <- read.csv(curve_path, stringsAsFactors = FALSE)

ms_pts <- data.frame(
  vocab_size = c(243,  543,  1843, 5743,  10243, 17243, 23243, 32000),
  pct        = c(100,  83.3, 58.3, 36.1,  36.1,  22.2,  19.4,  19.4),
  lbl_x      = c(3200, 4800, 6200, 9500,  13500, 17800, 23200, 28800),
  lbl_y      = c(104,  88,   68,   50,    66,    44,    56,    35),
  lbl = c(
    "起点: 243个基础字节 (100%)\nMerge #1 合出双空格 '  '，#95 合出「的」",
    "词表 ~540 (Merge #300)\n高频单字「一/在/了」率先成型 (降至83%)",
    "词表 ~1,840 (Merge #1362)\n第1个中文双字词「一个」及 Python 'def' 诞生",
    "词表 ~5,740 (Merge #3856)\n本句11个汉字成型 + 第1个三字词「自己的」",
    "词表 ~10,240 (Merge #10909)\n第1个中文四字词「有限公司」诞生",
    "词表 ~17,240 (Merge #13314~16902)\n「了一个」「苹」「苹果」接连合体 (骤降至22%)",
    "词表 ~23,240 (Merge #22856)\n「我在」合体 (降至 19.4%)",
    "终点: 32,000 核心词表 (Merge #31757)\n36字节定格为7个Token (19.4%)，「商店」未进线"
  ),
  stringsAsFactors = FALSE
)

p2 <- ggplot(cur_df, aes(x = vocab_size, y = pct_of_bytes, color = label, group = label)) +
  geom_line(linewidth = 1.3) +
  geom_point(size = 2.6) +
  geom_segment(data = ms_pts,
               aes(x = lbl_x, y = lbl_y, xend = vocab_size, yend = pct),
               inherit.aes = FALSE, color = COL_TERRA, linewidth = 0.6, linetype = "dotted") +
  geom_point(data = ms_pts, aes(x = vocab_size, y = pct),
             inherit.aes = FALSE, color = COL_TERRA, size = 3.0) +
  geom_label(data = ms_pts,
             aes(x = lbl_x, y = lbl_y, label = lbl),
             inherit.aes = FALSE, family = FONT_FAM, size = 2.85, fontface = "bold",
             color = COL_INK, fill = alpha(COL_WHITE, 0.95), linewidth = 0.25, label.padding = unit(0.2, "lines")) +
  scale_color_manual(values = c(
    "中文日常句子 (36字节)" = COL_TERRA,
    "中文技术句子 (48字节)" = COL_PINE,
    "Python代码行 (44字节)" = COL_PLUM
  )) +
  scale_x_continuous(limits = c(0, 34500), labels = comma,
                     breaks = c(243, 5000, 10000, 15000, 20000, 25000, 32000)) +
  scale_y_continuous(limits = c(10, 112), labels = function(x) paste0(x, "%"), breaks = seq(20, 100, 20)) +
  labs(
    title = "B. 宏观生长史：DeepSeek 如何从 243 个基础字节通过 31,757 轮统计合并长成 32,000 词表",
    subtitle = "每一次合并都在压缩序列长度：随着词表长到 32,000，原本 36~48 字节的句子被压缩到仅需原长 19%~27% 的 Token 数",
    x = "词表规模生长过程 (从 243 个初始单字节 → 32,000 个 BPE 核心词元)",
    y = "分词后 Token 数占原始字节数比例 (越低压缩率越高)"
  ) +
  theme_ed() +
  theme(legend.position = "top", legend.title = element_blank(),
        legend.text = element_text(size = 11, face = "bold", color = COL_INK))

full_fig <- p1 / p2 +
  plot_layout(heights = c(1.08, 1)) +
  plot_annotation(
    title = "BPE 算法实测全回放：从 243 个原始字节到 32,000 个词元的“滚雪球造词法”",
    subtitle = "基于本机 /Users/wangnianfei/w2v_lab/ds13b/tokenizer.json 的 31,757 条真实合并规则逐帧回放",
    theme = theme(
      plot.title = element_text(family = FONT_FAM, face = "bold", size = 16.5, color = COL_INK, margin = margin(t = 6, b = 3)),
      plot.subtitle = element_text(family = FONT_FAM, size = 12, color = COL_MUTED, margin = margin(b = 6)),
      plot.background = element_rect(fill = COL_WHITE, color = NA)
    )
  )

ragg::agg_png(fig_out, width = 14.8, height = 11.5, units = "in", res = 300)
print(full_fig)
dev.off()

file.copy(fig_out, art_out, overwrite = TRUE)
cat("Saved:", fig_out, "and", art_out, "\n")
