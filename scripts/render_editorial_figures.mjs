#!/usr/bin/env node
/**
 * Unified Warm-Tech Ceramic Optical Lab Figure Generator
 * 《掀开大模型的黑盒子》全 15 期真机实验图鉴统一重绘脚本 (11 Figures, 2x Retina)
 *
 * Reads exact measurements from data/*.csv and data/wechat_series_materials.json
 * and renders crisp HTML/SVG plates via local headless Chrome CDP to assets/*.png.
 */
import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO = path.resolve(__dirname, "..");
const DATA_DIR = path.join(REPO, "data");
const ASSETS_DIR = path.join(REPO, "assets");

const T = {
  paper: "#FAF9F6",
  card: "#FFFFFF",
  subcard: "#F4F6FA",
  border: "#E6E2DA",
  grid: "#ECEAE4",
  gridDark: "#CFD5DF",
  ink: "#18202C",
  ink2: "#3D495C",
  muted: "#5C687A",
  pine: "#2B548A",
  pineSoft: "#EFF4FC",
  pineMid: "#4D7BB8",
  vermilion: "#C85A38",
  vermilionSoft: "#FDF2EC",
  ochre: "#C57A28",
  ochreSoft: "#FDF6EA",
  slate: "#1E6F80",
  slateSoft: "#EDF7F9",
  plum: "#5D4F9B",
  plumSoft: "#F3F1FB",
  stone: "#8690A0",
  stoneSoft: "#F1F3F6",
  warmGlow: "#E08B5A",
};

function parseCSV(filename) {
  const raw = fs.readFileSync(path.join(DATA_DIR, filename), "utf8").trim();
  const lines = raw.split(/\r?\n/);
  const parseLine = (line) => {
    const out = [];
    let cur = "";
    let inQ = false;
    for (let i = 0; i < line.length; i++) {
      const ch = line[i];
      if (ch === '"') {
        if (inQ && line[i + 1] === '"') { cur += '"'; i++; }
        else inQ = !inQ;
      } else if (ch === "," && !inQ) {
        out.push(cur); cur = "";
      } else {
        cur += ch;
      }
    }
    out.push(cur);
    return out;
  };
  const headers = parseLine(lines[0]);
  return lines.slice(1).filter(Boolean).map((l) => {
    const vals = parseLine(l);
    const obj = {};
    headers.forEach((h, idx) => { obj[h.trim()] = (vals[idx] ?? "").trim(); });
    return obj;
  });
}

const MAT = JSON.parse(fs.readFileSync(path.join(DATA_DIR, "wechat_series_materials.json"), "utf8"));

function esc(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function fmtNum(n) {
  return Number(n).toLocaleString("en-US");
}

function mixHex(hexA, hexB, t) {
  const p = (h) => [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)];
  const a = p(hexA), b = p(hexB);
  const c = a.map((v, i) => Math.round(v + (b[i] - v) * Math.max(0, Math.min(1, t))));
  return "#" + c.map((x) => x.toString(16).padStart(2, "0")).join("");
}

function divergingColor(val, maxAbs = 0.45) {
  const t = Math.max(-1, Math.min(1, val / maxAbs));
  if (t >= 0) return mixHex("#FAF9F6", "#C85A38", Math.pow(t, 0.85) * 0.92);
  return mixHex("#FAF9F6", "#2B548A", Math.pow(-t, 0.85) * 0.92);
}

function sequentialPine(t) {
  const c = Math.max(0, Math.min(1, t));
  if (c < 0.5) return mixHex("#F5F7FB", "#6E9BD0", c * 2);
  return mixHex("#6E9BD0", "#214678", (c - 0.5) * 2);
}

