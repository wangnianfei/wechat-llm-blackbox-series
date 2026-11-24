#!/usr/bin/env python3
"""
WeChat Official Account HTML Typesetting & Portal Builder for:
《掀开大模型的黑盒子》（全 12 期硬核科普连载）

Converts /Users/wangnianfei/w2v_lab/wechat_articles/markdown/ep01.md .. ep12.md
into:
1. /Users/wangnianfei/w2v_lab/wechat_articles/html/ep01.html .. ep12.html
   (Standalone WeChat-styled HTML articles with inline CSS ready for mp.weixin.qq.com)
2. /Users/wangnianfei/w2v_lab/wechat_articles/index.html
   (All-in-one interactive WeChat Official Account preview & one-click copy portal)
"""
import html
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent
ART_DIR = ROOT / "wechat_articles"
MD_DIR = ART_DIR / "markdown"
HTML_DIR = ART_DIR / "html"
HTML_DIR.mkdir(parents=True, exist_ok=True)

EPISODE_META = [
    {"ep": 1,  "part": "第一部分：破除黑盒与底层基石", "tag": "总体观篇", "color": "#2563eb"},
    {"ep": 2,  "part": "第一部分：破除黑盒与底层基石", "tag": "学习方法论特辑", "color": "#0d9488"},
    {"ep": 3,  "part": "第二部分：从二进制到 Token 诞生", "tag": "进制与编码篇", "color": "#4f46e5"},
    {"ep": 4,  "part": "第二部分：从二进制到 Token 诞生", "tag": "Token 诞生记·上", "color": "#d97706"},
    {"ep": 5,  "part": "第二部分：从二进制到 Token 诞生", "tag": "Token 诞生记·下", "color": "#ea580c"},
    {"ep": 6,  "part": "第三部分：张量与几何空间表示语义", "tag": "张量专题篇", "color": "#0284c7"},
    {"ep": 7,  "part": "第三部分：张量与几何空间表示语义", "tag": "几何与点积篇", "color": "#0f766e"},
    {"ep": 8,  "part": "第四部分：分层解剖 Transformer", "tag": "分层学习与注意力篇", "color": "#7c3aed"},
    {"ep": 9,  "part": "第四部分：分层解剖 Transformer", "tag": "多头注意力真机实操篇", "color": "#dc2626"},
    {"ep": 10, "part": "第五部分：训练与推理的终极闭环", "tag": "训练过程篇", "color": "#059669"},
    {"ep": 11, "part": "第五部分：训练与推理的终极闭环", "tag": "训练 vs 推理对比篇", "color": "#1d4ed8"},
    {"ep": 12, "part": "第五部分：训练与推理的终极闭环", "tag": "大结局·全景贯通篇", "color": "#b91c1c"},
]

