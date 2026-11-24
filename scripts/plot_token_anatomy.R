#!/usr/bin/env Rscript
# 数据：本机 ds13b (deepseek-coder-1.3b-base) 导出的 deepseek_vocab_full.csv；绘图代码为本次独立编写，采用 PlotCase 简洁风格与项目 Warm Editorial 配色。

suppressPackageStartupMessages({
  library(ggplot2)
  library(ragg)
  library(patchwork)
  library(scales)
})

csv_path <- "/Users/wangnianfei/w2v_lab/deepseek_vocab_full.csv"
fig_out  <- "/Users/wangnianfei/w2v_lab/deepseek_token_anatomy.png"
art_out  <- "/Users/wangnianfei/.gemini/antigravity-cli/brain/7df9fa42-c6c1-4c6e-9579-7c305768922e/deepseek_token_anatomy.png"

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
      plot.margin      = margin(10, 14, 10, 10),
      legend.position  = "none"
    )
}

df <- read.csv(csv_path, stringsAsFactors = FALSE)

# Panel A: Vocabulary composition breakdown
cat_map <- c(
  "2_英文与代码词根 (EN/Code Word)"   = "英文与代码标识符",
  "5_代码符号与运算符 (Code/Punct)"    = "代码符号与标点组合",
  "4_中文多字词组 (CJK Phrase)"      = "中文多字词组 (2~4字)",
  "3_中文单字 (CJK 1-char)"         = "中文单字 (1字)",
  "1_UTF8残片字节 (Sub-char Bytes)" = "基础字节与UTF-8残片",
  "1_基础单字节 (Base Byte)"        = "基础字节与UTF-8残片",
  "8_GPU对齐空位 (Ghost Pad)"       = "GPU对齐幽灵空位 (未用)",
  "5_缩进与空白 (Whitespace)"        = "空白缩进 / 数字 / 控制符",
  "6_数字 (Digit)"                 = "空白缩进 / 数字 / 控制符",
  "7_特殊控制符 (Special)"           = "空白缩进 / 数字 / 控制符"
)
df$cat_clean <- cat_map[df$category]
cat_df <- as.data.frame(table(df$cat_clean), stringsAsFactors = FALSE)
names(cat_df) <- c("group", "count")
cat_df$pct <- cat_df$count / nrow(df) * 100
cat_df <- cat_df[order(cat_df$count), ]
cat_df$group <- factor(cat_df$group, levels = cat_df$group)
cat_df$label <- sprintf("%s (%s, %.1f%%)", format(cat_df$count, big.mark = ","),
  ifelse(cat_df$group == "GPU对齐幽灵空位 (未用)", "矩阵补齐", "词元"), cat_df$pct)
cat_df$col <- ifelse(grepl("中文", cat_df$group), COL_TERRA,
  ifelse(grepl("GPU", cat_df$group), COL_PLUM, COL_PINE))

pA <- ggplot(cat_df, aes(x = count, y = group, fill = col)) +
  geom_col(width = 0.68, alpha = 0.88) +
  geom_text(aes(label = label), hjust = -0.04, family = FONT_FAM, size = 3.7, fontface = "bold", color = COL_INK) +
  scale_fill_identity() +
  scale_x_continuous(limits = c(0, 31500), labels = comma) +
  labs(
    title = "A. DeepSeek-1.3B 词表总账 (矩阵共 32,256 行)",
    subtitle = "32,000 个 BPE 词元 + 22 个附加词元 + 234 个 GPU 64倍对齐幽灵行",
    x = "词元 (Token) 数量", y = NULL
  ) +
  theme_ed() +
  theme(panel.grid.major.y = element_blank(), axis.text.y = element_text(face = "bold"))

# Panel B: BPE Merge Rank Timeline
ms <- data.frame(
  rank = c(261, 366, 606, 1362, 1565, 2562, 2646, 5190, 6643, 12754, 15389, 16731, 16902, 21959, 22856, 30189, 34200),
  word = c("一 (id=503)", "在 (id=608)", "我 (id=848)", "一个 (id=1604)", "我们 (id=1807)",
           "公司 (id=2804)", "商 (id=2888)", "店 (id=5432)", "我的 (id=6885)", "商业 (id=12996)",
           "商品 (id=15631)", "苹 (id=16973)", "苹果 (id=17144)", "商务 (id=22201)", "我在 (id=23098)",
           "公安局 (id=30431)", "商店 (落选! 拆为 商+店)"),
  grp = c("单字", "单字", "单字", "高频词组", "高频词组", "高频词组", "单字", "单字", "高频词组",
          "商家族", "商家族", "苹果家族", "苹果家族", "商家族", "高频词组", "长尾词组", "门外落选"),
  stringsAsFactors = FALSE
)
ms$word <- factor(ms$word, levels = rev(ms$word))
ms$col <- c("单字" = COL_STONE, "高频词组" = COL_PINE, "商家族" = COL_OCHRE,
            "苹果家族" = COL_TERRA, "长尾词组" = COL_PLUM, "门外落选" = "#991B1B")[ms$grp]