function wrapPlate({ figNum, epTag, title, subtitle, bodyHtml, footerNote, width = 1200 }) {
  return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8" />
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html, body {
    background: ${T.paper};
    color: ${T.ink};
    font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Noto Sans SC", sans-serif;
    -webkit-font-smoothing: antialiased;
    width: ${width}px;
  }
  .plate {
    width: ${width}px;
    background:
      radial-gradient(ellipse 65% 24% at 90% 0%, rgba(224, 139, 90, 0.11), transparent 72%),
      radial-gradient(ellipse 60% 24% at 10% 0%, rgba(43, 84, 138, 0.075), transparent 70%),
      ${T.paper};
    padding: 28px 36px 24px 36px;
    position: relative;
  }
  .plate::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, ${T.pine} 0%, ${T.pineMid} 48%, ${T.warmGlow} 100%);
  }
  .folio {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 12px;
    border-bottom: 1px solid ${T.border};
    margin-bottom: 16px;
  }
  .folio-left { display: flex; align-items: center; gap: 10px; }
  .fig-badge {
    font-family: "SF Mono", "JetBrains Mono", Menlo, monospace;
    font-size: 11.5px;
    font-weight: 700;
    letter-spacing: 0.08em;
    color: #FFFFFF;
    background: linear-gradient(135deg, ${T.pine} 0%, ${T.pineMid} 100%);
    padding: 3.5px 11px;
    border-radius: 999px;
  }
  .ep-tag { font-size: 13px; font-weight: 600; color: ${T.ink2}; letter-spacing: 0.015em; }
  .folio-right {
    font-family: "SF Mono", "JetBrains Mono", Menlo, monospace;
    font-size: 11.5px;
    color: ${T.muted};
    letter-spacing: 0.04em;
  }
  .header { margin-bottom: 18px; }
  .title {
    font-family: "Source Han Serif SC", "Noto Serif SC", "Songti SC", "STSong", "PingFang SC", serif;
    font-size: 25px;
    font-weight: 800;
    color: ${T.ink};
    line-height: 1.32;
    letter-spacing: -0.01em;
    margin-bottom: 6px;
  }
  .subtitle { font-size: 14px; color: ${T.ink2}; line-height: 1.58; }
  .panel-grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }
  .panel-card {
    background: ${T.card};
    border: 1px solid #EBE7DF;
    border-radius: 12px;
    box-shadow: 0 2px 10px rgba(24, 32, 44, 0.04);
    padding: 18px 20px 16px 20px;
  }
  .panel-title { font-size: 15px; font-weight: 700; color: ${T.ink}; margin-bottom: 4px; line-height: 1.35; }
  .panel-sub { font-size: 12.5px; color: ${T.muted}; margin-bottom: 10px; line-height: 1.45; }
  .mono { font-family: "SF Mono", "JetBrains Mono", Menlo, monospace; font-variant-numeric: tabular-nums; }
  .legend-row {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 14px;
    font-size: 12px;
    color: ${T.ink2};
    margin-bottom: 8px;
  }
  .legend-item { display: inline-flex; align-items: center; gap: 6px; font-weight: 500; }
  .swatch { width: 11px; height: 11px; border-radius: 2px; display: inline-block; flex-shrink: 0; }
  .swatch-dot { width: 9px; height: 9px; border-radius: 999px; display: inline-block; flex-shrink: 0; }
  .footer {
    margin-top: 16px;
    padding-top: 10px;
    border-top: 1px solid ${T.border};
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 11.5px;
    color: ${T.muted};
  }
  svg { display: block; max-width: 100%; height: auto; }
  svg text { font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", sans-serif; }
  svg .t-mono { font-family: "SF Mono", "JetBrains Mono", Menlo, monospace; font-variant-numeric: tabular-nums; }
</style>
</head>
<body>
  <div class="plate" id="plate">
    <div class="folio">
      <div class="folio-left">
        <span class="fig-badge">${esc(figNum)}</span>
        <span class="ep-tag">${esc(epTag)}</span>
      </div>
      <div class="folio-right">DEEPSEEK-CODER-1.3B · 真机前向实测图鉴</div>
    </div>
    <div class="header">
      <div class="title">${esc(title)}</div>
      <div class="subtitle">${esc(subtitle)}</div>
    </div>
    ${bodyHtml}
    <div class="footer">
      <span>${esc(footerNote)}</span>
      <span>《掀开大模型的黑盒子》全 15 期科普连载</span>
    </div>
  </div>
</body>
</html>`;
}

// FIG 1: fig2_param_budget.png (Ep 01)
function buildFigParamBudget() {
  const pb = MAT.ep08_layer_tracking.param_buckets;
  const ov = MAT.ep01_overview;
  const rows = [
    { name: "MLP 前馈网络（24 层）", desc: "知识记忆与非线性变换主力", pct: pb.mlp.pct, m: pb.mlp.count / 1e6, color: T.pine },
    { name: "Attention 注意力（24 层）", desc: "跨词上下文关联与 Q/K/V/O 投影", pct: pb.attention.pct, m: pb.attention.count / 1e6, color: T.ochre },
    { name: "静态词表 Embedding", desc: "32,256 × 2,048 输入查表矩阵", pct: pb.embedding.pct, m: pb.embedding.count / 1e6, color: T.vermilion },
    { name: "输出投影头 LM Head", desc: "2,048 → 32,256 词表概率投影", pct: pb.lm_head.pct, m: pb.lm_head.count / 1e6, color: T.plum },
  ];

  let rx = 0;
  const ribbonW = 1094;
  const ribbonSvg = rows.map((r) => {
    const w = (r.pct / 100) * ribbonW;
    const seg = `<rect x="${rx.toFixed(1)}" y="0" width="${Math.max(2, w - 2).toFixed(1)}" height="30" rx="3" fill="${r.color}" />
      ${w > 95 ? `<text x="${(rx + w / 2).toFixed(1)}" y="20" text-anchor="middle" fill="#fff" font-size="12.5" font-weight="700" class="t-mono">${r.pct.toFixed(1)}%</text>` : ""}`;
    rx += w;
    return seg;
  }).join("");

  const barRows = rows.map((r, i) => {
    const y = 20 + i * 74;
    const maxW = 450;
    const bw = (r.pct / 66) * maxW;
    return `
      <text x="216" y="${y + 18}" text-anchor="end" fill="${T.ink}" font-size="14.5" font-weight="700">${esc(r.name)}</text>
      <text x="216" y="${y + 37}" text-anchor="end" fill="${T.muted}" font-size="12">${esc(r.desc)}</text>
      <rect x="234" y="${y + 4}" width="${bw.toFixed(1)}" height="34" rx="4" fill="${r.color}" />
      <text x="${(234 + bw + 12).toFixed(1)}" y="${y + 26}" fill="${T.ink}" font-size="14.5" font-weight="700" class="t-mono">${r.pct.toFixed(1)}% <tspan fill="${T.muted}" font-weight="500" font-size="13">(${r.m.toFixed(1)} M)</tspan></text>
    `;
  }).join("");

  const gridTicks = [0, 20, 40, 60].map((v) => {
    const x = 234 + (v / 66) * 450;
    return `<line x1="${x.toFixed(1)}" y1="8" x2="${x.toFixed(1)}" y2="310" stroke="${v === 0 ? T.border : T.grid}" stroke-width="${v === 0 ? 1.2 : 1}" stroke-dasharray="${v === 0 ? "none" : "3,3"}" />
            <text x="${x.toFixed(1)}" y="330" text-anchor="middle" fill="${T.muted}" font-size="12" class="t-mono">${v}%</text>`;
  }).join("");

  const specs = [
    ["总参数量", "1,346,471,936"],
    ["权重张量数", `${ov.total_tensors} 个`],
    ["Transformer 层数", `${ov.layers} 层`],
    ["隐藏维度 d_model", `${ov.hidden_size} 维`],
    ["注意力头数", `${ov.num_heads} 头 × ${ov.head_dim} 维`],
    ["词表矩阵行数", `${fmtNum(ov.vocab_size)} 行`],
  ].map(([k, v]) => `
    <div style="display:flex;justify-content:space-between;align-items:baseline;padding:9px 0;border-bottom:1px solid ${T.border};">
      <span style="font-size:12.5px;color:${T.ink2};">${k}</span>
      <span class="mono" style="font-size:13.5px;font-weight:700;color:${T.ink};">${v}</span>
    </div>
  `).join("");

  const bodyHtml = `
    <div class="panel-card" style="margin-bottom:16px;padding:15px 18px;">
      <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:9px;">
        <span style="font-size:14px;font-weight:700;color:${T.ink};">13.46 亿参数全景占比切片</span>
        <span style="font-size:12.5px;color:${T.pine};font-weight:600;">24 层计算权重合计 90.18%（1,214.3 M） · 词表与输出头合计 9.82%（132.1 M）</span>
      </div>
      <svg width="1094" height="34" viewBox="0 0 1094 34">${ribbonSvg}</svg>
    </div>
    <div style="display:grid;grid-template-columns:1fr 276px;gap:18px;align-items:stretch;">
      <div class="panel-card">
        <div class="panel-title">各核心模块参数明细（实测权重张量汇总）</div>
        <div class="panel-sub">层归一化 RMSNorm 共 49 个张量，仅占 0.01%（0.10 M），未单独列条</div>
        <svg width="800" height="342" viewBox="0 0 800 342">
          ${gridTicks}
          ${barRows}
        </svg>
      </div>
      <div class="panel-card" style="display:flex;flex-direction:column;justify-content:space-between;background:${T.subcard};">
        <div>
          <div class="panel-title" style="margin-bottom:10px;">模型骨架规格</div>
          ${specs}
        </div>
        <div style="margin-top:14px;padding:10px 12px;background:${T.pineSoft};border-left:3px solid ${T.pine};border-radius:4px;font-size:12px;line-height:1.6;color:${T.ink};">
          <strong>核心结论：</strong>查词表只占不到二十分之一的参数，真正决定理解与推理能力的是中间 24 层 MLP 与 Attention 矩阵。
        </div>
      </div>
    </div>
  `;

  return wrapPlate({
    figNum: "FIG. 01",
    epTag: "第 01 期 · 大模型总体观与架构拆解",
    title: "DeepSeek-1.3B 全部 13.46 亿参数去哪了？",
    subtitle: "静态词表仅占 4.9%，24 层 Transformer 计算权重（MLP + Attention）独占 90.2%，是绝对主力",
    bodyHtml,
    footerNote: "数据来源：DeepSeek-Coder-1.3B 实测权重文件（219 个参数张量精确统计）",
  });
}

// FIG 2: fig1_random_vs_trained.png (Ep 02 & Ep 10)
function buildFigRandomVsTrained() {
  const tr = MAT.ep10_training;
  const pairs = [...tr.random_vs_trained_pairs].sort((a, b) => b.trained_cos - a.trained_cos);
  const radToDeg = (c) => (Math.acos(Math.max(-1, Math.min(1, c))) * 180) / Math.PI;

  const angleMin = 48, angleMax = 96;
  const ax = (deg) => 112 + ((deg - angleMin) / (angleMax - angleMin)) * 372;
  const angleRows = pairs.map((p, idx) => {
    const y = 26 + idx * 31;
    const rDeg = radToDeg(p.random_cos);
    const tDeg = radToDeg(p.trained_cos);
    const label = `${p.w1} · ${p.w2}`;
    return `
      <line x1="112" y1="${y}" x2="484" y2="${y}" stroke="${T.grid}" stroke-width="0.8" />
      <text x="102" y="${y + 4.5}" text-anchor="end" fill="${T.ink}" font-size="12.5" font-weight="600">${esc(label)}</text>
      <line x1="${ax(tDeg).toFixed(1)}" y1="${y}" x2="${ax(rDeg).toFixed(1)}" y2="${y}" stroke="${T.pineMid}" stroke-width="2.6" stroke-opacity="0.45" />
      <circle cx="${ax(rDeg).toFixed(1)}" cy="${y}" r="4.5" fill="${T.stone}" />
      <circle cx="${ax(tDeg).toFixed(1)}" cy="${y}" r="5.5" fill="${T.pine}" />
      <text x="${(ax(tDeg) - 9).toFixed(1)}" y="${y + 4}" text-anchor="end" fill="${T.pine}" font-size="11.5" font-weight="700" class="t-mono">${tDeg.toFixed(1)}°</text>
    `;
  }).join("");

  const angleTicks = [50, 60, 70, 80, 90].map((v) => {
    const x = ax(v);
    return `<line x1="${x.toFixed(1)}" y1="10" x2="${x.toFixed(1)}" y2="392" stroke="${v === 90 ? T.vermilion : T.grid}" stroke-dasharray="${v === 90 ? "4,3" : "none"}" stroke-width="${v === 90 ? 1.4 : 0.8}" />
            <text x="${x.toFixed(1)}" y="410" text-anchor="middle" fill="${v === 90 ? T.vermilion : T.muted}" font-size="11.5" font-weight="${v === 90 ? 700 : 500}" class="t-mono">${v}°</text>`;
  }).join("");

  const bx = (v) => 112 + ((v + 0.06) / 0.74) * 372;
  const cosTicks = [0, 0.2, 0.4, 0.6].map((v) => {
    const x = bx(v);
    return `<line x1="${x.toFixed(1)}" y1="10" x2="${x.toFixed(1)}" y2="392" stroke="${v === 0 ? T.gridDark : T.grid}" stroke-width="${v === 0 ? 1.2 : 0.8}" />
            <text x="${x.toFixed(1)}" y="410" text-anchor="middle" fill="${T.muted}" font-size="11.5" class="t-mono">${v.toFixed(1)}</text>`;
  }).join("");

  const cosRows = pairs.map((p, idx) => {
    const y = 26 + idx * 31;
    const label = `${p.w1} · ${p.w2}`;
    const x0 = bx(p.random_cos);
    const x1 = bx(p.trained_cos);
    return `
      <line x1="112" y1="${y}" x2="484" y2="${y}" stroke="${T.grid}" stroke-width="0.8" />
      <text x="102" y="${y + 4.5}" text-anchor="end" fill="${T.ink}" font-size="12.5" font-weight="600">${esc(label)}</text>
      <line x1="${x0.toFixed(1)}" y1="${y}" x2="${x1.toFixed(1)}" y2="${y}" stroke="${T.pine}" stroke-width="3" stroke-opacity="0.55" />
      <circle cx="${x0.toFixed(1)}" cy="${y}" r="4.5" fill="${T.stone}" />
      <circle cx="${x1.toFixed(1)}" cy="${y}" r="5.8" fill="${T.vermilion}" />
      <text x="${(x1 + 10).toFixed(1)}" y="${y + 4.5}" fill="${T.ink}" font-size="12" font-weight="700" class="t-mono">+${p.trained_cos.toFixed(2)}</text>
    `;
  }).join("");

  const bodyHtml = `
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px;margin-bottom:16px;">
      <div class="panel-card" style="padding:13px 16px;background:${T.subcard};">
        <div style="font-size:12px;color:${T.muted};margin-bottom:4px;">训练前 · 300 词最近邻余弦均值</div>
        <div style="display:flex;align-items:baseline;gap:10px;">
          <span class="mono" style="font-size:25px;font-weight:800;color:${T.stone};">${tr.nn_random_mean.toFixed(3)}</span>
          <span style="font-size:12px;color:${T.ink2};">彼此近似正交（一盘散沙）</span>
        </div>
      </div>
      <div class="panel-card" style="padding:13px 16px;background:${T.pineSoft};border-color:#CADBF2;">
        <div style="font-size:12px;color:${T.pine};font-weight:600;margin-bottom:4px;">训练后 · DeepSeek-1.3B 最近邻均值</div>
        <div style="display:flex;align-items:baseline;gap:10px;">
          <span class="mono" style="font-size:25px;font-weight:800;color:${T.pine};">${tr.nn_trained_mean.toFixed(3)}</span>
          <span style="font-size:12px;color:${T.ink};">相关词自动形成语义团簇</span>
        </div>
      </div>
      <div class="panel-card" style="padding:13px 16px;background:${T.vermilionSoft};border-color:#F2D3C5;">
        <div style="font-size:12px;color:${T.vermilion};font-weight:600;margin-bottom:4px;">聚拢倍数 · 预训练几何跃迁</div>
        <div style="display:flex;align-items:baseline;gap:10px;">
          <span class="mono" style="font-size:25px;font-weight:800;color:${T.vermilion};">${(tr.nn_trained_mean / tr.nn_random_mean).toFixed(1)}×</span>
          <span style="font-size:12px;color:${T.ink};">「男·女」拉近 36°，「北京·上海」30°</span>
        </div>
      </div>
    </div>
    <div class="panel-grid-2">
      <div class="panel-card">
        <div class="panel-title">A. 2048 维空间夹角收缩（随机正交 90° → 训练后靠拢）</div>
        <div class="panel-sub">高维随机向量的夹角通常接近正交（90° 虚线）；预训练将共现词向彼此旋转</div>
        <div class="legend-row">
          <span class="legend-item"><span class="swatch-dot" style="background:${T.stone};"></span>训练前（随机初始化）</span>
          <span class="legend-item"><span class="swatch-dot" style="background:${T.pine};"></span>训练后（真实夹角 θ）</span>
        </div>
        <svg width="520" height="428" viewBox="0 0 520 428">
          ${angleTicks}
          ${angleRows}
          <text x="298" y="425" text-anchor="middle" fill="${T.ink2}" font-size="12" font-weight="600">词向量夹角 θ（度，越小越语义相近）</text>
        </svg>
      </div>
      <div class="panel-card">
        <div class="panel-title">B. 12 组典型词对余弦相似度跃升</div>
        <div class="panel-sub">灰点表示随机初始化，陶橘色点表示 DeepSeek-1.3B 静态词表实测值</div>
        <div class="legend-row">
          <span class="legend-item"><span class="swatch-dot" style="background:${T.stone};"></span>随机噪音表（≈ 0.00）</span>
          <span class="legend-item"><span class="swatch-dot" style="background:${T.vermilion};"></span>预训练后静态词表</span>
        </div>
        <svg width="520" height="428" viewBox="0 0 520 428">
          ${cosTicks}
          ${cosRows}
          <text x="298" y="425" text-anchor="middle" fill="${T.ink2}" font-size="12" font-weight="600">余弦相似度 Cosine Similarity</text>
        </svg>
      </div>
    </div>
  `;

  return wrapPlate({
    figNum: "FIG. 02",
    epTag: "第 02 / 12 期 · 从随机噪音表到语义几何空间",
    title: "随机初始化噪音表 vs DeepSeek-1.3B 训练后语义表实测对比",
    subtitle: "高维空间里的随机词向量彼此正交（夹角 ≈ 90°）；海量语料预训练后，共现词对在 2048 维空间中自动旋转聚拢",
    bodyHtml,
    footerNote: "数据来源：DeepSeek-Coder-1.3B 静态 Embedding（32,256 × 2,048）与同维度高斯随机矩阵对比实测",
  });
}

// FIG 3: deepseek_token_anatomy.png (Ep 03)
function buildFigTokenAnatomy() {
  const cats = [
    { name: "英文与代码标识符", count: 23251, pct: 72.1, color: T.pine },
    { name: "代码符号与标点组合", count: 3321, pct: 10.3, color: T.pineMid },
    { name: "中文多字词组 (2–4字)", count: 2668, pct: 8.3, color: T.vermilion },
    { name: "中文单字 (1字)", count: 2134, pct: 6.6, color: "#DF7B57" },
    { name: "基础字节与 UTF-8 残片", count: 573, pct: 1.8, color: T.ochre },
    { name: "GPU 对齐幽灵空位 (未用)", count: 234, pct: 0.7, color: T.plum },
    { name: "空白缩进 / 数字 / 控制符", count: 75, pct: 0.2, color: T.stone },
  ];

  const pASvg = (() => {
    const maxV = 28500, x0 = 165, wMax = 242;
    const rows = cats.map((c, i) => {
      const y = 14 + i * 38;
      const bw = Math.max(3, (c.count / maxV) * wMax);
      return `
        <text x="${x0 - 10}" y="${y + 18}" text-anchor="end" fill="${T.ink}" font-size="12.5" font-weight="600">${esc(c.name)}</text>
        <rect x="${x0}" y="${y + 4}" width="${wMax}" height="22" rx="3" fill="${T.subcard}" />
        <rect x="${x0}" y="${y + 4}" width="${bw.toFixed(1)}" height="22" rx="3" fill="${c.color}" />
        <text x="${(x0 + bw + 8).toFixed(1)}" y="${y + 19}" fill="${T.ink}" font-size="11.8" font-weight="700" class="t-mono">${fmtNum(c.count)} <tspan fill="${T.muted}" font-weight="500">(${c.pct.toFixed(1)}%)</tspan></text>
      `;
    }).join("");
    const ticks = [0, 10000, 20000].map((v) => {
      const x = x0 + (v / maxV) * wMax;
      return `<line x1="${x.toFixed(1)}" y1="8" x2="${x.toFixed(1)}" y2="280" stroke="${T.grid}" />
              <text x="${x.toFixed(1)}" y="296" text-anchor="middle" fill="${T.muted}" font-size="11" class="t-mono">${v === 0 ? "0" : (v / 1000) + "k"}</text>`;
    }).join("");
    return `<svg width="525" height="308" viewBox="0 0 525 308">${ticks}${rows}</svg>`;
  })();

  const merges = [
    { word: "一 (id=503)", rank: 261, col: T.stone },
    { word: "在 (id=608)", rank: 366, col: T.stone },
    { word: "我 (id=848)", rank: 606, col: T.stone },
    { word: "一个 (id=1604)", rank: 1362, col: T.pine },
    { word: "公司 (id=2804)", rank: 2562, col: T.pine },
    { word: "商 / 店 (2888/5432)", rank: 5190, col: T.stone, customLbl: "#2,646 / #5,190" },
    { word: "商业 (id=12996)", rank: 12754, col: T.ochre },
    { word: "商品 (id=15631)", rank: 15389, col: T.ochre },
    { word: "苹 (id=16973)", rank: 16731, col: T.vermilion },
    { word: "苹果 (id=17144)", rank: 16902, col: T.vermilion },
    { word: "商务 (id=22201)", rank: 21959, col: T.ochre },
    { word: "我在 (id=23098)", rank: 22856, col: T.pine },
    { word: "公安局 (id=30431)", rank: 30189, col: T.plum },
    { word: "商店（落选! 拆商+店）", rank: 34400, col: "#A63A2B", missed: true },
  ];

  const pBSvg = (() => {
    const x0 = 152, wMax = 278, maxR = 37000;
    const sx = (r) => x0 + (r / maxR) * wMax;
    const cutX = sx(31757);
    const rows = merges.map((m, i) => {
      const y = 16 + i * 20.4;
      const cx = sx(m.rank);
      const lbl = m.missed ? "未进前 31,757" : (m.customLbl || `#${fmtNum(m.rank)}`);
      const nearCut = !m.missed && m.rank > 25000;
      const lblSvg = nearCut
        ? `<rect x="${(cx - 60).toFixed(1)}" y="${(y - 8).toFixed(1)}" width="52" height="15" rx="3" fill="#FFFFFF" fill-opacity="0.94" />
           <text x="${(cx - 10).toFixed(1)}" y="${y + 3.5}" text-anchor="end" fill="${T.ink2}" font-size="10.8" font-weight="700" class="t-mono">${lbl}</text>`
        : `<text x="${(cx + 7).toFixed(1)}" y="${y + 3.8}" fill="${m.missed ? T.vermilion : T.ink2}" font-size="10.8" font-weight="700" class="t-mono">${lbl}</text>`;
      return `
        <text x="${x0 - 8}" y="${y + 4}" text-anchor="end" fill="${m.missed ? T.vermilion : T.ink}" font-size="11.5" font-weight="${m.missed ? 700 : 600}">${esc(m.word)}</text>
        <line x1="${x0}" y1="${y}" x2="${cx.toFixed(1)}" y2="${y}" stroke="${m.col}" stroke-width="2" stroke-opacity="0.55" ${m.missed ? 'stroke-dasharray="3,2"' : ""} />
        <circle cx="${cx.toFixed(1)}" cy="${y}" r="3.8" fill="${m.col}" />
        ${lblSvg}
      `;
    }).join("");
    return `<svg width="530" height="308" viewBox="0 0 530 308">
      <rect x="${cutX.toFixed(1)}" y="6" width="${(522 - cutX).toFixed(1)}" height="284" fill="${T.vermilionSoft}" fill-opacity="0.72" />
      <line x1="${cutX.toFixed(1)}" y1="6" x2="${cutX.toFixed(1)}" y2="290" stroke="${T.vermilion}" stroke-width="1.6" stroke-dasharray="4,3" />
      <text x="${(cutX - 6).toFixed(1)}" y="24" text-anchor="end" fill="${T.vermilion}" font-size="11" font-weight="700">词表关门线 #31,757</text>
      ${[0, 10000, 20000, 31757].map((v) => `
        <line x1="${sx(v).toFixed(1)}" y1="8" x2="${sx(v).toFixed(1)}" y2="290" stroke="${v === 31757 ? "none" : T.grid}" />
        <text x="${sx(v).toFixed(1)}" y="304" text-anchor="middle" fill="${v === 31757 ? T.vermilion : T.muted}" font-size="10.8" class="t-mono">${v === 0 ? "0" : v === 31757 ? "31,757" : (v / 1000) + "k"}</text>
      `).join("")}
      ${rows}
    </svg>`;
  })();

  const cjk = [
    { lbl: "1 字词元", sub: "单字", count: 2134, ex: "的 / 一 / 是 / 在 / 我 / 商 / 店", col: T.stone },
    { lbl: "2 字词元", sub: "双字搭配", count: 2398, ex: "一个 / 我们 / 公司 / 商业 / 苹果 / 我在", col: T.pine },
    { lbl: "3 字词元", sub: "高频短语", count: 251, ex: "自己的 / 的时候 / 为什么 / 公安局", col: T.ochre },
    { lbl: "4 字词元", sub: "固定套语", count: 19, ex: "有限公司 / 人工智能 / 的情况下", col: T.vermilion },
  ];

  const pCSvg = (() => {
    const baseY = 186, maxH = 148, maxC = 2700;
    const cols = cjk.map((c, i) => {
      const cx = 74 + i * 124;
      const h = Math.max(4, (c.count / maxC) * maxH);
      const y = baseY - h;
      return `
        <rect x="${cx - 32}" y="${y.toFixed(1)}" width="64" height="${h.toFixed(1)}" rx="4" fill="${c.col}" />
        <text x="${cx}" y="${(y - 8).toFixed(1)}" text-anchor="middle" fill="${T.ink}" font-size="13" font-weight="800" class="t-mono">${fmtNum(c.count)}</text>
        <text x="${cx}" y="${baseY + 19}" text-anchor="middle" fill="${T.ink}" font-size="13" font-weight="700">${c.lbl}</text>
        <text x="${cx}" y="${baseY + 35}" text-anchor="middle" fill="${T.muted}" font-size="11">${c.sub}</text>
      `;
    }).join("");
    const grid = [0, 1000, 2000].map((v) => {
      const y = baseY - (v / maxC) * maxH;
      return `<line x1="28" y1="${y.toFixed(1)}" x2="508" y2="${y.toFixed(1)}" stroke="${T.grid}" />
              <text x="23" y="${(y + 4).toFixed(1)}" text-anchor="end" fill="${T.muted}" font-size="10.5" class="t-mono">${v === 0 ? "0" : (v / 1000) + "k"}</text>`;
    }).join("");
    const exCards = cjk.map((c) => `
      <div style="display:flex;align-items:baseline;gap:8px;font-size:11.5px;line-height:1.45;padding:2.5px 0;">
        <span style="display:inline-block;width:8px;height:8px;border-radius:2px;background:${c.col};flex-shrink:0;"></span>
        <strong style="color:${T.ink};flex-shrink:0;">${c.lbl}：</strong>
        <span style="color:${T.ink2};">${c.ex}</span>
      </div>
    `).join("");
    return `<svg width="520" height="228" viewBox="0 0 520 228">${grid}${cols}</svg>
            <div style="margin-top:6px;padding:8px 12px;background:${T.subcard};border-radius:6px;border:1px solid ${T.border};">${exCards}</div>`;
  })();

  const ep06Rows = parseCSV("ep06_tensor_45_tokens.csv");
  const realPts = ep06Rows.map((r) => ({ id: +r.token_id, l2: +r.l2_norm, tok: r.token }));
  const landmarks = [
    { id: 848, l2: 9.88, lbl: "我 (id=848, L2=9.88)", lx: 152, ly: 32, w: 152 },
    { id: 2888, l2: 10.17, lbl: "商 (id=2888, L2=10.17)", lx: 356, ly: 22, w: 162 },
    { id: 16973, l2: 4.42, lbl: "苹 (id=16973, L2=4.42) 被吞噬", lx: 194, ly: 214, w: 192 },
    { id: 17144, l2: 8.07, lbl: "苹果 (id=17144, L2=8.07)", lx: 342, ly: 150, w: 168 },
    { id: 23098, l2: 7.94, lbl: "我在 (id=23098, L2=7.94)", lx: 422, ly: 94, w: 168 },
    { id: 32140, l2: 0.271, lbl: "234 幽灵行 (L2≈0.27 未训练)", lx: 404, ly: 254, w: 190 },
  ];

  const pDSvg = (() => {
    const x0 = 48, x1 = 510, y0 = 16, y1 = 278;
    const sx = (id) => x0 + (id / 33200) * (x1 - x0);
    const sy = (v) => y1 - (v / 12.2) * (y1 - y0);
    const grid = [0, 3, 6, 9, 12].map((v) => {
      const y = sy(v);
      return `<line x1="${x0}" y1="${y.toFixed(1)}" x2="${x1}" y2="${y.toFixed(1)}" stroke="${T.grid}" />
              <text x="${x0 - 8}" y="${(y + 4).toFixed(1)}" text-anchor="end" fill="${T.muted}" font-size="11" class="t-mono">${v}</text>`;
    }).join("") + [0, 10000, 20000, 30000].map((v) => {
      const x = sx(v);
      return `<line x1="${x.toFixed(1)}" y1="${y0}" x2="${x.toFixed(1)}" y2="${y1}" stroke="${T.grid}" />
              <text x="${x.toFixed(1)}" y="${y1 + 17}" text-anchor="middle" fill="${T.muted}" font-size="11" class="t-mono">${v === 0 ? "0" : (v / 1000) + "k"}</text>`;
    }).join("");

    const dots = realPts.map((p) =>
      `<circle cx="${sx(p.id).toFixed(1)}" cy="${sy(p.l2).toFixed(1)}" r="4.2" fill="${T.pine}" fill-opacity="0.48" stroke="${T.pine}" stroke-width="0.9" />`
    ).join("");

    const ghostX = sx(32022);
    const lms = landmarks.map((p) => {
      const px = sx(p.id), py = sy(p.l2);
      return `
        <line x1="${px.toFixed(1)}" y1="${py.toFixed(1)}" x2="${p.lx}" y2="${p.ly}" stroke="${T.vermilion}" stroke-width="1.2" stroke-dasharray="2,2" />
        <circle cx="${px.toFixed(1)}" cy="${py.toFixed(1)}" r="5.5" fill="${T.vermilion}" stroke="#fff" stroke-width="1.5" />
        <rect x="${p.lx - p.w / 2}" y="${p.ly - 12}" width="${p.w}" height="22" rx="4" fill="#FFFFFF" fill-opacity="0.95" stroke="${T.border}" />
        <text x="${p.lx}" y="${p.ly + 2.5}" text-anchor="middle" fill="${T.ink}" font-size="10.8" font-weight="700">${esc(p.lbl)}</text>
      `;
    }).join("");

    return `<svg width="525" height="320" viewBox="0 0 525 320">
      <rect x="${ghostX.toFixed(1)}" y="${y0}" width="${(x1 - ghostX).toFixed(1)}" height="${y1 - y0}" fill="${T.plumSoft}" />
      ${grid}
      <line x1="${x0}" y1="${sy(9.6).toFixed(1)}" x2="${sx(31800).toFixed(1)}" y2="${sy(8.1).toFixed(1)}" stroke="${T.pine}" stroke-width="2" stroke-dasharray="6,4" stroke-opacity="0.55" />
      ${dots}
      ${lms}
      <text x="278" y="314" text-anchor="middle" fill="${T.ink2}" font-size="11.5" font-weight="600">Token ID (0 → 32,255，按 BPE 合并顺位递增)</text>
      <text x="14" y="150" text-anchor="middle" fill="${T.ink2}" font-size="11.5" font-weight="600" transform="rotate(-90 14 150)">静态 Embedding 模长 (L2)</text>
    </svg>`;
  })();

  const bodyHtml = `
    <div class="panel-grid-2" style="margin-bottom:18px;">
      <div class="panel-card">
        <div class="panel-title">A. DeepSeek-1.3B 词表总账（矩阵共 32,256 行）</div>
        <div class="panel-sub">32,000 BPE 核心词元 + 22 附加控制符（含 13 幽灵字节）+ 234 GPU 64 倍对齐行</div>
        ${pASvg}
      </div>
      <div class="panel-card">
        <div class="panel-title">B. BPE 合并顺位 = 语料共现频率排行榜</div>
        <div class="panel-sub">越靠左频次越高；「商业 / 商品 / 商务 / 我在」抢进词表，「商店」被挡在门外</div>
        ${pBSvg}
      </div>
    </div>
    <div class="panel-grid-2">
      <div class="panel-card">
        <div class="panel-title">C. 纯中文词元字数分布（共 4,802 个，占总词表 14.9%）</div>
        <div class="panel-sub">2 字搭配（2,398）反超单字（2,134）——统计共现而非语法词典决定切词</div>
        ${pCSvg}
      </div>
      <div class="panel-card">
        <div class="panel-title">D. 权重里的“词频烙印”：Token ID vs 向量 L2 模长</div>
        <div class="panel-sub">实测 45 词样本（蓝点）与关键标记（陶橘色点）：被吞噬的「苹」与 234 幽灵行清晰可辨</div>
        ${pDSvg}
      </div>
    </div>
  `;

  return wrapPlate({
    figNum: "FIG. 03",
    epTag: "第 03 期 · 二进制、UTF-8 与词表总账解剖",
    title: "DeepSeek-1.3B 词元深度解剖：词表账本、合并顺位与权重词频烙印",
    subtitle: "基于 DeepSeek-Coder-1.3B 真实 tokenizer.json 与 Embedding 矩阵（32,256 × 2,048）实测统计",
    bodyHtml,
    footerNote: "数据来源：DeepSeek-Coder-1.3B 词表实测分类、BPE Merge Rank 记录与实测 L2 模长",
  });
}

