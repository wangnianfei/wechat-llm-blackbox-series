#!/usr/bin/env Rscript
# Generate 300-DPI figures for Episodes 6, 7, and 9 of the WeChat popular science series
suppressPackageStartupMessages({
  library(ggplot2)
  library(patchwork)
  library(ragg)
  library(scales)
})

root <- "/Users/wangnianfei/w2v_lab"
data_dir <- file.path(root, "wechat_articles/data")
asset_dir <- file.path(root, "wechat_articles/assets")
dir.create(asset_dir, recursive = TRUE, showWarnings = FALSE)

base_font <- "PingFang SC"
theme_clean <- function() {
  theme_minimal(base_family = base_font, base_size = 11) +
    theme(
      plot.title = element_text(face = "bold", size = 12.2, color = "#0f172a", margin = margin(b = 4)),
      plot.subtitle = element_text(size = 9.5, color = "#475569", margin = margin(b = 10)),
      panel.grid.minor = element_blank(),
      panel.grid.major = element_line(color = "#e2e8f0", linewidth = 0.4),
      axis.title = element_text(face = "bold", size = 10, color = "#1e293b"),
      axis.text = element_text(size = 9.2, color = "#334155"),
      legend.position = "top",
      plot.margin = margin(10, 18, 10, 10)
    )
}

# ==============================================================================
# Figure 1 (Ep 06): 45-Token 2D Tensor Heatmap & Token L2 Norm Profile
# ==============================================================================
df45 <- read.csv(file.path(data_dir, "ep06_tensor_45_tokens.csv"), stringsAsFactors = FALSE)
df45$tok_label <- sprintf("%02d:%s", df45$pos, df45$token)
df45$tok_label <- factor(df45$tok_label, levels = rev(df45$tok_label))

df_heat <- rbind(
  data.frame(pos = df45$pos, tok_label = df45$tok_label, dim = "第1维 (d0)", val = df45$dim1),
  data.frame(pos = df45$pos, tok_label = df45$tok_label, dim = "第2维 (d1)", val = df45$dim2),
  data.frame(pos = df45$pos, tok_label = df45$tok_label, dim = "第3维 (d2)", val = df45$dim3),
  data.frame(pos = df45$pos, tok_label = df45$tok_label, dim = "第4维 (d3)", val = df45$dim4)
)

p6_a <- ggplot(df_heat[df_heat$pos <= 15, ], aes(x = dim, y = tok_label, fill = val)) +
  geom_tile(color = "white", linewidth = 0.6) +
  geom_text(aes(label = sprintf("%+.3f", val)), family = base_font, size = 3.1, fontface = "bold", color = "#0f172a") +
  scale_fill_gradient2(low = "#2563eb", mid = "#f8fafc", high = "#ea580c", midpoint = 0, name = "张量数值") +
  labs(
    title = "A. 二维张量 [45, 2048] 局部切片（前 15 词 × 前 4 维）",
    subtitle = "每行是 1 个 Token 的 2048 维向量；45 行叠成 [45, 2048] 矩阵面",
    x = "语义向量维度切片 (共 2048 列)", y = "句子中的 Token 位置 (共 45 行)"
  ) +
  theme_clean()

lbl_sub <- df45[df45$pos %in% c(1, 2, 4, 6, 9, 18, 21, 28, 35, 39, 44), ]
p6_b <- ggplot(df45, aes(x = pos, y = l2_norm)) +
  geom_area(fill = "#3b82f6", alpha = 0.14) +
  geom_line(color = "#1d4ed8", linewidth = 0.9) +
  geom_point(aes(color = l2_norm > 8.6), size = 2.4) +
  geom_text(
    data = lbl_sub,
    aes(label = token), family = base_font, vjust = -0.85, size = 3.1, fontface = "bold", color = "#0f172a"
  ) +
  scale_color_manual(values = c("FALSE" = "#2563eb", "TRUE" = "#dc2626"), guide = "none") +
  scale_x_continuous(breaks = seq(0, 45, 5), expand = expansion(mult = c(0.04, 0.05))) +
  scale_y_continuous(limits = c(7.4, 11.4), breaks = seq(7.5, 11.0, 0.5)) +
  labs(
    title = "B. 45 个 Token 沿序列轴 (Sequence Axis) 的向量模长分布",
    subtitle = "4 句话并行送入 GPU 时，4 张 [45, 2048] 平面叠成 [4, 45, 2048] 立方体",
    x = "Token 序列位置索引 (1 ~ 45)", y = "2048 维语义向量 L2 模长"
  ) +
  theme_clean()