pB <- ggplot(ms, aes(x = rank, y = word, color = col)) +
  geom_vline(xintercept = 31757, linetype = "dashed", color = COL_TERRA, linewidth = 0.9) +
  annotate("rect", xmin = 31757, xmax = 36500, ymin = 0.4, ymax = 17.6, fill = "#FEE2E2", alpha = 0.45) +
  geom_segment(aes(x = 0, xend = rank, y = word, yend = word), linewidth = 1.1, alpha = 0.65) +
  geom_point(size = 3.3) +
  geom_text(aes(label = ifelse(rank <= 31757, sprintf("Merge #%s", format(rank, big.mark = ",")), "未进前 31,757 名")),
            hjust = -0.12, family = FONT_FAM, size = 3.3, fontface = "bold") +
  annotate("text", x = 31400, y = 15.8, label = "词表关门线 (#31,757)\n预算耗尽，停止合并",
           color = COL_TERRA, family = FONT_FAM, fontface = "bold", size = 3.3, hjust = 1) +
  scale_color_identity() +
  scale_x_continuous(limits = c(0, 41500), breaks = c(0, 10000, 20000, 31757),
                     labels = c("0\n(最高频)", "10,000", "20,000", "31,757\n(截止)")) +
  labs(
    title = "B. BPE 合并顺位 = 语料共现频率排行榜",
    subtitle = "越靠左语料频次越高；「商业/商品/商务/我在」抢进词表，「商店」排在关门线外",
    x = "BPE 合并顺位 (Merge Rank = token_id - 242)", y = NULL
  ) +
  theme_ed() +
  theme(panel.grid.major.y = element_blank(), axis.text.y = element_text(face = "bold", size = 10.2))

# Panel C: Chinese token character length distribution
cjk_df <- data.frame(
  x_num = 1:4,
  len_label = factor(c("1字词元\n(单字)", "2字词元\n(双字搭配)", "3字词元\n(高频短语)", "4字词元\n(固定套语)"),
                     levels = c("1字词元\n(单字)", "2字词元\n(双字搭配)", "3字词元\n(高频短语)", "4字词元\n(固定套语)")),
  count = c(2134, 2398, 251, 19),
  lbl_y = c(1050, 1200, 1150, 620),
  examples = c(
    "的 / 一 / 是 / 在 / 我\n公 / 司 / 商 / 店 / 果",
    "一个 / 我们 / 可以 / 公司\n商业 / 商品 / 苹果 / 我在",
    "自己的 / 的时候 / 我们的\n为什么 / 消费者 / 公安局",
    "有限公司 / 的情况下\n人工智能 / 原文地址"
  ),
  col = c(COL_STONE, COL_PINE, COL_OCHRE, COL_TERRA),
  stringsAsFactors = FALSE
)

pC <- ggplot(cjk_df, aes(x = len_label, y = count, fill = col)) +
  geom_col(width = 0.54, alpha = 0.88) +
  geom_segment(data = cjk_df[3:4, ],
               aes(x = len_label, xend = len_label, y = count + 120, yend = lbl_y - 160),
               color = cjk_df$col[3:4], linetype = "dotted", linewidth = 0.8) +
  geom_text(aes(label = sprintf("%s 个", format(count, big.mark = ","))),
            vjust = -0.45, family = FONT_FAM, fontface = "bold", size = 4.0, color = COL_INK) +
  geom_label(aes(y = lbl_y, label = examples),
             fill = alpha(COL_WHITE, 0.94), color = COL_INK, family = FONT_FAM,
             size = 3.05, fontface = "bold", linewidth = 0.25, label.padding = unit(0.22, "lines")) +
  scale_fill_identity() +
  scale_y_continuous(limits = c(0, 2750), labels = comma) +
  labs(
    title = "C. 中文词元字数分布与代表词 (共 4,802 个纯中文词元)",
    subtitle = "2字词元数量超过单字！切分依据不是语法词典，而是语料高频共现搭配",
    x = NULL, y = "词元数量"
  ) +
  theme_ed() +
  theme(panel.grid.major.x = element_blank(), axis.text.x = element_text(face = "bold", size = 11))

# Panel D: Token ID vs Embedding L2 Norm (Frequency footprint in weights)
df$bin <- cut(df$token_id, breaks = seq(0, 32000, by = 1000), include.lowest = TRUE, labels = FALSE)
bin_df <- aggregate(embed_l2_norm ~ bin, data = df[df$token_id < 32000, ],
                    FUN = function(x) c(mean = mean(x), q25 = quantile(x, 0.25), q75 = quantile(x, 0.75)))