def format_inline(text: str, accent: str = "#2563eb", asset_prefix: str = "../assets/") -> str:
    """Convert inline Markdown (images, links, bold, code, inline math) to WeChat inline-styled HTML."""
    # 1. Inline image: ![alt](src)
    def repl_img(m):
        alt = html.escape(m.group(1))
        src = m.group(2).strip()
        if src.startswith("../assets/"):
            src = asset_prefix + src[len("../assets/"):]
        elif src.startswith("assets/"):
            src = asset_prefix + src[len("assets/"):]
        return (
            f'<figure style="margin:22px 0;text-align:center;">'
            f'<img src="{src}" alt="{alt}" style="width:100%;max-width:100%;height:auto;border-radius:10px;'
            f'border:1px solid #e2e8f0;box-shadow:0 4px 14px rgba(15,23,42,0.06);display:block;margin:0 auto;" />'
            f'<figcaption style="margin-top:8px;font-size:12.5px;color:#64748b;line-height:1.5;">'
            f'▲ 图：{alt}</figcaption></figure>'
        )
    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', repl_img, text)

    # 2. Inline code `...`
    def repl_code(m):
        c = html.escape(m.group(1))
        return (
            f'<code style="font-family:\'JetBrains Mono\',Menlo,Consolas,monospace;font-size:13.5px;'
            f'background-color:#f1f5f9;color:#0f172a;padding:2px 6px;border-radius:4px;'
            f'border:1px solid #e2e8f0;margin:0 2px;">{c}</code>'
        )
    text = re.sub(r'`([^`]+)`', repl_code, text)

    # 3. Inline LaTeX math $...$ -> clean readable typographic math
    def repl_math(m):
        expr = m.group(1).strip()
        expr = (
            expr.replace(r"\rightarrow", "→")
            .replace(r"\to", "→")
            .replace(r"\leftrightarrow", "↔")
            .replace(r"\times", "×")
            .replace(r"\cdot", "·")
            .replace(r"\theta", "θ")
            .replace(r"\approx", "≈")
            .replace(r"\neq", "≠")
            .replace(r"\leq", "≤")
            .replace(r"\geq", "≥")
            .replace(r"\infty", "∞")
            .replace(r"\ln", "ln")
            .replace(r"\cos", "cos")
            .replace(r"\arccos", "arccos")
            .replace(r"\sum", "∑")
        )
        expr = re.sub(r'\\vec\{([^}]+)\}', r'\1⃗', expr)
        expr = re.sub(r'\\text\{([^}]+)\}', r'\1', expr)
        expr = re.sub(r'_\{([^}]+)\}', r'<sub>\1</sub>', expr)
        expr = re.sub(r'_([a-zA-Z0-9])', r'<sub>\1</sub>', expr)
        expr = re.sub(r'\^\{([^}]+)\}', r'<sup>\1</sup>', expr)
        expr = re.sub(r'\^([a-zA-Z0-9\+\-]+)', r'<sup>\1</sup>', expr)
        return (
            f'<span style="font-family:\'Cambria Math\',\'Times New Roman\',serif;font-style:italic;'
            f'color:#0f172a;background:#f8fafc;padding:1px 5px;border-radius:4px;">{expr}</span>'
        )
    text = re.sub(r'\$([^$\n]+)\$', repl_math, text)

    # 4. Links [label](url)
    def repl_link(m):
        lbl = m.group(1)
        url = m.group(2).strip()
        return (
            f'<a href="{url}" target="_blank" style="color:{accent};text-decoration:none;'
            f'border-bottom:1px dashed {accent};font-weight:500;">{lbl}</a> '
            f'<span style="font-size:12px;color:#64748b;word-break:break-all;">({url})</span>'
        )
    text = re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)', repl_link, text)

    # 5. Bold **...**
    text = re.sub(
        r'\*\*([^\n*]+?)\*\*',
        rf'<strong style="color:#0f172a;font-weight:700;background:linear-gradient(180deg,transparent 65%,{accent}22 0);padding:0 2px;">\1</strong>',
        text
    )
    # 6. Italic *...*
    text = re.sub(r'\*([^*]+)\*', r'<em style="color:#334155;">\1</em>', text)
    return text