fig6 <- p6_a + p6_b + plot_layout(widths = c(1.05, 1.15))
agg_png(file.path(asset_dir, "fig_ep06_tensor_stacking.png"), width = 3600, height = 1650, res = 300)
print(fig6)
dev.off()

# ==============================================================================
# Figure 2 (Ep 07): Geometric Angle & Dot Product (Random Orthogonal vs Trained Clusters)
# ==============================================================================
df7 <- read.csv(file.path(data_dir, "ep07_dot_product_geometry.csv"), stringsAsFactors = FALSE)
df7$pair <- factor(df7$pair, levels = rev(df7$pair))

df7_long <- rbind(
  data.frame(pair = df7$pair, stage = "训练前：随机初始化 (夹角 ≈ 90° 正交)", angle = df7$random_angle_deg, dot = df7$random_dot),
  data.frame(pair = df7$pair, stage = "训练后：DeepSeek 1.3B 真实语义空间", angle = df7$trained_angle_deg, dot = df7$trained_dot)
)

p7_a <- ggplot(df7_long, aes(x = angle, y = pair, color = stage)) +
  geom_vline(xintercept = 90, linetype = "dashed", color = "#94a3b8", linewidth = 0.7) +
  geom_segment(data = df7, aes(x = trained_angle_deg, xend = random_angle_deg, y = pair, yend = pair),
               inherit.aes = FALSE, color = "#cbd5e1", linewidth = 1.4) +
  geom_point(size = 3.8) +
  geom_text(data = df7, aes(x = trained_angle_deg - 4.2, y = pair, label = sprintf("%.1f°", trained_angle_deg)),
            inherit.aes = FALSE, family = base_font, size = 3.1, fontface = "bold", color = "#0f766e") +
  scale_color_manual(values = c("训练前：随机初始化 (夹角 ≈ 90° 正交)" = "#94a3b8",
                                "训练后：DeepSeek 1.3B 真实语义空间" = "#0d9488"), name = "") +
  scale_x_continuous(limits = c(48, 100), breaks = seq(50, 95, 10)) +
  labs(
    title = "A. 几何视角：训练如何让共现词向量的空间夹角 θ 缩小？",
    subtitle = "随机高维向量近乎垂直(90°)；训练后高频结伴词向彼此旋转靠拢",
    x = "2048 维空间中的几何夹角 θ (度，越小越靠近)", y = "测试词对"
  ) +
  theme_clean()

p7_b <- ggplot(df7, aes(x = trained_dot, y = pair, fill = note)) +
  geom_col(width = 0.62) +
  geom_text(aes(label = sprintf("点积 = %+.1f (cos=%.2f)", trained_dot, trained_cos)),
            hjust = -0.05, family = base_font, size = 3.05, fontface = "bold", color = "#0f172a") +
  scale_fill_manual(values = c(
    "同属水果语义簇" = "#0d9488", "科技巨头搭配簇" = "#2563eb", "数码产品语义簇" = "#3b82f6",
    "饮食动作高频共现" = "#f59e0b", "宠物名词高频共现" = "#10b981", "中国核心城市共现" = "#6366f1",
    "反义词共享修饰语境" = "#8b5cf6", "跨界无关词对" = "#94a3b8"
  ), name = "语境关系") +
  scale_x_continuous(limits = c(0, 62), breaks = seq(0, 50, 10)) +
  labs(
    title = "B. 数学视角：点积 (Dot Product = |a||b|cosθ) 实测得分",
    subtitle = "点积同时衡量长度与方向重合度，是注意力打分 Q·K 的核心算子",
    x = "DeepSeek 1.3B 真实向量点积得分 (a · b)", y = ""
  ) +
  theme_clean() +
  theme(legend.position = "right")

fig7 <- p7_a + p7_b + plot_layout(widths = c(1.05, 1.18))
agg_png(file.path(asset_dir, "fig_ep07_geometry_dot_product.png"), width = 3700, height = 1600, res = 300)
print(fig7)
dev.off()