// FIG 4: bpe_merging_process.png (Ep 04)
function buildFigBpeProcess() {
  const replay = parseCSV("bpe_sentence_replay.csv").map((r) => ({
    step: +r.step, rank: +r.merge_rank, n: +r.num_tokens, action: r.action,
  }));
  const growth = parseCSV("bpe_growth_compression.csv").map((r) => ({
    label: r.label, rank: +r.max_merge_rank, vocab: +r.vocab_size, n: +r.token_count, pct: +r.pct_of_bytes,
  }));

  function phaseOf(r) {
    if (r.step === 0) return { color: T.stone };
    if (r.action.includes("-> <0x")) return { color: T.ochre };
    if ([13, 20, 22, 23].includes(r.step)) return { color: T.vermilion };
    return { color: T.pine };
  }

  const pA = (() => {
    const x0 = 58, x1 = 1070, y0 = 26, y1 = 284;
    const sx = (s) => x0 + (s / 23) * (x1 - x0);
    const sy = (n) => y1 - (n / 40) * (y1 - y0);

    const gridY = [0, 6, 12, 18, 24, 30, 36].map((v) => {
      const y = sy(v);
      return `<line x1="${x0}" y1="${y.toFixed(1)}" x2="${x1}" y2="${y.toFixed(1)}" stroke="${T.grid}" />
              <text x="${x0 - 10}" y="${(y + 4).toFixed(1)}" text-anchor="end" fill="${T.muted}" font-size="11.5" class="t-mono">${v}</text>`;
    }).join("");
    const gridX = replay.map((r) => `<text x="${sx(r.step).toFixed(1)}" y="${y1 + 18}" text-anchor="middle" fill="${T.muted}" font-size="11" class="t-mono">${r.step}</text>`).join("");

    const ptsStr = replay.map((r) => `${sx(r.step).toFixed(1)},${sy(r.n).toFixed(1)}`).join(" ");
    const areaStr = `${x0},${y1} ${ptsStr} ${sx(23).toFixed(1)},${y1}`;
    const dots = replay.map((r) => `<circle cx="${sx(r.step).toFixed(1)}" cy="${sy(r.n).toFixed(1)}" r="5" fill="${phaseOf(r).color}" stroke="#fff" stroke-width="1.5" />`).join("");

    const callouts = [
      { step: 0, bx: 140, by: 122, w: 160, lines: ["Step 0 · 36 原始字节", "[e6][88][91]...[9c]"] },
      { step: 5, bx: 315, by: 42, w: 184, lines: ["Step 5 (Merge #261)", "合出本句第 1 个汉字「一」"] },
      { step: 11, bx: 420, by: 214, w: 204, lines: ["Step 11 (Merge #606)", "合出「一/在/了/个/我」5 高频字"] },
      { step: 13, bx: 685, by: 54, w: 226, lines: ["Step 13 (Merge #1,362)", "跨字合出「一个」(苹/果/商仍碎裂!)"] },
      { step: 20, bx: 695, by: 242, w: 218, lines: ["Step 20 (Merge #13,314)", "3 字词「了一个」成型，苹仍是残片"] },
      { step: 21, bx: 942, by: 100, w: 222, lines: ["Step 21–22 (#16,731→#16,902)", "「苹」刚拼好 171 轮即合体「苹果」"] },
      { step: 23, bx: 946, by: 180, w: 208, lines: ["Step 23 (Merge #22,856)", "「我+在→我在」，定格 7 词元"] },
    ];

    const annSvg = callouts.map((c) => {
      const r = replay[c.step];
      const px = sx(r.step), py = sy(r.n);
      return `
        <line x1="${px.toFixed(1)}" y1="${py.toFixed(1)}" x2="${c.bx}" y2="${c.by}" stroke="${T.ink2}" stroke-width="1" stroke-dasharray="3,2" />
        <rect x="${(c.bx - c.w / 2).toFixed(1)}" y="${c.by - 20}" width="${c.w}" height="40" rx="5" fill="#FFFFFF" stroke="${T.border}" />
        <text x="${c.bx}" y="${c.by - 4}" text-anchor="middle" fill="${T.ink}" font-size="11.2" font-weight="700">${esc(c.lines[0])}</text>
        <text x="${c.bx}" y="${c.by + 12}" text-anchor="middle" fill="${T.ink2}" font-size="10.8">${esc(c.lines[1])}</text>
      `;
    }).join("");

    return `<svg width="1090" height="338" viewBox="0 0 1090 338">
      ${gridY}
      <polygon points="${areaStr}" fill="${T.subcard}" fill-opacity="0.85" />
      <polyline points="${ptsStr}" fill="none" stroke="${T.ink}" stroke-width="2.2" />
      ${annSvg}
      ${dots}
      ${gridX}
      <text x="564" y="330" text-anchor="middle" fill="${T.ink2}" font-size="12" font-weight="600">本句触发的 BPE 合并步数（Step 0 → Step 23，按 Merge Rank 递增执行）</text>
      <text x="16" y="160" text-anchor="middle" fill="${T.ink2}" font-size="12" font-weight="600" transform="rotate(-90 16 160)">剩余词元块数</text>
    </svg>`;
  })();

  const seriesMeta = [
    { label: "中文日常句子 (36字节)", short: "中文日常句子 (36 字节)", color: T.vermilion },
    { label: "中文技术句子 (48字节)", short: "中文技术句子 (48 字节)", color: T.pine },
    { label: "Python代码行 (44字节)", short: "Python 代码行 (44 字节)", color: T.plum },
  ];

  const pB = (() => {
    const x0 = 58, x1 = 1018, y0 = 24, y1 = 278;
    const sx = (v) => x0 + ((v - 243) / (32000 - 243)) * (x1 - x0);
    const sy = (p) => y1 - ((p - 10) / 96) * (y1 - y0);

    const gridY = [20, 40, 60, 80, 100].map((v) => {
      const y = sy(v);
      return `<line x1="${x0}" y1="${y.toFixed(1)}" x2="${x1}" y2="${y.toFixed(1)}" stroke="${T.grid}" />
              <text x="${x0 - 10}" y="${(y + 4).toFixed(1)}" text-anchor="end" fill="${T.muted}" font-size="11.5" class="t-mono">${v}%</text>`;
    }).join("");
    const gridX = [243, 5000, 10000, 15000, 20000, 25000, 32000].map((v) => {
      const x = sx(v);
      return `<line x1="${x.toFixed(1)}" y1="${y0}" x2="${x.toFixed(1)}" y2="${y1}" stroke="${T.grid}" />
              <text x="${x.toFixed(1)}" y="${y1 + 18}" text-anchor="middle" fill="${T.muted}" font-size="11.5" class="t-mono">${fmtNum(v)}</text>`;
    }).join("");

    const linesSvg = seriesMeta.map((s, si) => {
      const pts = growth.filter((g) => g.label === s.label).sort((a, b) => a.vocab - b.vocab);
      const poly = pts.map((p) => `${sx(p.vocab).toFixed(1)},${sy(p.pct).toFixed(1)}`).join(" ");
      const dots = pts.map((p) => `<circle cx="${sx(p.vocab).toFixed(1)}" cy="${sy(p.pct).toFixed(1)}" r="3.6" fill="${s.color}" stroke="#fff" stroke-width="1.2" />`).join("");
      const last = pts[pts.length - 1];
      const yOff = si === 0 ? 2 : si === 1 ? 6 : 4;
      return `<polyline points="${poly}" fill="none" stroke="${s.color}" stroke-width="2.5" />${dots}
              <text x="${(sx(last.vocab) + 10).toFixed(1)}" y="${(sy(last.pct) + yOff).toFixed(1)}" text-anchor="start" fill="${s.color}" font-size="11.5" font-weight="700" class="t-mono">${last.pct.toFixed(1)}%</text>`;
    }).join("");

    const milestones = [
      { v: 243, pct: 100, bx: 215, by: 44, w: 208, l1: "起点 243 字节 (100%)", l2: "Merge #1 双空格 · #95「的」" },
      { v: 1840, pct: 58.3, bx: 280, by: 108, w: 208, l1: "词表 ~1,840 (Merge #1,362)", l2: "「一个」与 Python def 诞生" },
      { v: 10240, pct: 35.4, bx: 488, by: 112, w: 210, l1: "词表 ~10,240 (#10,909)", l2: "首个四字词「有限公司」入表" },
      { v: 17240, pct: 22.2, bx: 698, by: 146, w: 218, l1: "词表 ~17,240 (#13,314–16,902)", l2: "「了一个」「苹果」接连合体" },
      { v: 32000, pct: 19.4, bx: 904, by: 130, w: 218, l1: "终点 32,000 (Merge #31,757)", l2: "36 字节压缩至 7 词元 (19.4%)" },
    ];

    const msSvg = milestones.map((m) => {
      const px = sx(m.v), py = sy(m.pct);
      return `
        <line x1="${px.toFixed(1)}" y1="${py.toFixed(1)}" x2="${m.bx}" y2="${m.by}" stroke="${T.ink2}" stroke-width="1" stroke-dasharray="3,2" />
        <circle cx="${px.toFixed(1)}" cy="${py.toFixed(1)}" r="4.6" fill="${T.ink}" stroke="#fff" stroke-width="1.5" />
        <rect x="${(m.bx - m.w / 2).toFixed(1)}" y="${m.by - 20}" width="${m.w}" height="40" rx="5" fill="#FFFFFF" stroke="${T.border}" />
        <text x="${m.bx}" y="${m.by - 4}" text-anchor="middle" fill="${T.ink}" font-size="11.2" font-weight="700">${esc(m.l1)}</text>
        <text x="${m.bx}" y="${m.by + 12}" text-anchor="middle" fill="${T.ink2}" font-size="10.8">${esc(m.l2)}</text>
      `;
    }).join("");

    return `<svg width="1090" height="328" viewBox="0 0 1090 328">
      ${gridY}${gridX}${linesSvg}${msSvg}
      <text x="538" y="321" text-anchor="middle" fill="${T.ink2}" font-size="12" font-weight="600">词表规模生长过程（243 基础字节 → 32,000 个 BPE 核心词元）</text>
      <text x="16" y="150" text-anchor="middle" fill="${T.ink2}" font-size="12" font-weight="600" transform="rotate(-90 16 150)">剩余 Token / 原字节 (%)</text>
    </svg>`;
  })();

  const bodyHtml = `
    <div class="panel-card" style="margin-bottom:16px;">
      <div class="panel-title">A. 微观慢动作回放：「我在苹果商店吃了一个苹果」从 36 字节坍缩为 7 个 Token 的 23 步</div>
      <div class="panel-sub">反直觉真相：并非“先拼齐所有单字再组词”——「一个」和「了一个」早已成型，「苹」却还停留在 UTF-8 字节残片</div>
      <div class="legend-row">
        <span class="legend-item"><span class="swatch-dot" style="background:${T.stone};"></span>初始字节 (36 块)</span>
        <span class="legend-item"><span class="swatch-dot" style="background:${T.ochre};"></span>阶段①：字节拼成半字残片</span>
        <span class="legend-item"><span class="swatch-dot" style="background:${T.pine};"></span>阶段②：第 3 字节补齐汉字</span>
        <span class="legend-item"><span class="swatch-dot" style="background:${T.vermilion};"></span>阶段③：跨字合体为多字词组</span>
      </div>
      ${pA}
    </div>
    <div class="panel-card">
      <div class="panel-title">B. 宏观生长压缩曲线：31,757 轮统计合并如何把序列压短 4–5 倍</div>
      <div class="panel-sub">词表从 243 长至 32,000，日常中文、技术句子与 Python 代码均被压缩至原字节长度的 16%–26%</div>
      <div class="legend-row">
        ${seriesMeta.map((s) => `<span class="legend-item"><span class="swatch" style="background:${s.color};"></span>${s.short}</span>`).join("")}
      </div>
      ${pB}
    </div>
  `;

  return wrapPlate({
    figNum: "FIG. 04",
    epTag: "第 04 期 · BPE 滚雪球造词法真机回放",
    title: "BPE 算法实测全回放：从 243 个基础字节到 32,000 词元的滚雪球生长史",
    subtitle: "基于 DeepSeek-Coder-1.3B 真实 31,757 条 BPE 合并规则逐帧回放",
    bodyHtml,
    footerNote: "数据来源：data/bpe_sentence_replay.csv & data/bpe_growth_compression.csv（DeepSeek-Coder-1.3B 实测）",
  });
}