bin_stat <- data.frame(
  mid_id = (bin_df$bin - 0.5) * 1000,
  mean_l2 = bin_df$embed_l2_norm[, "mean"],
  q25 = bin_df$embed_l2_norm[, "q25.25%"],
  q75 = bin_df$embed_l2_norm[, "q75.75%"]
)

set.seed(42)
samp_idx <- sort(unique(c(
  sample(which(df$token_id < 32000), 1800),
  which(df$token_id >= 32022)
)))
samp_df <- df[samp_idx, ]
samp_df$pt_col <- ifelse(samp_df$token_id >= 32022, COL_PLUM,
  ifelse(samp_df$embed_l2_norm < 1.0, COL_OCHRE, COL_PINE))

hl_pts <- data.frame(
  token_id = c(848, 2888, 16973, 17144, 23098, 32140),
  l2 = c(9.879, 10.174, 4.416, 8.070, 7.935, 0.271),
  lbl = c("我 (id=848, L2=9.88)", "商 (id=2888, L2=10.17)",
          "苹 (id=16973, L2=4.42)\n刚合成就被「苹果」吞噬!",
          "苹果 (id=17144, L2=8.07)", "我在 (id=23098, L2=7.94)",
          "234个GPU对齐幽灵行\n(L2≈0.271, 停留在随机初始化)"),
  nudge_y = c(1.25, 1.45, -1.55, -1.25, 1.35, 1.75),
  nudge_x = c(1800, 2200, -2500, 1500, -1500, -5500),
  stringsAsFactors = FALSE
)

pD <- ggplot() +
  geom_point(data = samp_df, aes(x = token_id, y = embed_l2_norm, color = pt_col),
             alpha = 0.28, size = 1.1) +
  geom_ribbon(data = bin_stat, aes(x = mid_id, ymin = q25, ymax = q75),
              fill = COL_PINE, alpha = 0.22) +
  geom_line(data = bin_stat, aes(x = mid_id, y = mean_l2),
            color = COL_PINE, linewidth = 1.25) +
  geom_segment(data = hl_pts,
               aes(x = token_id + nudge_x * 0.7, y = l2 + nudge_y * 0.7, xend = token_id, yend = l2),
               color = COL_TERRA, linewidth = 0.65) +
  geom_point(data = hl_pts, aes(x = token_id, y = l2), color = COL_TERRA, size = 3.0) +
  geom_label(data = hl_pts, aes(x = token_id + nudge_x, y = l2 + nudge_y, label = lbl),
             family = FONT_FAM, size = 3.0, fontface = "bold", color = COL_INK,
             fill = alpha(COL_WHITE, 0.92), linewidth = 0.25, label.padding = unit(0.2, "lines")) +
  scale_color_identity() +
  scale_x_continuous(limits = c(0, 33500), labels = comma) +
  scale_y_continuous(limits = c(0, 13.5), breaks = seq(0, 12, 3)) +
  labs(
    title = "D. 神经网络权重里的“词频烙印”：Token ID vs 词向量 L2 范数",
    subtitle = "被长词吞噬的过渡词元(如「苹」)与末尾 234 个幽灵空位(L2≈0.27)在权重里清晰可辨",
    x = "Token ID (0 → 32,255，按 BPE 合并顺位递增)", y = "静态 Embedding 向量 L2 范数"
  ) +
  theme_ed()

full_fig <- (pA | pB) / (pC | pD) +
  plot_annotation(
    title = "DeepSeek-1.3B (ds13b) 词元 (Token) 深度解剖：词表账本、BPE 合并树与权重词频烙印",
    subtitle = "基于本机 /Users/wangnianfei/w2v_lab/ds13b 真实 tokenizer.json 与 pytorch_model.bin (32,256 × 2048) 实测绘制",
    theme = theme(
      plot.title = element_text(family = FONT_FAM, face = "bold", size = 17, color = COL_INK, margin = margin(t = 6, b = 4)),
      plot.subtitle = element_text(family = FONT_FAM, size = 12.5, color = COL_MUTED, margin = margin(b = 8)),
      plot.background = element_rect(fill = COL_WHITE, color = NA)
    )
  )

ragg::agg_png(fig_out, width = 15.5, height = 11.2, units = "in", res = 300)
print(full_fig)
dev.off()

dir.create(dirname(art_out), recursive = TRUE, showWarnings = FALSE)
file.copy(fig_out, art_out, overwrite = TRUE)
cat("Saved:", fig_out, "and", art_out, "\n")