def md_to_wechat_html(md_text: str, meta: dict, asset_prefix: str = "../assets/") -> dict:
    """Parse Episode Markdown into WeChat-compatible inline-CSS HTML and return metadata."""
    accent = meta["color"]
    ep_num = meta["ep"]
    part_name = meta["part"]
    tag_name = meta["tag"]

    # Extract raw Chinese char count for reading time metrics
    plain_for_count = re.sub(r'<svg[\s\S]*?</svg>', '', md_text)
    plain_for_count = re.sub(r'[#>*`|_\-\[\]\(\)!]', '', plain_for_count)
    cjk_chars = len(re.findall(r'[\u4e00-\u9fff]', plain_for_count))
    read_mins = max(7, round(cjk_chars / 260))

    # Extract H1 title
    title = f"第 {ep_num} 期"
    lines = md_text.splitlines()
    body_lines = []
    for ln in lines:
        if ln.startswith("# ") and title == f"第 {ep_num} 期":
            title = ln[2:].strip()
        else:
            body_lines.append(ln)

    text = "\n".join(body_lines)

    # Protect inline <svg>...</svg> blocks from line splitting
    svg_blocks = []
    def save_svg(m):
        idx = len(svg_blocks)
        svg_html = m.group(0)
        wrapper = (
            f'<section style="margin:22px 0;padding:14px 12px;background:#f8fafc;'
            f'border:1px solid #e2e8f0;border-radius:12px;text-align:center;overflow-x:auto;">'
            f'{svg_html}'
            f'</section>'
        )
        svg_blocks.append(wrapper)
        return f"\n@@SVG_BLOCK_{idx}@@\n"

    text = re.sub(r'<svg[\s\S]*?</svg>', save_svg, text)

    # Protect fenced code blocks ```...```
    code_blocks = []
    def save_code(m):
        idx = len(code_blocks)
        lang = (m.group(1) or "code").strip()
        code_raw = html.escape(m.group(2).strip())
        box = (
            f'<section style="margin:18px 0;border-radius:10px;overflow:hidden;border:1px solid #1e293b;'
            f'background:#0f172a;box-shadow:0 4px 12px rgba(15,23,42,0.12);">'
            f'<div style="background:#1e293b;padding:6px 14px;font-size:12px;color:#94a3b8;'
            f'display:flex;align-items:center;justify-content:space-between;font-family:monospace;">'
            f'<span>● ● ● &nbsp; {lang}</span><span>DeepSeek 1.3B 实操代码</span></div>'
            f'<pre style="margin:0;padding:14px 16px;overflow-x:auto;font-family:\'JetBrains Mono\',Menlo,Consolas,monospace;'
            f'font-size:13px;line-height:1.65;color:#e2e8f0;white-space:pre;">{code_raw}</pre></section>'
        )
        code_blocks.append(box)
        return f"\n@@CODE_BLOCK_{idx}@@\n"

    text = re.sub(r'```([a-zA-Z0-9_\-]*)\n([\s\S]*?)```', save_code, text)

    # Now parse line by line into structured blocks
    out_html = []

    # Top WeChat Series Masthead Card
    masthead = f"""
    <section style="margin-bottom:24px;border-radius:14px;overflow:hidden;border:1px solid #e2e8f0;background:linear-gradient(135deg,#0f172a 0%,#1e293b 100%);color:#ffffff;padding:22px 20px;box-shadow:0 8px 24px rgba(15,23,42,0.12);">
      <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;margin-bottom:12px;">
        <span style="display:inline-block;background:{accent};color:#ffffff;font-size:12px;font-weight:700;padding:3px 10px;border-radius:999px;letter-spacing:0.5px;">《掀开大模型的黑盒子》第 {ep_num:02d}/12 期 · {tag_name}</span>
        <span style="font-size:12px;color:#94a3b8;">{part_name}</span>
      </div>
      <h1 style="margin:0 0 12px 0;font-size:21px;line-height:1.45;font-weight:800;color:#ffffff;letter-spacing:0.3px;">{html.escape(title)}</h1>
      <div style="display:flex;align-items:center;gap:16px;font-size:12.5px;color:#cbd5e1;border-top:1px solid rgba(255,255,255,0.12);padding-top:10px;">
        <span>✍️ 作者：AI 硬核科普实验室</span>
        <span>⏱️ 预计阅读：{read_mins} 分钟（{cjk_chars} 字）</span>
        <span>🔬 实验底座：DeepSeek-1.3B 真机实测</span>
      </div>
    </section>
    """
    out_html.append(masthead.strip())

    raw_lines = text.splitlines()
    i = 0
    n = len(raw_lines)
    current_section_mode = "normal"  # "normal", "keypoints", "story", "hook", "resources"

    while i < n:
        ln = raw_lines[i].strip()
        if not ln:
            i += 1
            continue

        # Placeholder restoration
        m_svg = re.match(r'^@@SVG_BLOCK_(\d+)@@$', ln)
        if m_svg:
            out_html.append(svg_blocks[int(m_svg.group(1))])
            i += 1
            continue

        m_code = re.match(r'^@@CODE_BLOCK_(\d+)@@$', ln)
        if m_code:
            out_html.append(code_blocks[int(m_code.group(1))])
            i += 1
            continue

        # Horizontal rule
        if re.match(r'^-{3,}$', ln) or re.match(r'^\*{3,}$', ln):
            out_html.append('<hr style="border:none;border-top:1px dashed #cbd5e1;margin:24px 0;" />')
            i += 1
            continue

        # H2 Heading
        if ln.startswith("## "):
            h2_text = ln[3:].strip()
            # Check special section modes
            if "本节核心要点" in h2_text or "核心要点" in h2_text:
                current_section_mode = "keypoints"
                # Collect all bullets/paragraphs until next ## heading
                i += 1
                kp_items = []
                while i < n and not raw_lines[i].strip().startswith("## "):
                    s = raw_lines[i].strip()
                    if s and not re.match(r'^-{3,}$', s):
                        s_clean = re.sub(r'^[\-\*\+]\s+', '', s)
                        s_clean = re.sub(r'^\d+\.\s+', '', s_clean)
                        kp_items.append(format_inline(s_clean, accent, asset_prefix))
                    i += 1
                li_html = "".join(
                    f'<li style="margin:8px 0;line-height:1.75;color:#1e293b;font-size:14.5px;">{item}</li>'
                    for item in kp_items
                )
                card = (
                    f'<section style="margin:20px 0 26px 0;padding:18px 18px 14px 18px;background:linear-gradient(180deg,#eff6ff 0%,#f8fafc 100%);'
                    f'border-left:5px solid {accent};border-radius:10px;border-top:1px solid #dbeafe;border-right:1px solid #dbeafe;border-bottom:1px solid #dbeafe;">'
                    f'<div style="font-size:15.5px;font-weight:800;color:{accent};margin-bottom:10px;display:flex;align-items:center;gap:6px;">'
                    f'<span>💡 本期核心要点（1分钟先抓主干）</span></div>'
                    f'<ul style="margin:0;padding-left:20px;">{li_html}</ul></section>'
                )
                out_html.append(card)
                current_section_mode = "normal"
                continue

            elif "科学史故事" in h2_text or "故事栏" in h2_text:
                current_section_mode = "story"
                story_title = re.sub(r'^.*?科学史故事栏[：:\s]*', '', h2_text).strip() or h2_text
                i += 1
                story_paras = []
                while i < n and not raw_lines[i].strip().startswith("## "):
                    s = raw_lines[i].strip()
                    if s and not re.match(r'^-{3,}$', s):
                        story_paras.append(f'<p style="margin:10px 0;font-size:14.8px;line-height:1.85;color:#334155;text-align:justify;">{format_inline(s, accent, asset_prefix)}</p>')
                    i += 1
                card = (
                    f'<section style="margin:28px 0;padding:20px 18px;background:linear-gradient(135deg,#fffbeb 0%,#fef3c7 100%);'
                    f'border:1px solid #fcd34d;border-radius:12px;box-shadow:0 4px 14px rgba(217,119,6,0.08);">'
                    f'<div style="display:inline-block;background:#d97706;color:#ffffff;font-size:12px;font-weight:700;padding:2px 10px;border-radius:999px;margin-bottom:8px;">📜 科学史故事专栏</div>'
                    f'<h3 style="margin:4px 0 12px 0;font-size:17px;font-weight:800;color:#92400e;">{html.escape(story_title)}</h3>'
                    f'{"".join(story_paras)}</section>'
                )
                out_html.append(card)
                current_section_mode = "normal"
                continue

            elif "下期悬念" in h2_text or "毕业挑战" in h2_text:
                current_section_mode = "hook"
                i += 1
                hook_paras = []
                while i < n and not raw_lines[i].strip().startswith("## "):
                    s = raw_lines[i].strip()
                    if s and not re.match(r'^-{3,}$', s):
                        s_clean = re.sub(r'^>\s*', '', s)
                        hook_paras.append(f'<p style="margin:10px 0;font-size:15px;line-height:1.8;color:#1e1b4b;">{format_inline(s_clean, "#4f46e5", asset_prefix)}</p>')
                    i += 1
                card = (
                    f'<section style="margin:26px 0;padding:18px 18px;background:linear-gradient(135deg,#eef2ff 0%,#e0e7ff 100%);'
                    f'border:1px solid #a5b4fc;border-left:5px solid #4f46e5;border-radius:10px;">'
                    f'<div style="font-size:15.5px;font-weight:800;color:#4338ca;margin-bottom:8px;">🔮 {html.escape(h2_text.replace("🔮", "").strip())}</div>'
                    f'{"".join(hook_paras)}</section>'
                )
                out_html.append(card)
                current_section_mode = "normal"
                continue

            elif "拓展资源" in h2_text:
                current_section_mode = "resources"
                i += 1
                res_items = []
                while i < n and not raw_lines[i].strip().startswith("## "):
                    s = raw_lines[i].strip()
                    if s and not re.match(r'^-{3,}$', s):
                        s_clean = re.sub(r'^[\-\*\+]\s+', '', s)
                        s_clean = re.sub(r'^\d+\.\s+', '', s_clean)
                        res_items.append(f'<li style="margin:8px 0;font-size:13.8px;line-height:1.75;color:#334155;">{format_inline(s_clean, accent, asset_prefix)}</li>')
                    i += 1
                card = (
                    f'<section style="margin:26px 0 12px 0;padding:16px 18px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;">'
                    f'<div style="font-size:15px;font-weight:800;color:#0f172a;margin-bottom:8px;">🔗 拓展资源加油站（课后动手实验室）</div>'
                    f'<ol style="margin:0;padding-left:20px;">{"".join(res_items)}</ol></section>'
                )
                out_html.append(card)
                current_section_mode = "normal"
                continue

            else:
                # Standard Section H2
                out_html.append(
                    f'<h2 style="margin:30px 0 14px 0;padding-bottom:8px;border-bottom:2px solid {accent};'
                    f'font-size:18px;font-weight:800;color:#0f172a;display:flex;align-items:center;gap:8px;">'
                    f'<span style="display:inline-block;width:8px;height:18px;background:{accent};border-radius:3px;"></span>'
                    f'<span>{format_inline(h2_text, accent, asset_prefix)}</span></h2>'
                )
                i += 1
                continue

        # H3 Heading
        if ln.startswith("### "):
            h3_text = ln[4:].strip()
            out_html.append(
                f'<h3 style="margin:20px 0 10px 0;font-size:16px;font-weight:700;color:#1e293b;'
                f'padding-left:10px;border-left:3px solid {accent};">{format_inline(h3_text, accent, asset_prefix)}</h3>'
            )
            i += 1
            continue

        # Blockquote (> ...)
        if ln.startswith(">"):
            bq_lines = []
            while i < n and raw_lines[i].strip().startswith(">"):
                s = re.sub(r'^>\s?', '', raw_lines[i].strip())
                if s:
                    bq_lines.append(format_inline(s, accent, asset_prefix))
                i += 1
            bq_joined = "<br/>".join(bq_lines)
            if "底层思想" in bq_joined:
                out_html.append(
                    f'<section style="margin:18px 0;padding:15px 16px;background:linear-gradient(135deg,#f0fdf4 0%,#dcfce7 100%);'
                    f'border:1px solid #86efac;border-left:5px solid #16a34a;border-radius:10px;font-size:14.5px;line-height:1.8;color:#14532d;">'
                    f'{bq_joined}</section>'
                )
            else:
                out_html.append(
                    f'<blockquote style="margin:16px 0;padding:12px 16px;background:#f8fafc;border-left:4px solid #64748b;'
                    f'border-radius:6px;font-size:14.5px;line-height:1.75;color:#475569;">{bq_joined}</blockquote>'
                )
            continue

        # Markdown Table
        if ln.startswith("|") and i + 1 < n and re.match(r'^\|\s*[:\-]+', raw_lines[i + 1].strip()):
            headers = [c.strip() for c in ln.strip("|").split("|")]
            i += 2  # skip separator row
            rows = []
            while i < n and raw_lines[i].strip().startswith("|"):
                r_cells = [c.strip() for c in raw_lines[i].strip().strip("|").split("|")]
                rows.append(r_cells)
                i += 1
            th_html = "".join(
                f'<th style="padding:9px 10px;background:{accent};color:#ffffff;font-weight:700;font-size:12.5px;'
                f'text-align:left;border:1px solid #cbd5e1;white-space:nowrap;">{format_inline(h, accent, asset_prefix)}</th>'
                for h in headers
            )
            tr_html = []
            for r_idx, r in enumerate(rows):
                bg = "#ffffff" if r_idx % 2 == 0 else "#f8fafc"
                tds = "".join(
                    f'<td style="padding:8px 10px;border:1px solid #e2e8f0;font-size:12.8px;line-height:1.55;color:#1e293b;background:{bg};">'
                    f'{format_inline(c, accent, asset_prefix)}</td>'
                    for c in r
                )
                tr_html.append(f"<tr>{tds}</tr>")
            table_block = (
                f'<section style="margin:18px 0;overflow-x:auto;border-radius:8px;border:1px solid #cbd5e1;'
                f'box-shadow:0 2px 8px rgba(15,23,42,0.04);">'
                f'<table style="width:100%;border-collapse:collapse;font-size:12.8px;">'
                f'<thead><tr>{th_html}</tr></thead><tbody>{"".join(tr_html)}</tbody></table></section>'
            )
            out_html.append(table_block)
            continue

        # Unordered or Ordered List
        if re.match(r'^([\-\*\+]|\d+\.)\s+', ln):
            is_ordered = bool(re.match(r'^\d+\.\s+', ln))
            tag = "ol" if is_ordered else "ul"
            items = []
            while i < n and re.match(r'^([\-\*\+]|\d+\.)\s+', raw_lines[i].strip()):
                s = re.sub(r'^([\-\*\+]|\d+\.)\s+', '', raw_lines[i].strip())
                items.append(f'<li style="margin:7px 0;font-size:15px;line-height:1.8;color:#1e293b;">{format_inline(s, accent, asset_prefix)}</li>')
                i += 1
            out_html.append(f'<{tag} style="margin:12px 0;padding-left:22px;">{"".join(items)}</{tag}>')
            continue

        # Standalone Image line
        if re.match(r'^!\[[^\]]*\]\([^)]+\)$', ln):
            out_html.append(format_inline(ln, accent, asset_prefix))
            i += 1
            continue

        # Standard paragraph
        out_html.append(
            f'<p style="margin:14px 0;font-size:15.5px;line-height:1.85;color:#1e293b;letter-spacing:0.3px;text-align:justify;">'
            f'{format_inline(ln, accent, asset_prefix)}</p>'
        )
        i += 1

    # Footer Signature Card
    footer = f"""
    <section style="margin-top:30px;padding:16px 18px;background:#0f172a;color:#cbd5e1;border-radius:10px;font-size:12.5px;line-height:1.7;text-align:center;">
      <div style="font-weight:700;color:#ffffff;font-size:13.5px;margin-bottom:4px;">《掀开大模型的黑盒子》全 12 期硬核科普连载</div>
      <div>数据与真机实验基于本地开源模型 <code style="color:#38bdf8;">deepseek-coder-1.3b-base</code> (32,256 词表 · 24 层 · 13.46 亿参数) 实测生成</div>
    </section>
    """
    out_html.append(footer.strip())

    wechat_inner_html = (
        f'<section id="wechat-article-body" style="max-width:677px;margin:0 auto;padding:24px 20px;'
        f'background:#ffffff;font-family:-apple-system,BlinkMacSystemFont,\'PingFang SC\',\'Hiragino Sans GB\','
        f'\'Microsoft YaHei\',sans-serif;color:#1e293b;box-sizing:border-box;">\n'
        + "\n".join(out_html)
        + "\n</section>"
    )

    return {
        "ep": ep_num,
        "title": title,
        "part": part_name,
        "tag": tag_name,
        "color": accent,
        "cjk_chars": cjk_chars,
        "read_mins": read_mins,
        "wechat_html": wechat_inner_html,
    }