// FIG 5: tokenizer_design_tradeoffs.png (Ep 05)
function buildFigTokenizerTradeoffs() {
  const algo = parseCSV("algo_comparison_results.csv").map((r) => ({
    pair: r.pair, type: r.pair_type, bpe: +r.bpe_score, bpeRank: +r.bpe_rank, wp: +r.wp_score, wpRank: +r.wp_rank,
  }));
  const vocab = parseCSV("llm_vocab_landscape.csv").map((r) => ({
    size: +r.vocab_size, name: r.model_name, pct13: +r.pct_1_3b, pct70: +r.pct_70b, flops: +r.rel_attention_flops_pct,
  }));

  const typeColor = { "高频虚词搭配": T.vermilion, "高频量词搭配": T.ochre, "紧密语义实体": T.pine };

  const pA = (() => {
    const rowH = 34;
    const drawSide = (title, maxVal, getter, rankGetter, unit, xOff) => {
      const wMax = 350;
      const bars = algo.map((a, i) => {
        const y = 34 + i * rowH;
        const val = getter(a);
        const bw = (val / maxVal) * wMax;
        const col = typeColor[a.type] || T.pine;
        return `
          <rect x="${xOff}" y="${y}" width="${wMax}" height="22" rx="3" fill="${T.subcard}" />
          <rect x="${xOff}" y="${y}" width="${bw.toFixed(1)}" height="22" rx="3" fill="${col}" />
          <text x="${(xOff + bw + 8).toFixed(1)}" y="${y + 15.5}" fill="${T.ink}" font-size="12" font-weight="700" class="t-mono">#${rankGetter(a)} <tspan fill="${T.muted}" font-weight="500">(${unit === "次" ? val + "次" : val.toFixed(1)})</tspan></text>
        `;
      }).join("");
      return `<text x="${xOff}" y="18" fill="${T.ink}" font-size="13" font-weight="700">${esc(title)}</text>${bars}`;
    };

    const labels = algo.map((a, i) => `<text x="64" y="${34 + i * rowH + 15.5}" text-anchor="end" fill="${T.ink}" font-size="13.5" font-weight="700">${esc(a.pair)}</text>`).join("");

    return `<svg width="1090" height="278" viewBox="0 0 1090 278">
      ${labels}
      ${drawSide("BPE 合并指标：共现绝对频次 Count(A, B)", 230, (a) => a.bpe, (a) => a.bpeRank, "次", 78)}
      <line x1="564" y1="10" x2="564" y2="270" stroke="${T.border}" />
      ${drawSide("WordPiece 合并指标：互信息分 Count(AB)/[Count(A)Count(B)] ×1000", 78, (a) => a.wp, (a) => a.wpRank, "分", 588)}
    </svg>`;
  })();

  const pB = (() => {
    const x0 = 60, x1 = 1056, y0 = 22, y1 = 290;
    const sx = (sz) => x0 + ((sz / 1000 - 20) / (274 - 20)) * (x1 - x0);
    const sy = (p) => y1 - (p / 125) * (y1 - y0);

    const gridY = [0, 20, 40, 60, 80, 100, 120].map((v) => {
      const y = sy(v);
      return `<line x1="${x0}" y1="${y.toFixed(1)}" x2="${x1}" y2="${y.toFixed(1)}" stroke="${T.grid}" />
              <text x="${x0 - 10}" y="${(y + 4).toFixed(1)}" text-anchor="end" fill="${T.muted}" font-size="11.5" class="t-mono">${v}%</text>`;
    }).join("");
    const gridX = [30, 60, 90, 120, 150, 180, 210, 240].map((v) => {
      const x = sx(v * 1000);
      return `<line x1="${x.toFixed(1)}" y1="${y0}" x2="${x.toFixed(1)}" y2="${y1}" stroke="${T.grid}" />
              <text x="${x.toFixed(1)}" y="${y1 + 18}" text-anchor="middle" fill="${T.muted}" font-size="11.5" class="t-mono">${v}k</text>`;
    }).join("");

    const lineFor = (key, color, dash = "") => {
      const poly = vocab.map((v) => `${sx(v.size).toFixed(1)},${sy(v[key]).toFixed(1)}`).join(" ");
      const dots = vocab.map((v) => `<circle cx="${sx(v.size).toFixed(1)}" cy="${sy(v[key]).toFixed(1)}" r="4.5" fill="${color}" stroke="#fff" stroke-width="1.4" />`).join("");
      return `<polyline points="${poly}" fill="none" stroke="${color}" stroke-width="2.8" ${dash ? `stroke-dasharray="${dash}"` : ""} />${dots}`;
    };

    const modelPins = [
      { idx: 0, yVal: vocab[0].flops, lx: sx(30522) + 18, ly: sy(115.4) + 3, anchor: "start", lbl: "BERT (30.5k · 115%)" },
      { idx: 1, yVal: vocab[1].pct13, lx: sx(32256) + 16, ly: sy(9.81) - 24, anchor: "start", lbl: "ds13b / LLaMA-2 (32.3k)" },
      { idx: 2, yVal: vocab[2].flops, lx: sx(50257) + 16, ly: sy(85.7) - 5, anchor: "start", lbl: "GPT-2/3 (50.3k)" },
      { idx: 3, yVal: vocab[3].flops, lx: sx(64000) + 16, ly: sy(60.5) - 6, anchor: "start", lbl: "Baichuan-2 (64k)" },
      { idx: 4, yVal: vocab[4].flops, lx: sx(100256) + 10, ly: sy(49.5) - 16, anchor: "start", lbl: "GPT-4 (100.3k)" },
      { idx: 5, yVal: vocab[5].pct13, lx: sx(129280) - 6, ly: sy(30.37) + 30, anchor: "middle", lbl: "DeepSeek-V3/R1 (129.3k)" },
      { idx: 6, yVal: vocab[6].pct13, lx: sx(151936), ly: sy(33.88) - 22, anchor: "middle", lbl: "Qwen-2.5 (151.9k)" },
      { idx: 7, yVal: vocab[7].pct13, lx: sx(200019), ly: sy(40.29) - 22, anchor: "middle", lbl: "GPT-4o (200k)" },
      { idx: 8, yVal: vocab[8].pct13, lx: sx(256000) - 8, ly: sy(46.34) - 24, anchor: "end", lbl: "Gemma-2/3 (256k · 46.3%)" },
    ];

    const pinsSvg = modelPins.map((p) => {
      const v = vocab[p.idx];
      const px = sx(v.size), py = sy(p.yVal);
      return `
        <line x1="${px.toFixed(1)}" y1="${py.toFixed(1)}" x2="${p.lx.toFixed(1)}" y2="${(p.ly - 4).toFixed(1)}" stroke="${T.muted}" stroke-width="0.9" stroke-dasharray="2,2" />
        <text x="${p.lx.toFixed(1)}" y="${p.ly.toFixed(1)}" text-anchor="${p.anchor}" fill="${T.ink}" font-size="11.5" font-weight="700" style="paint-order:stroke;stroke:#FFFFFF;stroke-width:4px;stroke-linejoin:round;">${esc(p.lbl)}</text>
      `;
    }).join("");

    const crossX = sx(135000);
    return `<svg width="1090" height="328" viewBox="0 0 1090 328">
      ${gridY}${gridX}
      <line x1="${crossX.toFixed(1)}" y1="${y0}" x2="${crossX.toFixed(1)}" y2="${y1}" stroke="${T.ochre}" stroke-width="1.3" stroke-dasharray="4,3" />
      <rect x="${(crossX - 92).toFixed(1)}" y="34" width="184" height="24" rx="4" fill="${T.ochreSoft}" stroke="#EBD2AE" />
      <text x="${crossX.toFixed(1)}" y="50" text-anchor="middle" fill="${T.ochre}" font-size="11.2" font-weight="700">128k–152k 现代大模型甜点区</text>
      ${lineFor("pct70", T.stone, "6,4")}
      ${lineFor("flops", T.pine)}
      ${lineFor("pct13", T.vermilion)}
      ${pinsSvg}
      <text x="562" y="322" text-anchor="middle" fill="${T.ink2}" font-size="12" font-weight="600">词表总规模 Vocab Size（千个 Token）</text>
      <text x="16" y="158" text-anchor="middle" fill="${T.ink2}" font-size="12" font-weight="600" transform="rotate(-90 16 158)">参数占比 / 相对算力开销 (%)</text>
    </svg>`;
  })();

  const bodyHtml = `
    <div class="panel-card" style="margin-bottom:16px;">
      <div class="panel-title">A. 算法流派之争：为何 BPE 先合并「了一 / 我在」，WordPiece 却偏爱「公司 / 商店」？</div>
      <div class="panel-sub">BPE 只看共现绝对次数（高频虚字占优）；WordPiece 除以单字频次乘积，优先挑出“彼此唯一绑定”的语义实体</div>
      <div class="legend-row">
        <span class="legend-item"><span class="swatch" style="background:${T.vermilion};"></span>高频虚词搭配</span>
        <span class="legend-item"><span class="swatch" style="background:${T.ochre};"></span>高频量词搭配</span>
        <span class="legend-item"><span class="swatch" style="background:${T.pine};"></span>紧密语义实体</span>
      </div>
      ${pA}
    </div>
    <div class="panel-card">
      <div class="panel-title">B. 词表规模的算力跷跷板：小模型守着 32k，现代大模型扩充到 128k–256k 的数学账</div>
      <div class="panel-sub">在这组对照中，词表越大，中文自注意力开销越低（蓝线），但 1.3B 小模型的词表参数占比越高（陶橘色线）</div>
      <div class="legend-row">
        <span class="legend-item"><span class="swatch" style="background:${T.pine};"></span>中文自注意力 O(N²) 相对算力开销 (%)</span>
        <span class="legend-item"><span class="swatch" style="background:${T.vermilion};"></span>1.3B 小模型词表参数占比 (%)</span>
        <span class="legend-item"><span class="swatch" style="background:${T.stone};"></span>70B 大模型词表参数占比（虚线，仅 0.7%–5.7%）</span>
      </div>
      ${pB}
    </div>
  `;

  return wrapPlate({
    figNum: "FIG. 05",
    epTag: "第 05 期 · 分词算法流派与词表容量权衡",
    title: "大模型分词器设计全景：算法流派偏好与词表规模跷跷板",
    subtitle: "基于 DeepSeek-Coder-1.3B 权重结构与 9 款主流大模型公开词表参数实测对比",
    bodyHtml,
    footerNote: "数据来源：data/algo_comparison_results.csv & data/llm_vocab_landscape.csv",
  });
}