# ==============================================================================
# Figure 3 (Ep 09): Multi-Head Attention Dissection ("我在苹果公司吃了一个苹果")
# ==============================================================================
df9 <- read.csv(file.path(data_dir, "ep09_all_384_heads.csv"), stringsAsFactors = FALSE)
df9_l1 <- df9[df9$layer == 1, ]

tok_cols <- c("apple2_to_wozai", "apple2_to_apple1", "apple2_to_gongsi", "apple2_to_chi", "apple2_to_leyige", "apple2_to_self")
tok_names <- c("① 我在", "② 苹果₁", "③ 公司", "④ 吃", "⑤ 了一个", "⑥ 苹果₂(自身)")

heat_l1 <- do.call(rbind, lapply(seq_along(tok_cols), function(i) {
  data.frame(
    head_lbl = factor(sprintf("Head %02d", df9_l1$head), levels = rev(sprintf("Head %02d", 1:16))),
    target_tok = factor(tok_names[i], levels = tok_names),
    weight = df9_l1[[tok_cols[i]]]
  )
}))

p9_a <- ggplot(heat_l1, aes(x = target_tok, y = head_lbl, fill = weight)) +
  geom_tile(color = "white", linewidth = 0.6) +
  geom_text(aes(label = sprintf("%.2f", weight), color = weight > 0.38),
            family = base_font, size = 3.0, fontface = "bold") +
  scale_fill_gradient(low = "#f8fafc", high = "#1d4ed8", name = "注意力权重") +
  scale_color_manual(values = c("FALSE" = "#1e293b", "TRUE" = "white"), guide = "none") +
  labs(
    title = "A. 第 1 层 16 个注意力头实测表：句末“苹果₂”在看谁？",
    subtitle = "Head 10 锁定动词“吃”(0.60)，Head 11 锁定“公司”(0.93)，Head 08 锁定“了一个”(0.41)",
    x = "前文被关注的 Token (Key 位置)", y = "第 1 层 16 个注意力头 (Query = 句末“苹果₂”)"
  ) +
  theme_clean()

layer_max <- aggregate(
  cbind(apple2_to_chi, gongsi_to_apple1, apple2_to_apple1) ~ layer,
  data = df9, FUN = max
)
layer_long <- rbind(
  data.frame(layer = layer_max$layer, role = "动宾锁定头：句末“苹果₂” → 动词“吃”", max_w = layer_max$apple2_to_chi),
  data.frame(layer = layer_max$layer, role = "专名修饰头：“公司” → 前文“苹果₁”", max_w = layer_max$gongsi_to_apple1),
  data.frame(layer = layer_max$layer, role = "同名比对头：句末“苹果₂” → 前文“苹果₁”", max_w = layer_max$apple2_to_apple1)
)

p9_b <- ggplot(layer_long, aes(x = layer, y = max_w, color = role)) +
  geom_line(linewidth = 1.0) +
  geom_point(size = 2.3) +
  scale_color_manual(values = c(
    "动宾锁定头：句末“苹果₂” → 动词“吃”" = "#dc2626",
    "专名修饰头：“公司” → 前文“苹果₁”" = "#2563eb",
    "同名比对头：句末“苹果₂” → 前文“苹果₁”" = "#0d9488"
  ), name = "") +
  scale_x_continuous(breaks = seq(1, 24, 2)) +
  scale_y_continuous(labels = percent_format(accuracy = 1), limits = c(0, 1.0)) +
  labs(
    title = "B. 1~24 层跨层追踪：三类语义头在各层的最高注意力强度",
    subtitle = "浅层(1~4层)完成动宾与同名比对；中层(7层)强化实体绑定；深层综合输出预测",
    x = "Transformer 层数 (Layer 1 ~ Layer 24)", y = "该层 16 个头中的最高注意力权重"
  ) +
  theme_clean() +
  theme(legend.direction = "vertical", legend.position = "top")

fig9 <- p9_a + p9_b + plot_layout(widths = c(1.15, 1.05))
agg_png(file.path(asset_dir, "fig_ep09_multihead_dissection.png"), width = 3700, height = 1750, res = 300)
print(fig9)
dev.off()

cat("[DONE] Re-rendered Ep06, Ep07, Ep09 figures cleanly\n")