def write_standalone_episode_html(ep_data: dict):
    ep = ep_data["ep"]
    prev_link = f'<a href="ep{ep-1:02d}.html" class="nav-btn">← 上一期 (第{ep-1}期)</a>' if ep > 1 else '<span></span>'
    next_link = f'<a href="ep{ep+1:02d}.html" class="nav-btn">下一期 (第{ep+1}期) →</a>' if ep < 12 else '<span></span>'

    page = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{html.escape(ep_data["title"])} - 微信公众号排版预览</title>
<style>
  body {{
    margin: 0;
    padding: 0;
    background: #e2e8f0;
    font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif;
  }}
  .toolbar {{
    position: sticky;
    top: 0;
    z-index: 100;
    background: #0f172a;
    color: #fff;
    padding: 10px 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.2);
  }}
  .toolbar-left, .toolbar-right {{
    display: flex;
    align-items: center;
    gap: 10px;
  }}
  .btn {{
    background: #2563eb;
    color: #fff;
    border: none;
    padding: 7px 14px;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    text-decoration: none;
  }}
  .btn:hover {{ background: #1d4ed8; }}
  .btn-copy {{ background: #16a34a; }}
  .btn-copy:hover {{ background: #15803d; }}
  .btn-outline {{
    background: transparent;
    border: 1px solid #475569;
    color: #e2e8f0;
  }}
  .preview-shell {{
    margin: 24px auto;
    max-width: 677px;
    background: #fff;
    border-radius: 12px;
    box-shadow: 0 12px 32px rgba(15,23,42,0.12);
    overflow: hidden;
    transition: max-width 0.25s ease;
  }}
  .preview-shell.mobile {{
    max-width: 390px;
    border: 10px solid #1e293b;
    border-radius: 32px;
  }}
  .bottom-nav {{
    max-width: 677px;
    margin: 0 auto 40px auto;
    display: flex;
    justify-content: space-between;
    padding: 0 12px;
  }}
  .nav-btn {{
    background: #fff;
    color: #0f172a;
    padding: 10px 16px;
    border-radius: 8px;
    text-decoration: none;
    font-size: 13.5px;
    font-weight: 600;
    box-shadow: 0 2px 6px rgba(0,0,0,0.08);
  }}
</style>
</head>
<body>
  <div class="toolbar">
    <div class="toolbar-left">
      <a href="../index.html" class="btn btn-outline">📚 返回全12期总览工作台</a>
      <span style="font-size:13px;color:#cbd5e1;">第 {ep:02d}/12 期 · {ep_data["cjk_chars"]} 字 · 约 {ep_data["read_mins"]} 分钟</span>
    </div>
    <div class="toolbar-right">
      <button class="btn btn-outline" onclick="toggleWidth()">📱 切换手机(390px) / 电脑(677px)视野</button>
      <button class="btn btn-copy" id="copyBtn" onclick="copyWeChat()">📋 一键复制公众号富文本排版</button>
    </div>
  </div>

  <div class="preview-shell" id="shell">
    {ep_data["wechat_html"]}
  </div>

  <div class="bottom-nav">
    {prev_link}
    {next_link}
  </div>

<script>
function toggleWidth() {{
  document.getElementById('shell').classList.toggle('mobile');
}}
function copyWeChat() {{
  const node = document.getElementById('wechat-article-body');
  const range = document.createRange();
  range.selectNode(node);
  const sel = window.getSelection();
  sel.removeAllRanges();
  sel.addRange(range);
  document.execCommand('copy');
  sel.removeAllRanges();
  const btn = document.getElementById('copyBtn');
  btn.textContent = '✅ 已复制！可直接粘贴到微信公众号后台';
  setTimeout(() => {{ btn.textContent = '📋 一键复制公众号富文本排版'; }}, 3000);
}}
</script>
</body>
</html>"""
    (HTML_DIR / f"ep{ep:02d}.html").write_text(page, encoding="utf-8")


def write_master_portal(all_eps: list):
    total_chars = sum(x["cjk_chars"] for x in all_eps)
    sidebar_items = []
    for x in all_eps:
        ep = x["ep"]
        sidebar_items.append(f"""
        <div class="ep-item {'active' if ep == 1 else ''}" id="nav-ep-{ep}" onclick="selectEp({ep})">
          <div class="ep-badge" style="background:{x['color']};">第 {ep:02d} 期 · {x['tag']}</div>
          <div class="ep-title">{html.escape(x['title'])}</div>
          <div class="ep-meta">{x['cjk_chars']} 字 · 约 {x['read_mins']} 分钟 · <a href="html/ep{ep:02d}.html" target="_blank" onclick="event.stopPropagation();" style="color:#38bdf8;">独立页 ↗</a></div>
        </div>
        """)

    # Re-render each episode with asset_prefix="assets/" for the root index.html portal
    portal_articles = []
    for meta in EPISODE_META:
        md_file = MD_DIR / f"ep{meta['ep']:02d}.md"
        if md_file.exists():
            d = md_to_wechat_html(md_file.read_text(encoding="utf-8"), meta, asset_prefix="assets/")
            disp = "block" if meta["ep"] == 1 else "none"
            portal_articles.append(f'<div class="ep-pane" id="pane-ep-{meta["ep"]}" style="display:{disp};">{d["wechat_html"]}</div>')

    portal_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>《掀开大模型的黑盒子》全 12 期微信公众号推文排版工作台</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    padding: 0;
    background: #0f172a;
    color: #f8fafc;
    font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif;
    display: flex;
    height: 100vh;
    overflow: hidden;
  }}
  .sidebar {{
    width: 350px;
    background: #1e293b;
    border-right: 1px solid #334155;
    display: flex;
    flex-direction: column;
    height: 100vh;
    flex-shrink: 0;
  }}
  .sidebar-header {{
    padding: 18px 16px;
    background: #0f172a;
    border-bottom: 1px solid #334155;
  }}
  .sidebar-header h1 {{
    margin: 0 0 6px 0;
    font-size: 16.5px;
    color: #ffffff;
  }}
  .sidebar-header p {{
    margin: 0;
    font-size: 12px;
    color: #94a3b8;
    line-height: 1.5;
  }}
  .ep-list {{
    flex: 1;
    overflow-y: auto;
    padding: 10px;
  }}
  .ep-item {{
    padding: 12px;
    border-radius: 10px;
    margin-bottom: 8px;
    cursor: pointer;
    background: rgba(255,255,255,0.03);
    border: 1px solid transparent;
    transition: all 0.15s ease;
  }}
  .ep-item:hover {{
    background: rgba(255,255,255,0.07);
  }}
  .ep-item.active {{
    background: rgba(37,99,235,0.18);
    border-color: #3b82f6;
  }}
  .ep-badge {{
    display: inline-block;
    font-size: 11px;
    font-weight: 700;
    color: #fff;
    padding: 2px 8px;
    border-radius: 999px;
    margin-bottom: 6px;
  }}
  .ep-title {{
    font-size: 13.2px;
    font-weight: 600;
    color: #f1f5f9;
    line-height: 1.45;
    margin-bottom: 5px;
  }}
  .ep-meta {{
    font-size: 11.5px;
    color: #94a3b8;
  }}
  .main-stage {{
    flex: 1;
    display: flex;
    flex-direction: column;
    height: 100vh;
    background: #cbd5e1;
  }}
  .stage-toolbar {{
    background: #0f172a;
    padding: 12px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 1px solid #334155;
  }}
  .btn {{
    background: #2563eb;
    color: #fff;
    border: none;
    padding: 8px 15px;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
  }}
  .btn-copy {{ background: #16a34a; }}
  .btn-copy:hover {{ background: #15803d; }}
  .btn-mode {{ background: #334155; }}
  .stage-scroll {{
    flex: 1;
    overflow-y: auto;
    padding: 28px 16px 60px 16px;
  }}
  .wechat-frame {{
    max-width: 677px;
    margin: 0 auto;
    background: #ffffff;
    border-radius: 12px;
    box-shadow: 0 16px 40px rgba(15,23,42,0.22);
    overflow: hidden;
    transition: max-width 0.25s ease;
  }}
  .wechat-frame.mobile {{
    max-width: 390px;
    border: 12px solid #0f172a;
    border-radius: 36px;
  }}
</style>
</head>
<body>
  <aside class="sidebar">
    <div class="sidebar-header">
      <h1>📦 《掀开大模型的黑盒子》</h1>
      <p>微信公众号全 12 期连载排版工作台<br/>共 {len(all_eps)} 期 · 累计 {total_chars:,} 字 · DeepSeek-1.3B 实测</p>
    </div>
    <div class="ep-list">
      {"".join(sidebar_items)}
    </div>
  </aside>

  <main class="main-stage">
    <div class="stage-toolbar">
      <div style="font-size:13.5px;color:#e2e8f0;">
        当前预览：<strong id="cur-ep-label" style="color:#38bdf8;">第 01 期</strong>
        <span style="margin-left:10px;font-size:12px;color:#94a3b8;">(所有样式均已内联化，支持直接粘贴至微信公众号后台)</span>
      </div>
      <div style="display:flex;gap:10px;">
        <button class="btn btn-mode" onclick="toggleMobile()">📱 切换手机(390px) / 公众号标准宽(677px)</button>
        <button class="btn btn-copy" id="copyBtn" onclick="copyCurrentEp()">📋 一键复制当前期公众号排版</button>
      </div>
    </div>
    <div class="stage-scroll" id="stageScroll">
      <div class="wechat-frame" id="wechatFrame">
        {"".join(portal_articles)}
      </div>
    </div>
  </main>

<script>
let currentEp = 1;
function selectEp(ep) {{
  currentEp = ep;
  document.querySelectorAll('.ep-item').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.ep-pane').forEach(el => el.style.display = 'none');
  document.getElementById('nav-ep-' + ep).classList.add('active');
  document.getElementById('pane-ep-' + ep).style.display = 'block';
  document.getElementById('cur-ep-label').textContent = '第 ' + String(ep).padStart(2, '0') + ' 期';
  document.getElementById('stageScroll').scrollTop = 0;
}}
function toggleMobile() {{
  document.getElementById('wechatFrame').classList.toggle('mobile');
}}
function copyCurrentEp() {{
  const pane = document.getElementById('pane-ep-' + currentEp);
  const range = document.createRange();
  range.selectNode(pane);
  const sel = window.getSelection();
  sel.removeAllRanges();
  sel.addRange(range);
  document.execCommand('copy');
  sel.removeAllRanges();
  const btn = document.getElementById('copyBtn');
  btn.textContent = '✅ 已复制第 ' + currentEp + ' 期！可直接粘贴到公众号后台';
  setTimeout(() => {{ btn.textContent = '📋 一键复制当前期公众号排版'; }}, 3000);
}}
</script>
</body>
</html>"""
    (ART_DIR / "index.html").write_text(portal_html, encoding="utf-8")


def main():
    all_eps = []
    for meta in EPISODE_META:
        ep = meta["ep"]
        md_file = MD_DIR / f"ep{ep:02d}.md"
        if not md_file.exists():
            print(f"[WARN] Missing {md_file}")
            continue
        md_text = md_file.read_text(encoding="utf-8")
        ep_data = md_to_wechat_html(md_text, meta, asset_prefix="../assets/")
        write_standalone_episode_html(ep_data)
        all_eps.append(ep_data)
        print(f"[OK] Built html/ep{ep:02d}.html ({ep_data['cjk_chars']} Chinese chars, ~{ep_data['read_mins']} min) - {ep_data['title']}")

    if all_eps:
        write_master_portal(all_eps)
        print(f"[DONE] Built master portal at {ART_DIR / 'index.html'} with {len(all_eps)} episodes.")


if __name__ == "__main__":
    main()