// FIG 6: fig_ep06_tensor_stacking.png (Ep 06)
function buildFigEp06Tensor() {
  const rows = parseCSV("ep06_tensor_45_tokens.csv").map((r) => ({
    pos: +r.pos, tok: r.token, id: +r.token_id, l2: +r.l2_norm, dims: [+r.dim1, +r.dim2, +r.dim3, +r.dim4],
  }));

  const top15 = rows.slice(0, 15);
  const cellW = 86, cellH = 26, x0 = 96, y0 = 32;
  const dimHeaders = ["第1维 (d0)", "第2维 (d1)", "第3维 (d2)", "第4维 (d3)"];
  const cells = top15.map((r, ri) => {
    const y = y0 + ri * cellH;
    const lbl = `${String(r.pos).padStart(2, "0")}:${r.tok}`;
    const rowCells = r.dims.map((v, ci) => {
      const x = x0 + ci * cellW;
      const bg = divergingColor(v, 0.44);
      const tc = Math.abs(v) > 0.27 ? "#FFFFFF" : T.ink;
      return `<rect x="${x}" y="${y}" width="${cellW - 2}" height="${cellH - 2}" rx="2" fill="${bg}" />
              <text x="${x + (cellW - 2) / 2}" y="${y + 16.5}" text-anchor="middle" fill="${tc}" font-size="11.5" font-weight="700" class="t-mono">${v >= 0 ? "+" : ""}${v.toFixed(3)}</text>`;
    }).join("");
    return `<text x="${x0 - 8}" y="${y + 16.5}" text-anchor="end" fill="${T.ink}" font-size="12" font-weight="600" class="t-mono">${esc(lbl)}</text>${rowCells}`;
  }).join("");

  const pASvg = `<svg width="460" height="454" viewBox="0 0 460 454">
    ${dimHeaders.map((h, i) => `<text x="${x0 + i * cellW + (cellW - 2) / 2}" y="20" text-anchor="middle" fill="${T.ink2}" font-size="11.5" font-weight="700">${h}</text>`).join("")}
    ${cells}
    <g transform="translate(96, 428)">
      <defs><linearGradient id="divGrad6" x1="0" x2="1"><stop offset="0%" stop-color="#2B548A"/><stop offset="50%" stop-color="#FAF9F6"/><stop offset="100%" stop-color="#C85A38"/></linearGradient></defs>
      <text x="0" y="12" fill="${T.muted}" font-size="11">负值 -0.45</text>
      <rect x="64" y="2" width="180" height="11" rx="2" fill="url(#divGrad6)" stroke="${T.border}" />
      <text x="252" y="12" fill="${T.muted}" font-size="11">+0.45 正值</text>
    </g>
  </svg>`;

  const pBSvg = (() => {
    const px0 = 52, px1 = 568, py0 = 28, py1 = 380;
    const sx = (p) => px0 + ((p - 1) / 44) * (px1 - px0);
    const sy = (v) => py1 - ((v - 7.3) / (11.8 - 7.3)) * (py1 - py0);

    const gridY = [7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0, 11.5].map((v) => {
      const y = sy(v);
      return `<line x1="${px0}" y1="${y.toFixed(1)}" x2="${px1}" y2="${y.toFixed(1)}" stroke="${T.grid}" />
              <text x="${px0 - 8}" y="${(y + 4).toFixed(1)}" text-anchor="end" fill="${T.muted}" font-size="11" class="t-mono">${v.toFixed(1)}</text>`;
    }).join("");
    const gridX = [1, 5, 10, 15, 20, 25, 30, 35, 40, 45].map((v) => {
      const x = sx(v);
      return `<line x1="${x.toFixed(1)}" y1="${py0}" x2="${x.toFixed(1)}" y2="${py1}" stroke="${T.grid}" />
              <text x="${x.toFixed(1)}" y="${py1 + 18}" text-anchor="middle" fill="${T.muted}" font-size="11" class="t-mono">${v}</text>`;
    }).join("");

    const pts = rows.map((r) => `${sx(r.pos).toFixed(1)},${sy(r.l2).toFixed(1)}`).join(" ");
    const area = `${sx(1).toFixed(1)},${py1} ${pts} ${sx(45).toFixed(1)},${py1}`;
    const dots = rows.map((r) => {
      const hi = r.l2 > 10.2;
      return `<circle cx="${sx(r.pos).toFixed(1)}" cy="${sy(r.l2).toFixed(1)}" r="${hi ? 4.4 : 3.4}" fill="${hi ? T.vermilion : T.pine}" stroke="#fff" stroke-width="1.2" />`;
    }).join("");

    const maxRow = rows.reduce((a, b) => (b.l2 > a.l2 ? b : a), rows[0]);
    const pins = [
      { pos: 1, lx: 108, ly: 356, w: 94, txt: "① 我在 (7.94)" },
      { pos: 6, lx: 215, ly: 356, w: 94, txt: "⑥ 苹果 (8.07)" },
      { pos: 10, lx: 158, ly: 92, w: 92, txt: `⑩ 模 (${rows[9].l2.toFixed(2)})` },
      { pos: 21, lx: 284, ly: 56, w: 90, txt: `㉑ 把 (${rows[20].l2.toFixed(2)})` },
      { pos: maxRow.pos, lx: 438, ly: 42, w: 122, txt: `峰值「${maxRow.tok}」(${maxRow.l2.toFixed(2)})` },
      { pos: 40, lx: 468, ly: 326, w: 92, txt: `㊵ ${rows[39].tok} (${rows[39].l2.toFixed(2)})` },
      { pos: 45, lx: 522, ly: 254, w: 92, txt: `45:${rows[44].tok} (${rows[44].l2.toFixed(2)})` },
    ];
    const pinSvg = pins.map((p) => {
      const r = rows[p.pos - 1];
      const cx = sx(r.pos), cy = sy(r.l2);
      return `
        <line x1="${cx.toFixed(1)}" y1="${cy.toFixed(1)}" x2="${p.lx}" y2="${p.ly}" stroke="${T.ink2}" stroke-width="1" stroke-dasharray="2,2" />
        <rect x="${(p.lx - p.w / 2).toFixed(1)}" y="${p.ly - 11}" width="${p.w}" height="21" rx="4" fill="#fff" fill-opacity="0.95" stroke="${T.border}" />
        <text x="${p.lx}" y="${p.ly + 3}" text-anchor="middle" fill="${T.ink}" font-size="10.8" font-weight="700">${esc(p.txt)}</text>
      `;
    }).join("");

    return `<svg width="585" height="428" viewBox="0 0 585 428">
      ${gridY}${gridX}
      <polygon points="${area}" fill="${T.pineSoft}" fill-opacity="0.7" />
      <polyline points="${pts}" fill="none" stroke="${T.pine}" stroke-width="2.2" />
      ${dots}${pinSvg}
      <text x="310" y="420" text-anchor="middle" fill="${T.ink2}" font-size="12" font-weight="600">Token 序列位置索引（1 ~ 45，共 45 行叠成 [45, 2048] 平面）</text>
      <text x="14" y="204" text-anchor="middle" fill="${T.ink2}" font-size="12" font-weight="600" transform="rotate(-90 14 204)">2048 维语义向量 L2 模长</text>
    </svg>`;
  })();

  const bodyHtml = `
    <div style="display:grid;grid-template-columns:496px 1fr;gap:18px;">
      <div class="panel-card">
        <div class="panel-title">A. 二维张量 [45, 2048] 局部切片（前 15 词 × 前 4 维）</div>
        <div class="panel-sub">每行是 1 个词的 2048 维向量；注意第 02 与第 06 行的「苹果」完全一致</div>
        ${pASvg}
      </div>
      <div class="panel-card">
        <div class="panel-title">B. 45 个 Token 沿序列轴的向量 L2 模长脉动</div>
        <div class="panel-sub">4 句话并行送入 GPU 时，4 张 [45, 2048] 平面叠成 [4, 45, 2048] 三维张量立方体</div>
        <div class="legend-row">
          <span class="legend-item"><span class="swatch-dot" style="background:${T.pine};"></span>常规词元向量模长</span>
          <span class="legend-item"><span class="swatch-dot" style="background:${T.vermilion};"></span>高模长尖峰词元（L2 &gt; 10.2）</span>
        </div>
        ${pBSvg}
      </div>
    </div>
  `;

  return wrapPlate({
    figNum: "FIG. 06",
    epTag: "第 06 期 · 从数字到三维张量魔方",
    title: "45 个 Token 的二维张量真实切片与序列模长分布",
    subtitle: "真机导出 DeepSeek-1.3B 静态查表张量 [45, 2048]：既有正负交错的浮点坐标，也有沿句展开的模长起伏",
    bodyHtml,
    footerNote: "数据来源：data/ep06_tensor_45_tokens.csv（DeepSeek-Coder-1.3B 实测张量切片）",
  });
}

// FIG 7: fig_ep07_geometry_dot_product.png (Ep 07)
function buildFigEp07Geometry() {
  const rows = parseCSV("ep07_dot_product_geometry.csv").map((r) => ({
    label: `${r.w1} — ${r.w2}`, tdot: +r.trained_dot, tcos: +r.trained_cos, tang: +r.trained_angle_deg, rang: +r.random_angle_deg, note: r.note,
  }));

  function tier(r) {
    if (r.note.includes("无关")) return { col: T.stone };
    if (r.tcos >= 0.30) return { col: T.pine };
    return { col: T.ochre };
  }

  const rowH = 38;
  const pA = (() => {
    const x0 = 114, x1 = 482, minA = 50, maxA = 96;
    const sx = (a) => x0 + ((a - minA) / (maxA - minA)) * (x1 - x0);
    const ticks = [50, 60, 70, 80, 90].map((v) => {
      const x = sx(v);
      return `<line x1="${x.toFixed(1)}" y1="8" x2="${x.toFixed(1)}" y2="${18 + rows.length * rowH}" stroke="${v === 90 ? T.vermilion : T.grid}" stroke-dasharray="${v === 90 ? "4,3" : "none"}" stroke-width="${v === 90 ? 1.4 : 0.8}" />
              <text x="${x.toFixed(1)}" y="${36 + rows.length * rowH}" text-anchor="middle" fill="${v === 90 ? T.vermilion : T.muted}" font-size="11.5" font-weight="${v === 90 ? 700 : 500}" class="t-mono">${v}°</text>`;
    }).join("");

    const items = rows.map((r, i) => {
      const y = 28 + i * rowH;
      const xr = sx(r.rang), xt = sx(r.tang);
      const t = tier(r);
      const lblX = Math.min(xr, xt) - 11;
      return `
        <line x1="${x0}" y1="${y}" x2="${x1}" y2="${y}" stroke="${T.grid}" stroke-width="0.7" />
        <text x="${x0 - 10}" y="${y + 4.5}" text-anchor="end" fill="${T.ink}" font-size="13" font-weight="600">${esc(r.label)}</text>
        <line x1="${Math.min(xr, xt).toFixed(1)}" y1="${y}" x2="${Math.max(xr, xt).toFixed(1)}" y2="${y}" stroke="${t.col}" stroke-width="3" stroke-opacity="0.45" />
        <circle cx="${xr.toFixed(1)}" cy="${y}" r="5" fill="${T.stone}" />
        <circle cx="${xt.toFixed(1)}" cy="${y}" r="6" fill="${t.col}" stroke="#fff" stroke-width="1.3" />
        <text x="${lblX.toFixed(1)}" y="${y + 4.5}" text-anchor="end" fill="${t.col}" font-size="12" font-weight="700" class="t-mono">${r.tang.toFixed(1)}°</text>
      `;
    }).join("");

    return `<svg width="505" height="398" viewBox="0 0 505 398">
      ${ticks}${items}
      <text x="298" y="392" text-anchor="middle" fill="${T.ink2}" font-size="12" font-weight="600">2048 维空间几何夹角 θ（度，越小越靠近）</text>
    </svg>`;
  })();

  const pB = (() => {
    const x0 = 16, wMax = 305, maxD = 48;
    const ticks = [0, 10, 20, 30, 40].map((v) => {
      const x = x0 + (v / maxD) * wMax;
      return `<line x1="${x.toFixed(1)}" y1="8" x2="${x.toFixed(1)}" y2="${18 + rows.length * rowH}" stroke="${v === 0 ? T.border : T.grid}" stroke-width="${v === 0 ? 1.2 : 1}" />
              <text x="${x.toFixed(1)}" y="${36 + rows.length * rowH}" text-anchor="middle" fill="${T.muted}" font-size="11.5" class="t-mono">${v}</text>`;
    }).join("");

    const items = rows.map((r, i) => {
      const y = 17 + i * rowH;
      const bw = Math.max(4, (r.tdot / maxD) * wMax);
      const t = tier(r);
      return `
        <rect x="${x0}" y="${y}" width="${bw.toFixed(1)}" height="22" rx="3" fill="${t.col}" />
        <text x="${(x0 + bw + 9).toFixed(1)}" y="${y + 15.5}" fill="${T.ink}" font-size="12" font-weight="700" class="t-mono">+${r.tdot.toFixed(1)} <tspan fill="${T.muted}" font-weight="500">(cos=${r.tcos.toFixed(2)})</tspan></text>
      `;
    }).join("");

    return `<svg width="525" height="398" viewBox="0 0 525 398">
      ${ticks}${items}
      <text x="195" y="392" text-anchor="middle" fill="${T.ink2}" font-size="12" font-weight="600">DeepSeek-1.3B 真实点积得分 (a · b = |a||b|cosθ)</text>
    </svg>`;
  })();

  const bodyHtml = `
    <div class="panel-grid-2">
      <div class="panel-card">
        <div class="panel-title">A. 几何视角：训练让共现词向量夹角 θ 明显缩小</div>
        <div class="panel-sub">虚线表示 90° 正交基线；「苹果—微积分」「吃—二进制」仍停留在近 90°</div>
        <div class="legend-row">
          <span class="legend-item"><span class="swatch-dot" style="background:${T.stone};"></span>训练前（随机正交）</span>
          <span class="legend-item"><span class="swatch-dot" style="background:${T.pine};"></span>强共现语义簇</span>
          <span class="legend-item"><span class="swatch-dot" style="background:${T.ochre};"></span>中度 / 多义关联</span>
        </div>
        ${pA}
      </div>
      <div class="panel-card">
        <div class="panel-title">B. 数学视角：点积得分同时融合向量模长与方向重合度</div>
        <div class="panel-sub">点积是 Transformer 自注意力 Q·K 打分的底层核心算子</div>
        <div class="legend-row">
          <span class="legend-item"><span class="swatch" style="background:${T.pine};"></span>强共现语义簇 (cos ≥ 0.30)</span>
          <span class="legend-item"><span class="swatch" style="background:${T.ochre};"></span>中度 / 多义关联</span>
          <span class="legend-item"><span class="swatch" style="background:${T.stone};"></span>跨界无关基线</span>
        </div>
        ${pB}
      </div>
    </div>
  `;

  return wrapPlate({
    figNum: "FIG. 07",
    epTag: "第 07 期 · 高维空间的拉伸、旋转与点积",
    title: "几何夹角缩小与点积得分实测：预训练如何在空间中“拉近关系”",
    subtitle: "测试 9 组中文词对在 DeepSeek-1.3B 真实 2048 维空间中的夹角演化与点积（a·b）对比",
    bodyHtml,
    footerNote: "数据来源：data/ep07_dot_product_geometry.csv（DeepSeek-Coder-1.3B 词向量实测）",
  });
}

// FIG 8: fig3_layer_evolution.png (Ep 08)
function buildFigLayerEvolution() {
  const ev = MAT.ep08_layer_tracking.layer_evolution.filter((d) => d.layer <= 23);
  const x0 = 64, x1 = 1062;
  const sx = (l) => x0 + (l / 23) * (x1 - x0);

  const pTop = (() => {
    const y0 = 22, y1 = 216;
    const sy = (v) => y1 - ((v - 0.35) / (1.08 - 0.35)) * (y1 - y0);
    const gridY = [0.4, 0.6, 0.8, 1.0].map((v) => {
      const y = sy(v);
      return `<line x1="${x0}" y1="${y.toFixed(1)}" x2="${x1}" y2="${y.toFixed(1)}" stroke="${T.grid}" />
              <text x="${x0 - 10}" y="${(y + 4).toFixed(1)}" text-anchor="end" fill="${T.muted}" font-size="11.5" class="t-mono">${v.toFixed(1)}</text>`;
    }).join("");
    const gridX = [0, 4, 8, 12, 16, 20, 23].map((v) => {
      const x = sx(v);
      return `<line x1="${x.toFixed(1)}" y1="${y0}" x2="${x.toFixed(1)}" y2="${y1}" stroke="${T.grid}" />
              <text x="${x.toFixed(1)}" y="${y1 + 18}" text-anchor="middle" fill="${T.muted}" font-size="11.5" class="t-mono">${v}</text>`;
    }).join("");

    const pts = ev.map((d) => `${sx(d.layer).toFixed(1)},${sy(d.cos).toFixed(1)}`).join(" ");
    const area = `${sx(0)},${y1} ${pts} ${sx(23)},${y1}`;
    const hiLayers = [
      { l: 0, dx: 12, dy: 4, anchor: "start", lbl: "第 0 层：1.000（查静态表，完全相同）", col: T.vermilion },
      { l: 1, dx: 14, dy: 4, anchor: "start", lbl: "第 1 层：0.876（单层注意力即瞬间分开）", col: T.vermilion },
      { l: 8, dx: 10, dy: 22, anchor: "start", lbl: "第 8 层分化最深：0.442（公司 vs 吃 语义剥离）", col: T.pine },
      { l: 23, dx: -12, dy: -16, anchor: "end", lbl: "第 23 层：0.672（汇入高层语法表征）", col: T.vermilion },
    ];
    const marks = hiLayers.map((m) => {
      const d = ev[m.l];
      const cx = sx(d.layer), cy = sy(d.cos);
      return `<circle cx="${cx.toFixed(1)}" cy="${cy.toFixed(1)}" r="5.5" fill="${m.col}" stroke="#fff" stroke-width="1.6" />
              <text x="${(cx + m.dx).toFixed(1)}" y="${(cy + m.dy).toFixed(1)}" text-anchor="${m.anchor}" fill="${m.col}" font-size="12.5" font-weight="700">${esc(m.lbl)}</text>`;
    }).join("");

    return `<svg width="1090" height="248" viewBox="0 0 1090 248">
      ${gridY}${gridX}
      <polygon points="${area}" fill="${T.pineSoft}" fill-opacity="0.65" />
      <polyline points="${pts}" fill="none" stroke="${T.pine}" stroke-width="3" />
      ${marks}
      <text x="18" y="120" text-anchor="middle" fill="${T.ink2}" font-size="12" font-weight="600" transform="rotate(-90 18 120)">Cosine 相似度</text>
    </svg>`;
  })();

  const pBot = (() => {
    const y0 = 20, y1 = 216;
    const sy = (v) => y1 - (v / 96) * (y1 - y0);
    const gridY = [0, 20, 40, 60, 80].map((v) => {
      const y = sy(v);
      return `<line x1="${x0}" y1="${y.toFixed(1)}" x2="${x1}" y2="${y.toFixed(1)}" stroke="${T.grid}" />
              <text x="${x0 - 10}" y="${(y + 4).toFixed(1)}" text-anchor="end" fill="${T.muted}" font-size="11.5" class="t-mono">${v}</text>`;
    }).join("");
    const gridX = [0, 4, 8, 12, 16, 20, 23].map((v) => {
      const x = sx(v);
      return `<line x1="${x.toFixed(1)}" y1="${y0}" x2="${x.toFixed(1)}" y2="${y1}" stroke="${T.grid}" />
              <text x="${x.toFixed(1)}" y="${y1 + 18}" text-anchor="middle" fill="${T.muted}" font-size="11.5" class="t-mono">${v}</text>`;
    }).join("");

    const pts = ev.map((d) => `${sx(d.layer).toFixed(1)},${sy(d.l2).toFixed(1)}`).join(" ");
    const area = `${sx(0)},${y1} ${pts} ${sx(23)},${y1}`;
    const hi = [
      { l: 0, bx: sx(0) + 46, by: sy(0) - 52, w: 92, lbl: "第 0 层：0.0" },
      { l: 1, bx: sx(1) + 92, by: sy(8.2) - 44, w: 92, lbl: "第 1 层：8.2" },
      { l: 12, bx: sx(12) - 10, by: sy(31.7) - 34, w: 102, lbl: "第 12 层：31.7" },
      { l: 23, bx: sx(23) - 118, by: sy(84.9) + 4, w: 204, lbl: "第 23 层：84.9（残差流只增不减）" },
    ];
    const marks = hi.map((m) => {
      const d = ev[m.l];
      const cx = sx(d.layer), cy = sy(d.l2);
      return `<line x1="${cx.toFixed(1)}" y1="${cy.toFixed(1)}" x2="${m.bx.toFixed(1)}" y2="${m.by.toFixed(1)}" stroke="${T.ink2}" stroke-width="1" stroke-dasharray="2,2" />
              <circle cx="${cx.toFixed(1)}" cy="${cy.toFixed(1)}" r="5.5" fill="${T.vermilion}" stroke="#fff" stroke-width="1.6" />
              <rect x="${(m.bx - m.w / 2).toFixed(1)}" y="${(m.by - 12).toFixed(1)}" width="${m.w}" height="22" rx="4" fill="#FFFFFF" fill-opacity="0.96" stroke="${m.l === 23 ? T.vermilion : T.border}" />
              <text x="${m.bx.toFixed(1)}" y="${(m.by + 3.5).toFixed(1)}" text-anchor="middle" fill="${m.l === 23 ? T.vermilion : T.ink}" font-size="11.8" font-weight="700">${esc(m.lbl)}</text>`;
    }).join("");

    return `<svg width="1090" height="262" viewBox="0 0 1090 262">
      ${gridY}${gridX}
      <polygon points="${area}" fill="${T.ochreSoft}" fill-opacity="0.85" />
      <polyline points="${pts}" fill="none" stroke="${T.ochre}" stroke-width="3" />
      ${marks}
      <text x="562" y="256" text-anchor="middle" fill="${T.ink2}" font-size="12" font-weight="600">Transformer 层数（Layer 0 = 静态词表查表 · Layer 1–23 = 逐层残差累加）</text>
      <text x="18" y="118" text-anchor="middle" fill="${T.ink2}" font-size="12" font-weight="600" transform="rotate(-90 18 118)">L2 欧氏距离</text>
    </svg>`;
  })();

  const bodyHtml = `
    <div class="panel-card" style="margin-bottom:16px;">
      <div class="panel-title">A. 方向分化：余弦相似度 cos(苹果₁, 苹果₂) 随层数演变</div>
      <div class="panel-sub">输入「我在苹果公司吃了一个苹果」——两个「苹果」出发时一模一样（1.000），第 1 层即刻分道扬镳</div>
      ${pTop}
    </div>
    <div class="panel-card">
      <div class="panel-title">B. 空间拉开：欧氏距离 L2(苹果₁, 苹果₂) — 残差连接逐层叠加</div>
      <div class="panel-sub">每一层的 ΔAttention 与 ΔMLP 不断写入残差流，两者的欧氏距离从 0.0 一路攀升至 84.9（第 24 层经最终 RMSNorm 缩放回 9.6）</div>
      ${pBot}
    </div>
  `;

  return wrapPlate({
    figNum: "FIG. 08",
    epTag: "第 08 期 · 分层输入输出与语境注入全追踪",
    title: "24 层语境注入追踪：两个“苹果”如何从完全相同走向分道扬镳",
    subtitle: "真机逐层拦截 DeepSeek-1.3B 隐藏状态（Hidden States），实时测量句中两个「苹果」的方向夹角与空间距离",
    bodyHtml,
    footerNote: "数据来源：data/wechat_series_materials.json → ep08_layer_tracking.layer_evolution",
  });
}

// FIG 9: fig_ep09_multihead_dissection.png (Ep 09)
function buildFigEp09Multihead() {
  const all = parseCSV("ep09_all_384_heads.csv").map((r) => ({
    layer: +r.layer, head: +r.head,
    w_wozai: +r.apple2_to_wozai, w_apple1: +r.apple2_to_apple1, w_gongsi: +r.apple2_to_gongsi,
    w_chi: +r.apple2_to_chi, w_leyige: +r.apple2_to_leyige, w_self: +r.apple2_to_self, g_apple1: +r.gongsi_to_apple1,
  }));

  const l1 = all.filter((r) => r.layer === 1).sort((a, b) => a.head - b.head);
  const cols = [
    { k: "w_wozai", lbl: "① 我在" }, { k: "w_apple1", lbl: "② 苹果₁" }, { k: "w_gongsi", lbl: "③ 公司" },
    { k: "w_chi", lbl: "④ 吃" }, { k: "w_leyige", lbl: "⑤ 了一个" }, { k: "w_self", lbl: "⑥ 苹果₂" },
  ];
  const stars = new Set(["8:w_leyige", "10:w_chi", "11:w_gongsi", "7:w_wozai"]);

  const cellW = 72, cellH = 24, hx0 = 76, hy0 = 36;
  const heatRows = l1.map((r, ri) => {
    const y = hy0 + ri * cellH;
    const isStarRow = [8, 10, 11].includes(r.head);
    const cells = cols.map((c, ci) => {
      const v = r[c.k];
      const x = hx0 + ci * cellW;
      const bg = sequentialPine(v / 0.93);
      const tc = v > 0.42 ? "#FFFFFF" : T.ink;
      const star = stars.has(`${r.head}:${c.k}`);
      return `<rect x="${x}" y="${y}" width="${cellW - 2}" height="${cellH - 2}" rx="2.5" fill="${bg}" ${star ? `stroke="${T.vermilion}" stroke-width="2"` : ""} />
              <text x="${x + (cellW - 2) / 2}" y="${y + 15.5}" text-anchor="middle" fill="${tc}" font-size="11.2" font-weight="${v > 0.35 ? 800 : 500}" class="t-mono">${v.toFixed(2)}</text>`;
    }).join("");
    return `<text x="${hx0 - 8}" y="${y + 15.5}" text-anchor="end" fill="${isStarRow ? T.vermilion : T.ink2}" font-size="11.5" font-weight="${isStarRow ? 700 : 600}" class="t-mono">Head ${String(r.head).padStart(2, "0")}</text>${cells}`;
  }).join("");

  const pASvg = `<svg width="525" height="456" viewBox="0 0 525 456">
    ${cols.map((c, i) => `<text x="${hx0 + i * cellW + (cellW - 2) / 2}" y="22" text-anchor="middle" fill="${T.ink}" font-size="11.5" font-weight="700">${c.lbl}</text>`).join("")}
    ${heatRows}
    <g transform="translate(76, 434)">
      <defs><linearGradient id="pineRamp9" x1="0" x2="1"><stop offset="0%" stop-color="#F5F7FB"/><stop offset="50%" stop-color="#6E9BD0"/><stop offset="100%" stop-color="#214678"/></linearGradient></defs>
      <text x="0" y="12" fill="${T.muted}" font-size="11">权重 0.00</text>
      <rect x="60" y="2" width="180" height="11" rx="2" fill="url(#pineRamp9)" stroke="${T.border}" />
      <text x="248" y="12" fill="${T.muted}" font-size="11">0.93 · 描边标出代表性权重</text>
    </g>
  </svg>`;

  const byLayer = Array.from({ length: 24 }, (_, idx) => {
    const l = idx + 1;
    const sub = all.filter((r) => r.layer === l);
    return {
      layer: l,
      gongsi: Math.max(...sub.map((s) => s.g_apple1)),
      chi: Math.max(...sub.map((s) => s.w_chi)),
      apple1: Math.max(...sub.map((s) => s.w_apple1)),
    };
  });

  const pBSvg = (() => {
    const px0 = 52, px1 = 524, py0 = 26, py1 = 384;
    const sx = (l) => px0 + ((l - 1) / 23) * (px1 - px0);
    const sy = (v) => py1 - (v / 1.0) * (py1 - py0);

    const gridY = [0, 0.25, 0.5, 0.75, 1.0].map((v) => {
      const y = sy(v);
      return `<line x1="${px0}" y1="${y.toFixed(1)}" x2="${px1}" y2="${y.toFixed(1)}" stroke="${T.grid}" />
              <text x="${px0 - 8}" y="${(y + 4).toFixed(1)}" text-anchor="end" fill="${T.muted}" font-size="11" class="t-mono">${Math.round(v * 100)}%</text>`;
    }).join("");
    const gridX = [1, 4, 7, 10, 13, 16, 19, 22, 24].map((v) => {
      const x = sx(v);
      return `<line x1="${x.toFixed(1)}" y1="${py0}" x2="${x.toFixed(1)}" y2="${py1}" stroke="${T.grid}" />
              <text x="${x.toFixed(1)}" y="${py1 + 18}" text-anchor="middle" fill="${T.muted}" font-size="11" class="t-mono">${v}</text>`;
    }).join("");

    const series = [{ k: "gongsi", col: T.pine }, { k: "chi", col: T.vermilion }, { k: "apple1", col: T.ochre }];
    const lines = series.map((s) => {
      const poly = byLayer.map((d) => `${sx(d.layer).toFixed(1)},${sy(d[s.k]).toFixed(1)}`).join(" ");
      const dots = byLayer.map((d) => `<circle cx="${sx(d.layer).toFixed(1)}" cy="${sy(d[s.k]).toFixed(1)}" r="3.4" fill="${s.col}" stroke="#fff" stroke-width="1" />`).join("");
      return `<polyline points="${poly}" fill="none" stroke="${s.col}" stroke-width="2.4" />${dots}`;
    }).join("");

    const peakG = byLayer.reduce((a, b) => (b.gongsi > a.gongsi ? b : a), byLayer[0]);
    const peakA = byLayer.reduce((a, b) => (b.apple1 > a.apple1 ? b : a), byLayer[0]);
    const peakC = byLayer.reduce((a, b) => (b.chi > a.chi ? b : a), byLayer[0]);

    const callouts = [
      { x: sx(peakA.layer), y: sy(peakA.apple1), bx: 186, by: 36, w: 132, h: 22, lines: [`L${peakA.layer} 同名比对 ${(peakA.apple1 * 100).toFixed(0)}%`], col: T.ochre },
      { x: sx(peakG.layer), y: sy(peakG.gongsi), bx: 356, by: 68, w: 162, h: 22, lines: [`L${peakG.layer} 专名绑定峰值 ${(peakG.gongsi * 100).toFixed(0)}%`], col: T.pine },
      { x: sx(peakC.layer), y: sy(peakC.chi), bx: 99, by: 353, w: 84, h: 34, lines: [`L${peakC.layer} 动宾锁定`, `${(peakC.chi * 100).toFixed(0)}% (Head 10)`], col: T.vermilion },
    ].map((c) => `
      <line x1="${c.x.toFixed(1)}" y1="${c.y.toFixed(1)}" x2="${c.bx}" y2="${c.by}" stroke="${c.col}" stroke-width="1.1" stroke-dasharray="3,2" />
      <circle cx="${c.x.toFixed(1)}" cy="${c.y.toFixed(1)}" r="5" fill="${c.col}" stroke="#fff" stroke-width="1.5" />
      <rect x="${(c.bx - c.w / 2).toFixed(1)}" y="${(c.by - c.h / 2).toFixed(1)}" width="${c.w}" height="${c.h}" rx="4" fill="#FFFFFF" fill-opacity="0.96" stroke="${c.col}" stroke-width="1" />
      ${c.lines.length === 1
        ? `<text x="${c.bx}" y="${c.by + 3.8}" text-anchor="middle" fill="${c.col}" font-size="11.2" font-weight="700">${esc(c.lines[0])}</text>`
        : `<text x="${c.bx}" y="${c.by - 3}" text-anchor="middle" fill="${c.col}" font-size="11" font-weight="700">${esc(c.lines[0])}</text>
           <text x="${c.bx}" y="${c.by + 11}" text-anchor="middle" fill="${T.ink2}" font-size="10.2" font-weight="600" class="t-mono">${esc(c.lines[1])}</text>`}
    `).join("");

    return `<svg width="540" height="422" viewBox="0 0 540 422">
      <rect x="${px0}" y="${py0}" width="${(sx(4) - px0).toFixed(1)}" height="${py1 - py0}" fill="${T.subcard}" />
      <text x="${((px0 + sx(4)) / 2).toFixed(1)}" y="${py0 + 16}" text-anchor="middle" fill="${T.muted}" font-size="10.5" font-weight="600">浅层 1–4</text>
      ${gridY}${gridX}${lines}${callouts}
      <text x="288" y="416" text-anchor="middle" fill="${T.ink2}" font-size="12" font-weight="600">Transformer 层数（Layer 1 ~ Layer 24）</text>
      <text x="14" y="204" text-anchor="middle" fill="${T.ink2}" font-size="12" font-weight="600" transform="rotate(-90 14 204)">该层 16 头最高注意力权重</text>
    </svg>`;
  })();

  const bodyHtml = `
    <div style="display:grid;grid-template-columns:552px 1fr;gap:18px;">
      <div class="panel-card">
        <div class="panel-title">A. 第 1 层 16 个注意力头实测表：句末「苹果₂」在看谁？</div>
        <div class="panel-sub">Head 11 锁定「公司」(0.93)，Head 10 锁定「吃」(0.60)，Head 08 锁定「了一个」(0.41)</div>
        ${pASvg}
      </div>
      <div class="panel-card">
        <div class="panel-title">B. 1–24 层跨层追踪：三类语义头最高注意力强度</div>
        <div class="panel-sub">浅层完成动宾与同名比对；中层强化实体绑定；深层汇合预测输出</div>
        <div class="legend-row" style="gap:10px;font-size:12px;">
          <span class="legend-item"><span class="swatch-dot" style="background:${T.pine};"></span>专名修饰：公司 → 苹果₁</span>
          <span class="legend-item"><span class="swatch-dot" style="background:${T.vermilion};"></span>动宾锁定：苹果₂ → 吃</span>
          <span class="legend-item"><span class="swatch-dot" style="background:${T.ochre};"></span>同名比对：苹果₂ → 苹果₁</span>
        </div>
        ${pBSvg}
      </div>
    </div>
  `;

  return wrapPlate({
    figNum: "FIG. 09",
    epTag: "第 09 期 · 16 个注意力头真机实操解剖",
    title: "真机解剖「我在苹果公司吃了一个苹果」：16 个注意力头如何各司其职？",
    subtitle: "实测 DeepSeek-1.3B 全部 24 层 × 16 头（共 384 个注意力头），直观呈现多头并行的语义分工网络",
    bodyHtml,
    footerNote: "数据来源：data/ep09_all_384_heads.csv（DeepSeek-Coder-1.3B 全部 384 个注意力头权重实测）",
  });
}

// FIG 10: fig4_context_clusters.png (Ep 11)
function buildFigContextClusters() {
  const cc = MAT.ep11_frozen_inference.context_control_disambig;
  const labels = cc.details.map((d) => d.label);
  const m0 = cc.cos_matrices["0"];
  const m23 = cc.cos_matrices["23"];

  function heatMap(mat, xOff, title, sub, highlightClusters) {
    const cs = 76, x0 = xOff + 94, y0 = 66;
    let out = `<text x="${x0 + cs * 2}" y="22" text-anchor="middle" fill="${T.ink}" font-size="15" font-weight="700">${esc(title)}</text>
               <text x="${x0 + cs * 2}" y="42" text-anchor="middle" fill="${T.muted}" font-size="12">${esc(sub)}</text>`;
    for (let r = 0; r < 4; r++) {
      out += `<text x="${x0 - 10}" y="${y0 + r * cs + cs / 2 + 5}" text-anchor="end" fill="${T.ink}" font-size="12.5" font-weight="700">${esc(labels[r])}</text>`;
      out += `<text x="${x0 + r * cs + cs / 2}" y="${y0 + 4 * cs + 22}" text-anchor="middle" fill="${T.ink}" font-size="12" font-weight="700">${esc(labels[r])}</text>`;
      for (let c = 0; c < 4; c++) {
        const v = mat[r][c];
        const t = (v - 0.38) / (1.0 - 0.38);
        const bg = sequentialPine(t);
        const tc = v >= 0.72 ? "#FFFFFF" : T.ink;
        out += `<rect x="${x0 + c * cs + 2}" y="${y0 + r * cs + 2}" width="${cs - 4}" height="${cs - 4}" rx="4" fill="${bg}" />
                <text x="${x0 + c * cs + cs / 2}" y="${y0 + r * cs + cs / 2 + 5}" text-anchor="middle" fill="${tc}" font-size="14" font-weight="800" class="t-mono">${v.toFixed(2)}</text>`;
      }
    }
    if (highlightClusters) {
      out += `<rect x="${x0}" y="${y0}" width="${cs * 2}" height="${cs * 2}" rx="6" fill="none" stroke="${T.ochre}" stroke-width="2.5" stroke-dasharray="5,3" />
              <rect x="${x0 + cs * 2}" y="${y0 + cs * 2}" width="${cs * 2}" height="${cs * 2}" rx="6" fill="none" stroke="${T.vermilion}" stroke-width="2.5" stroke-dasharray="5,3" />
              <text x="${x0 + cs}" y="${y0 - 6}" text-anchor="middle" fill="${T.ochre}" font-size="11.5" font-weight="700">数码语境簇 (0.57)</text>
              <text x="${x0 + cs * 3}" y="${y0 + cs * 2 - 6}" text-anchor="middle" fill="${T.vermilion}" font-size="11.5" font-weight="700">水果语境簇 (0.88)</text>`;
    }
    return out;
  }

  const nextCards = cc.details.map((d, idx) => {
    const top1 = d.next_top5[0];
    const isTech = idx < 2;
    return `<div style="padding:10px 12px;background:${isTech ? T.ochreSoft : T.pineSoft};border-left:3px solid ${isTech ? T.ochre : T.pine};border-radius:4px;">
      <div style="font-size:11.5px;font-weight:700;color:${isTech ? T.ochre : T.pine};margin-bottom:3px;">${esc(d.label)}</div>
      <div style="font-size:12.5px;color:${T.ink};margin-bottom:4px;">「${esc(d.sentence)}」</div>
      <div class="mono" style="font-size:11.5px;color:${T.ink2};">续写 Top-1：<strong>「${esc(top1.token)}」</strong>（${(top1.prob * 100).toFixed(1)}%）</div>
    </div>`;
  }).join("");

  const bodyHtml = `
    <div class="panel-card" style="margin-bottom:16px;">
      <svg width="1090" height="408" viewBox="0 0 1090 408">
        ${heatMap(m0, 10, "第 0 层：静态词表查表（100% 相同）", "权重完全冻结，4 句句尾「苹果」查出同一行向量", false)}
        <g transform="translate(460, 198)">
          <line x1="0" y1="0" x2="54" y2="0" stroke="${T.ink}" stroke-width="2" />
          <polygon points="54,-6 66,0 54,6" fill="${T.ink}" />
          <text x="30" y="-12" text-anchor="middle" fill="${T.ink2}" font-size="11.5" font-weight="700">23 层</text>
          <text x="30" y="20" text-anchor="middle" fill="${T.muted}" font-size="11">语境注入</text>
        </g>
        ${heatMap(m23, 520, "第 23 层：融入上文自然分簇", "水果两句紧聚 0.88，跨语义跌至 0.43", true)}
        <g transform="translate(970, 74)">
          <defs><linearGradient id="cb10" x1="0" y1="1" x2="0" y2="0"><stop offset="0%" stop-color="#F5F7FB"/><stop offset="50%" stop-color="#6E9BD0"/><stop offset="100%" stop-color="#214678"/></linearGradient></defs>
          <rect x="0" y="0" width="16" height="288" rx="3" fill="url(#cb10)" stroke="${T.border}" />
          ${[1.0, 0.8, 0.6, 0.4].map((v, i) => `<text x="24" y="${i * 94 + 8}" fill="${T.muted}" font-size="11.5" class="t-mono">${v.toFixed(1)}</text>`).join("")}
          <text x="8" y="-12" text-anchor="middle" fill="${T.ink2}" font-size="11.5" font-weight="700">Cosine</text>
        </g>
      </svg>
    </div>
    <div style="display:grid;grid-template-columns:repeat(4, 1fr);gap:12px;">
      ${nextCards}
    </div>
  `;

  return wrapPlate({
    figNum: "FIG. 10",
    epTag: "第 14 期 · 冻结权重下的动态语境消歧",
    title: "同一个词「苹果 (id=17144)」放句尾：只换前文，向量自动分簇",
    subtitle: "推理期间 13.46 亿参数纹丝不动（SHA-256 哈希 100% 校验一致），上下文通过注意力动态重塑向量方向",
    bodyHtml,
    footerNote: "数据来源：data/wechat_series_materials.json → ep11_frozen_inference.context_control_disambig",
  });
}

// FIG 11: fig5_hallucination_entropy.png (Ep 12)
function buildFigHallucination() {
  const probes = MAT.ep12_finale.hallucination_probe;
  const x0 = 330, wMax = 382, maxE = 6.2;

  const rowsSvg = probes.map((p, i) => {
    const isTrue = p.kind === "真事实";
    const y = (i >= 2 ? 44 : 18) + i * 62;
    const bw = (p.entropy / maxE) * wMax;
    const col = isTrue ? T.pine : T.vermilion;
    const top1 = p.top5[0];
    const promptDisp = p.prompt.length > 18 ? p.prompt.slice(0, 18) + "…" : p.prompt + "…";
    const badge = isTrue
      ? `高把握接「${top1.token}」(${Math.round(top1.prob * 100)}%)`
      : `没底仍强行接「${top1.token}」(${Math.round(top1.prob * 100)}%)`;

    return `
      ${i === 2 ? `
        <line x1="16" y1="${y - 24}" x2="1074" y2="${y - 24}" stroke="${T.border}" stroke-dasharray="5,4" />
        <rect x="${x0}" y="${y - 34}" width="184" height="20" rx="10" fill="${T.vermilionSoft}" />
        <text x="${x0 + 92}" y="${y - 20}" text-anchor="middle" fill="${T.vermilion}" font-size="11" font-weight="700">以下为假前提 / 虚构实体测试</text>
      ` : ""}
      <text x="${x0 - 14}" y="${y + 17}" text-anchor="end" fill="${T.ink}" font-size="13.8" font-weight="700">${esc(promptDisp)}</text>
      <text x="${x0 - 14}" y="${y + 34}" text-anchor="end" fill="${T.muted}" font-size="11.5">${esc(p.kind)}</text>
      <rect x="${x0}" y="${y + 4}" width="${bw.toFixed(1)}" height="32" rx="4" fill="${col}" />
      <text x="${(x0 + bw + 12).toFixed(1)}" y="${y + 25}" fill="${T.ink}" font-size="13.2" font-weight="800" class="t-mono">熵 ${p.entropy.toFixed(2)} <tspan fill="${col}" font-weight="700" font-size="12.5">｜ ${esc(badge)}</tspan></text>
    `;
  }).join("");

  const ticks = [0, 1, 2, 3, 4, 5, 6].map((v) => {
    const x = x0 + (v / maxE) * wMax;
    return `<line x1="${x.toFixed(1)}" y1="8" x2="${x.toFixed(1)}" y2="354" stroke="${v === 0 ? T.border : T.grid}" stroke-width="${v === 0 ? 1.2 : 1}" />
            <text x="${x.toFixed(1)}" y="372" text-anchor="middle" fill="${T.muted}" font-size="12" class="t-mono">${v}</text>`;
  }).join("");

  const bodyHtml = `
    <div class="panel-card">
      <div class="legend-row" style="justify-content:space-between;margin-bottom:12px;">
        <div style="display:flex;gap:18px;">
          <span class="legend-item"><span class="swatch" style="background:${T.pine};"></span>真实前提（低熵 · 概率集中于正确答案）</span>
          <span class="legend-item"><span class="swatch" style="background:${T.vermilion};"></span>假前提 / 虚构实体（高熵 · 概率分散但仍被迫续写）</span>
        </div>
        <span class="mono" style="font-size:12px;color:${T.muted};">H = -∑ p log p (nats)</span>
      </div>
      <svg width="1090" height="396" viewBox="0 0 1090 396">
        ${ticks}
        ${rowsSvg}
        <text x="${x0 + wMax / 2}" y="392" text-anchor="middle" fill="${T.ink2}" font-size="12.5" font-weight="600">下一步预测不确定度：信息熵 Entropy (nats，越高越“心里没底”)</text>
      </svg>
    </div>
  `;

  return wrapPlate({
    figNum: "FIG. 11",
    epTag: "第 15 期 · 大结局：概率采样与幻觉的数学本质",
    title: "心里越没底（信息熵越高），大模型照样顺着语法硬往下接",
    subtitle: "32,256 个词表里没有「我不知道」——面对荒谬前提，预测分布急剧扁平化，但采样机制仍逼迫模型挑出下一个词",
    bodyHtml,
    footerNote: "数据来源：data/wechat_series_materials.json → ep12_finale.hallucination_probe（DeepSeek-1.3B 实测）",
  });
}

function findChrome() {
  const candidates = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
  ];
  for (const c of candidates) if (fs.existsSync(c)) return c;
  throw new Error("No local Chrome/Chromium/Edge binary found.");
}

async function launchChrome() {
  const chromePath = findChrome();
  const userDataDir = fs.mkdtempSync(path.join(os.tmpdir(), "oil-fig-chrome-"));
  const proc = spawn(chromePath, [
    "--headless=new",
    "--disable-gpu",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--remote-debugging-port=0",
    "--user-data-dir=" + userDataDir,
    "about:blank",
  ], { stdio: ["ignore", "pipe", "pipe"] });

  const wsUrl = await new Promise((resolve, reject) => {
    let buf = "";
    const timer = setTimeout(() => reject(new Error("Chrome CDP timeout: " + buf)), 15000);
    proc.stderr.on("data", (chunk) => {
      buf += chunk.toString();
      const m = buf.match(/DevTools listening on (ws:\/\/[^\s]+)/);
      if (m) { clearTimeout(timer); resolve(m[1]); }
    });
    proc.on("exit", (code) => { clearTimeout(timer); reject(new Error("Chrome exited early: " + code)); });
  });

  const httpBase = wsUrl.replace(/^ws:/, "http:").replace(/\/devtools\/browser\/.*/, "");
  const targets = await (await fetch(httpBase + "/json/list")).json();
  const pageTarget = targets.find((t) => t.type === "page") || targets[0];
  const ws = new WebSocket(pageTarget.webSocketDebuggerUrl);
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });

  let seq = 0;
  const pending = new Map();
  ws.onmessage = (ev) => {
    const msg = JSON.parse(ev.data);
    if (msg.id && pending.has(msg.id)) {
      const { resolve, reject } = pending.get(msg.id);
      pending.delete(msg.id);
      if (msg.error) reject(new Error(msg.error.message));
      else resolve(msg.result);
    }
  };

  const send = (method, params = {}) => new Promise((resolve, reject) => {
    const id = ++seq;
    pending.set(id, { resolve, reject });
    ws.send(JSON.stringify({ id, method, params }));
  });

  await send("Page.enable");
  await send("Runtime.enable");

  return {
    send,
    async close() {
      try { ws.close(); } catch {}
      const exited = new Promise((r) => proc.once("exit", r));
      try { proc.kill("SIGTERM"); } catch {}
      await Promise.race([exited, new Promise((r) => setTimeout(r, 1500))]);
      try { fs.rmSync(userDataDir, { recursive: true, force: true, maxRetries: 5, retryDelay: 100 }); } catch {}
    },
  };
}

async function renderPlateToPng(cdp, htmlContent, outFile, width = 1200) {
  const tmpHtml = path.join(os.tmpdir(), "plate_" + Date.now() + "_" + Math.random().toString(36).slice(2) + ".html");
  fs.writeFileSync(tmpHtml, htmlContent, "utf8");
  try {
    await cdp.send("Emulation.setDeviceMetricsOverride", { width, height: 1600, deviceScaleFactor: 2, mobile: false });
    await cdp.send("Page.navigate", { url: "file://" + tmpHtml });
    await new Promise((r) => setTimeout(r, 220));
    const { result } = await cdp.send("Runtime.evaluate", {
      expression: "JSON.stringify(document.getElementById('plate').getBoundingClientRect())",
      returnByValue: true,
    });
    const rect = JSON.parse(result.value);
    const h = Math.ceil(rect.height);
    await cdp.send("Emulation.setDeviceMetricsOverride", { width, height: h, deviceScaleFactor: 2, mobile: false });
    await new Promise((r) => setTimeout(r, 80));
    const shot = await cdp.send("Page.captureScreenshot", {
      format: "png",
      clip: { x: 0, y: 0, width, height: h, scale: 1 },
    });
    fs.writeFileSync(outFile, Buffer.from(shot.data, "base64"));
    return { file: path.basename(outFile), w: width * 2, h: h * 2 };
  } finally {
    fs.rmSync(tmpHtml, { force: true });
  }
}

const FIGURES = [
  ["fig2_param_budget.png", buildFigParamBudget],
  ["fig1_random_vs_trained.png", buildFigRandomVsTrained],
  ["deepseek_token_anatomy.png", buildFigTokenAnatomy],
  ["bpe_merging_process.png", buildFigBpeProcess],
  ["tokenizer_design_tradeoffs.png", buildFigTokenizerTradeoffs],
  ["fig_ep06_tensor_stacking.png", buildFigEp06Tensor],
  ["fig_ep07_geometry_dot_product.png", buildFigEp07Geometry],
  ["fig3_layer_evolution.png", buildFigLayerEvolution],
  ["fig_ep09_multihead_dissection.png", buildFigEp09Multihead],
  ["fig4_context_clusters.png", buildFigContextClusters],
  ["fig5_hallucination_entropy.png", buildFigHallucination],
];

async function main() {
  const cdp = await launchChrome();
  try {
    const results = [];
    const filters = process.argv.slice(2);
    const targets = filters.length ? FIGURES.filter(([f]) => filters.some((k) => f.includes(k))) : FIGURES;
    for (const [filename, builder] of targets) {
      const htmlStr = builder();
      const info = await renderPlateToPng(cdp, htmlStr, path.join(ASSETS_DIR, filename), 1200);
      results.push(info);
      console.log("[OK] " + info.file.padEnd(36) + " " + info.w + "x" + info.h);
    }
    console.log("[DONE] Rendered " + results.length + " editorial figures to " + ASSETS_DIR);
  } finally {
    await cdp.close();
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
