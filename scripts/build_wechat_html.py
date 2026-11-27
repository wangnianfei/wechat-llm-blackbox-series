#!/usr/bin/env python3
"""
WeChat Official Account HTML Typesetting & Editorial Workbench Builder for:
《掀开大模型的黑盒子》（全 15 期硬核科普连载）

Design System: Warm-Tech Ceramic Optical Lab (「晨光瓷感 · 光学实验室」)
Harmonized with scripts/render_editorial_figures.mjs
Outputs:
1. html/ep01.html .. html/ep15.html
   (Standalone WeChat-styled HTML articles with inline CSS ready for mp.weixin.qq.com)
2. index.html
   (All-in-one editorial preview & one-click WeChat copy workbench)
"""
import html
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
MD_DIR = ROOT / "markdown"
HTML_DIR = ROOT / "html"
HTML_DIR.mkdir(parents=True, exist_ok=True)

# Warm-Tech Ceramic Optical Lab design tokens
PAPER_BG = "#FFFEFC"
PAPER_TINT = "#F7F5F0"
PAPER_WARM = "#F3EFE8"
PAPER_TECH = "#F0F5FC"
PAPER_SUN = "#FDF6EE"
INK = "#18202C"
INK_BODY = "#2B3544"
INK_SUB = "#475569"
INK_MUTE = "#556173"
LINE = "#E5E0D6"
LINE_SOFT = "#EFECE4"
INDIGO = "#2B548A"
INDIGO_HOVER = "#1F416E"
INDIGO_MID = "#4C82C2"
TERRACOTTA = "#B04A22"
WARM_GLOW = "#E08B5A"

FONT_SERIF = "'Source Han Serif SC','Noto Serif SC','Songti SC','STSong',Georgia,serif"
FONT_SANS = "-apple-system,BlinkMacSystemFont,'PingFang SC','Hiragino Sans GB','Noto Sans SC','Microsoft YaHei',sans-serif"
FONT_MONO = "'JetBrains Mono','SF Mono',Menlo,Consolas,monospace"
FONT_MATH = "Georgia,'Cambria Math','Times New Roman',serif"

# Six harmonious warm-tech optical accents (one per Part — luminous, warm, legible)
PART_PALETTE = {
    1: {"roman": "PART I",   "accent": "#2B548A", "glow": "#4C82C2", "soft": "#F0F5FC", "border": "#CFE0F5"},
    2: {"roman": "PART II",  "accent": "#B04A22", "glow": "#DC7F4F", "soft": "#FDF4EC", "border": "#F2D5BE"},
    3: {"roman": "PART III", "accent": "#196473", "glow": "#3D92A3", "soft": "#EEF7F9", "border": "#C7E4EA"},
    4: {"roman": "PART IV",  "accent": "#564787", "glow": "#8271B8", "soft": "#F3F1FA", "border": "#D9D2EE"},
    5: {"roman": "PART V",   "accent": "#2E6F5E", "glow": "#4F9A86", "soft": "#EEF7F4", "border": "#C5E3DA"},
    6: {"roman": "PART VI",  "accent": "#A83E35", "glow": "#D67065", "soft": "#FCF1F0", "border": "#F0CFCB"},
}

EPISODE_META = [
    {"ep": 1,  "part_no": 1, "part": "第一部分：破除黑盒与底层基石",   "tag": "总体观篇"},
    {"ep": 2,  "part_no": 1, "part": "第一部分：破除黑盒与底层基石",   "tag": "学习方法论特辑"},
    {"ep": 3,  "part_no": 2, "part": "第二部分：从二进制到 Token 诞生", "tag": "进制与编码篇"},
    {"ep": 4,  "part_no": 2, "part": "第二部分：从二进制到 Token 诞生", "tag": "Token 诞生记·上"},
    {"ep": 5,  "part_no": 2, "part": "第二部分：从二进制到 Token 诞生", "tag": "Token 诞生记·下"},
    {"ep": 6,  "part_no": 3, "part": "第三部分：张量与几何空间表示语义", "tag": "张量专题篇"},
    {"ep": 7,  "part_no": 3, "part": "第三部分：张量与几何空间表示语义", "tag": "几何与点积篇"},
    {"ep": 8,  "part_no": 4, "part": "第四部分：分层解剖 Transformer",  "tag": "分层学习与注意力篇"},
    {"ep": 9,  "part_no": 4, "part": "第四部分：分层解剖 Transformer",  "tag": "多头注意力实操篇"},
    {"ep": 10, "part_no": 5, "part": "第五部分：FFN 知识库与激活函数本质", "tag": "FFN 升维提炼篇"},
    {"ep": 11, "part_no": 5, "part": "第五部分：FFN 知识库与激活函数本质", "tag": "激活函数本质篇"},
    {"ep": 12, "part_no": 6, "part": "第六部分：训练、梯度进化与终极闭环", "tag": "训练过程篇"},
    {"ep": 13, "part_no": 6, "part": "第六部分：训练、梯度进化与终极闭环", "tag": "梯度与激活进化篇"},
    {"ep": 14, "part_no": 6, "part": "第六部分：训练、梯度进化与终极闭环", "tag": "训练 vs 推理对比篇"},
    {"ep": 15, "part_no": 6, "part": "第六部分：训练、梯度进化与终极闭环", "tag": "大结局·全景贯通篇"},
]

TOTAL_EPS = len(EPISODE_META)

for _m in EPISODE_META:
    _p = PART_PALETTE[_m["part_no"]]
    _m["roman"] = _p["roman"]
    _m["color"] = _p["accent"]
    _m["glow"] = _p["glow"]
    _m["soft"] = _p["soft"]
    _m["border"] = _p["border"]

INTERACTIVE_DEMOS = [
    {
        "id": "activation-221",
        "code": "LAB 01",
        "title": "2→2→1 神经网络激活函数直观演示",
        "desc": "有 vs 无激活对比 · 空间折弯 · XOR 实时训练",
        "href": "demos/activation-221.html",
        "accent": "#564787",
        "soft": "#F3F1FA",
        "search": "lab 01 激活函数 activation relu sigmoid silu gelu tanh xor ffn 神经网络 交互 演示 2-2-1",
    },
]


# =============================================================================
# 1. Brace-Aware LaTeX -> WeChat-Safe Editorial HTML Math Renderer
# =============================================================================

MATH_SYMBOLS = {
    "rightarrow": "→",
    "to": "→",
    "leftrightarrow": "↔",
    "times": "×",
    "cdot": "·",
    "odot": "⊙",
    "div": "÷",
    "approx": "≈",
    "propto": "∝",
    "neq": "≠",
    "leq": "≤",
    "geq": "≥",
    "infty": "∞",
    "theta": "θ",
    "sigma": "σ",
    "Phi": "Φ",
    "alpha": "α",
    "beta": "β",
    "epsilon": "ε",
    "partial": "∂",
    "cdots": "⋯",
    "dots": "…",
    "sim": "~",
    "nabla": "∇",
    "circ": "°",
    "quad": "&emsp;",
    "qquad": "&emsp;&emsp;",
    "big": "",
    "Big": "",
}

UPRIGHT_FUNCS = {"cos", "sin", "tan", "tanh", "arccos", "arcsin", "ln", "log", "exp", "max", "min", "softmax"}


def _read_braced(s: str, pos: int) -> tuple[str, int]:
    """Read a { ... } balanced group starting at pos, or a single token if not '{'."""
    n = len(s)
    while pos < n and s[pos] == " ":
        pos += 1
    if pos >= n:
        return "", pos
    if s[pos] == "{":
        depth = 1
        i = pos + 1
        while i < n and depth > 0:
            if s[i] == "\\" and i + 1 < n:
                i += 2
                continue
            if s[i] == "{":
                depth += 1
            elif s[i] == "}":
                depth -= 1
            i += 1
        return s[pos + 1 : i - 1], i
    if s[pos] == "\\":
        j = pos + 1
        while j < n and s[j].isalpha():
            j += 1
        if j == pos + 1 and j < n:
            j += 1
        return s[pos:j], j
    return s[pos], pos + 1


def render_latex_to_html(expr: str, display: bool = False) -> str:
    """Recursively convert LaTeX math subset into crisp WeChat-compatible HTML."""
    s = expr.strip()
    # Normalize degree notation before ^ parsing
    s = re.sub(r"\^\{\s*\\circ\s*\}", "°", s)
    s = re.sub(r"\^\\circ\b", "°", s)

    out: list[str] = []
    i = 0
    n = len(s)

    while i < n:
        ch = s[i]

        # Backslash commands
        if ch == "\\":
            if i + 1 < n and not s[i + 1].isalpha():
                nxt = s[i + 1]
                if nxt == "%":
                    out.append("%")
                elif nxt == " ":
                    out.append("&nbsp;")
                elif nxt == ",":
                    out.append("&thinsp;")
                else:
                    out.append(html.escape(nxt))
                i += 2
                continue

            j = i + 1
            while j < n and s[j].isalpha():
                j += 1
            cmd = s[i + 1 : j]
            i = j

            if cmd == "frac":
                num_raw, i = _read_braced(s, i)
                den_raw, i = _read_braced(s, i)
                num_h = render_latex_to_html(num_raw, display=False)
                den_h = render_latex_to_html(den_raw, display=False)
                if display:
                    out.append(
                        f'<span style="display:inline-block;vertical-align:middle;text-align:center;'
                        f'margin:0 5px;line-height:1.25;">'
                        f'<span style="display:block;padding:0 8px 3px 8px;border-bottom:1.2px solid {INK};">{num_h}</span>'
                        f'<span style="display:block;padding:3px 8px 0 8px;">{den_h}</span></span>'
                    )
                else:
                    out.append(
                        f'<span style="display:inline-block;vertical-align:middle;text-align:center;'
                        f'margin:0 3px;font-size:0.86em;line-height:1.18;">'
                        f'<span style="display:block;padding:0 4px 1px 4px;border-bottom:1px solid {INK};">{num_h}</span>'
                        f'<span style="display:block;padding:1px 4px 0 4px;">{den_h}</span></span>'
                    )
                continue

            if cmd == "sqrt":
                arg_raw, i = _read_braced(s, i)
                arg_h = render_latex_to_html(arg_raw, display=False)
                out.append(
                    f'<span style="font-style:normal;">√</span>'
                    f'<span style="border-top:1px solid {INK};padding:0 2px;font-style:normal;">{arg_h}</span>'
                )
                continue

            if cmd == "text":
                arg_raw, i = _read_braced(s, i)
                out.append(
                    f'<span style="font-style:normal;font-family:{FONT_SANS};font-size:0.92em;">'
                    f'{html.escape(arg_raw)}</span>'
                )
                continue

            if cmd == "mathbf":
                arg_raw, i = _read_braced(s, i)
                arg_h = render_latex_to_html(arg_raw, display=False)
                out.append(f'<strong style="font-style:normal;font-weight:700;color:{INK};">{arg_h}</strong>')
                continue

            if cmd == "vec":
                arg_raw, i = _read_braced(s, i)
                arg_h = render_latex_to_html(arg_raw, display=False)
                out.append(f'<strong style="font-style:italic;font-weight:700;color:{INK};">{arg_h}</strong>')
                continue

            if cmd == "sum":
                sz = "1.28em" if display else "1.12em"
                out.append(f'<span style="font-style:normal;font-size:{sz};vertical-align:-0.05em;">∑</span>')
                continue

            if cmd in UPRIGHT_FUNCS:
                need_sp = i < n and (s[i].isalpha() or s[i] == "\\")
                sp = "&thinsp;" if need_sp else ""
                out.append(f'<span style="font-style:normal;">{cmd}</span>{sp}')
                continue

            if cmd in MATH_SYMBOLS:
                sym = MATH_SYMBOLS[cmd]
                if cmd in ("rightarrow", "to", "leftrightarrow", "times", "cdot", "odot", "div", "approx", "propto", "neq", "leq", "geq", "sim"):
                    out.append(f'<span style="font-style:normal;"> {sym} </span>')
                elif sym:
                    out.append(f'<span style="font-style:normal;">{sym}</span>')
                continue

            out.append(html.escape(cmd))
            continue

        # Subscript
        if ch == "_":
            sub_raw, i = _read_braced(s, i + 1)
            sub_h = render_latex_to_html(sub_raw, display=False)
            out.append(f'<sub style="font-size:0.80em;line-height:0;vertical-align:-0.22em;">{sub_h}</sub>')
            continue

        # Superscript
        if ch == "^":
            sup_raw, i = _read_braced(s, i + 1)
            sup_h = render_latex_to_html(sup_raw, display=False)
            out.append(f'<sup style="font-size:0.80em;line-height:0;vertical-align:0.38em;">{sup_h}</sup>')
            continue

        # Stray grouping braces
        if ch in "{}":
            i += 1
            continue

        # Minus sign as typographic minus
        if ch == "-":
            out.append("−")
            i += 1
            continue

        # Numbers & punctuation upright; ASCII letters italic via parent math font
        if ch.isdigit() or ch in "()[],.:;=+|/°%":
            out.append(f'<span style="font-style:normal;">{html.escape(ch)}</span>')
            i += 1
            continue

        out.append(html.escape(ch))
        i += 1

    rendered = "".join(out)
    rendered = re.sub(r" {2,}", " ", rendered)
    return rendered


# =============================================================================
# 2. Inline SVG Palette Harmonizer (Warm-Tech Ceramic Optical Lab)
# =============================================================================

SVG_COLOR_MAP = {
    # Neutral light backgrounds -> warm porcelain & ceramic mist
    "#f8fafc": "#FAF9F6",
    "#f1f5f9": "#F2F5FA",
    "#ffffff": "#FFFEFC",
    "#fff":    "#FFFEFC",
    # Borders & muted rules
    "#cbd5e1": "#D8D4CA",
    "#e2e8f0": "#E7E3DA",
    "#94a3b8": "#6C798C",
    # Neutral inks -> deep obsidian-indigo & calm slate
    "#0f172a": "#18202C",
    "#1e293b": "#2B3544",
    "#334155": "#3B4759",
    "#475569": "#475569",
    "#64748b": "#556173",
    # Blues -> luminous optical indigo scale
    "#eff6ff": "#F0F5FC",
    "#dbeafe": "#DCE9F9",
    "#e0f2fe": "#EAF4FA",
    "#bfdbfe": "#BDD7F3",
    "#93c5fd": "#8CB7E8",
    "#60a5fa": "#588FD1",
    "#3b82f6": "#396EB0",
    "#2563eb": "#2B548A",
    "#1d4ed8": "#234778",
    "#1e40af": "#1F416E",
    "#1e3a8a": "#19355B",
    "#0284c7": "#1D6880",
    "#0369a1": "#17556B",
    "#0ea5e9": "#2E7F99",
    "#38bdf8": "#59A3BA",
    # Emerald / teal -> optical clear cyan-teal
    "#ecfdf5": "#EEF7F8",
    "#f0fdf4": "#EFF8F8",
    "#d1fae5": "#D4ECEF",
    "#dcfce7": "#D8EEF0",
    "#a7f3d0": "#A9DAE0",
    "#6ee7b7": "#77C2CC",
    "#34d399": "#46A1AE",
    "#10b981": "#267E8D",
    "#059669": "#1D6D7B",
    "#16a34a": "#237380",
    "#15803d": "#1A5F6C",
    "#047857": "#196473",
    "#065f46": "#14505C",
    "#14532d": "#124651",
    "#166534": "#175763",
    "#4ade80": "#5AAFB9",
    "#0d9488": "#1D6E7C",
    "#0f766e": "#175A67",
    "#f0fdfa": "#EEF7F9",
    "#ccfbf1": "#D3ECEF",
    "#99f6e4": "#A6D9DF",
    "#5eead4": "#6EC0C9",
    "#2dd4bf": "#3E9CA8",
    # Amber / yellow -> warm sunrise apricot-amber
    "#fffbeb": "#FDF7EE",
    "#fefce8": "#FCF5E8",
    "#fef3c7": "#F8E9D2",
    "#fde68a": "#F1D4A9",
    "#fcd34d": "#E8BD80",
    "#fbbf24": "#DEA356",
    "#f59e0b": "#C8812D",
    "#d97706": "#B26B1F",
    "#b45309": "#985517",
    "#92400e": "#7C4312",
    "#78350f": "#61330E",
    "#eab308": "#C48426",
    "#facc15": "#D8A142",
    "#a16207": "#8D5414",
    "#854d0e": "#714210",
    # Red / rose -> warm sunrise terracotta & coral
    "#fef2f2": "#FCF2EE",
    "#fff1f2": "#FCF1F0",
    "#fee2e2": "#F6DDD5",
    "#ffe4e6": "#F5DBD8",
    "#fecdd3": "#EDC4BC",
    "#fda4af": "#E29F92",
    "#f87171": "#DA785E",
    "#ef4444": "#C85A38",
    "#dc2626": "#B04A22",
    "#e11d48": "#A83E35",
    "#b91c1c": "#96391C",
    "#be123c": "#91322A",
    "#991b1b": "#7E2E17",
    "#9f1239": "#7B2822",
    "#881337": "#69211C",
    # Purple -> soft iris indigo
    "#faf5ff": "#F3F1FA",
    "#f3e8ff": "#E6E1F5",
    "#c084fc": "#9B8CC9",
    "#9333ea": "#6A5A9E",
    "#7e22ce": "#564787",
    "#6b21a8": "#493B74",
    "#581c87": "#3C3061",
}


def harmonize_svg(svg_html: str) -> str:
    """Harmonize embedded SVG diagrams into the Warm-Tech Ceramic Optical Lab palette
    without touching textual numbers (like #16731 merge ranks) and removing redundant outer borders."""
    def clean_svg_open(m):
        tag = m.group(0)
        style_clean = (
            f"width:100%;max-width:640px;height:auto;display:block;margin:0 auto;"
            f"font-family:{FONT_SANS};"
        )
        if 'style="' in tag:
            tag = re.sub(r'style="[^"]*"', f'style="{style_clean}"', tag, count=1)
        else:
            tag = tag[:-1] + f' style="{style_clean}">'
        return tag

    svg_html = re.sub(r"<svg\b[^>]*>", clean_svg_open, svg_html, count=1)

    def repl_attr_color(m):
        prefix = m.group(1)
        col = m.group(2).lower()
        return prefix + SVG_COLOR_MAP.get(col, m.group(2))

    svg_html = re.sub(
        r'((?:fill|stroke|stop-color)\s*=\s*["\']|(?<!-)(?:background|color|fill|stroke)\s*:\s*|border[^;"\']*\s)(#[0-9a-fA-F]{3,6})\b',
        repl_attr_color,
        svg_html,
        flags=re.IGNORECASE,
    )
    return svg_html


# =============================================================================
# 3. Inline Markdown Formatter (Placeholder-Protected)
# =============================================================================

def format_inline(text: str, accent: str = INDIGO, asset_prefix: str = "../assets/") -> str:
    """Convert inline Markdown (images, code, inline math, links, bold, italic) to WeChat inline-CSS HTML."""
    tokens: list[str] = []

    def stash(html_frag: str) -> str:
        idx = len(tokens)
        tokens.append(html_frag)
        return f"@@INL_{idx}@@"

    # 1. Inline image: ![alt](src) — floating borderless plate so the rendered figure breathes
    def repl_img(m):
        alt = html.escape(m.group(1))
        src = m.group(2).strip()
        if src.startswith("../assets/"):
            src = asset_prefix + src[len("../assets/"):]
        elif src.startswith("assets/"):
            src = asset_prefix + src[len("assets/"):]
        return stash(
            f'<figure style="margin:28px 0 26px 0;padding:0;text-align:center;">'
            f'<img src="{src}" alt="{alt}" style="width:100%;max-width:100%;height:auto;border-radius:12px;'
            f'display:block;margin:0 auto;box-shadow:0 4px 20px rgba(24,32,44,0.08);" />'
            f'<figcaption style="margin-top:11px;font-size:12.5px;color:{INK_SUB};line-height:1.58;letter-spacing:0.15px;">'
            f'<span style="font-family:{FONT_MONO};font-size:11.5px;font-weight:700;color:{accent};margin-right:6px;">FIG.</span>'
            f'{alt}</figcaption></figure>'
        )
    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', repl_img, text)

    # 2. Inline code (soft optical-indigo mist pill, borderless)
    def repl_code(m):
        c = html.escape(m.group(1))
        return stash(
            f'<code style="font-family:{FONT_MONO};font-size:13.2px;'
            f'background-color:#EEF3FA;color:{INDIGO_HOVER};padding:1.5px 6px;border-radius:5px;'
            f'margin:0 2px;">{c}</code>'
        )
    text = re.sub(r'\x60([^\x60]+)\x60', repl_code, text)

    # 3. Inline LaTeX math $...$ (soft warm ivory pill, borderless)
    def repl_math(m):
        rendered = render_latex_to_html(m.group(1), display=False)
        return stash(
            f'<span style="font-family:{FONT_MATH};font-style:italic;font-size:15px;'
            f'color:{INK};background:{PAPER_TINT};padding:1px 6px;border-radius:5px;'
            f'margin:0 1px;">{rendered}</span>'
        )
    text = re.sub(r'(?<!\$)\$(?!\$)([^$\n]+?)(?<!\$)\$(?!\$)', repl_math, text)

    # 4. Links [label](url)
    def repl_link(m):
        lbl = html.escape(m.group(1))
        url = html.escape(m.group(2).strip())
        return stash(
            f'<a href="{url}" target="_blank" style="color:{accent};text-decoration:none;'
            f'border-bottom:1px solid {accent};font-weight:600;padding-bottom:1px;">{lbl}</a>'
            f'<span style="font-family:{FONT_MONO};font-size:12px;color:{INK_MUTE};margin-left:4px;word-break:break-all;">({url})</span>'
        )
    text = re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)', repl_link, text)

    # 5. Bold **...** (deep obsidian-indigo emphasis)
    text = re.sub(
        r'\*\*([^\n*]+?)\*\*',
        rf'<strong style="color:{INK};font-weight:700;">\1</strong>',
        text,
    )

    # 6. Italic *...*
    text = re.sub(r'\*([^\n*]+?)\*', rf'<em style="color:{INK_SUB};font-style:italic;">\1</em>', text)

    # 7. Restore protected placeholders
    for idx, frag in enumerate(tokens):
        text = text.replace(f"@@INL_{idx}@@", frag)

    return text


def keep_heading_terms_together(heading_html: str) -> str:
    """Keep a few short terms intact without changing the visible source text."""
    return "".join(
        re.sub(r'外衣|大模型|张量|漂流', r'<span style="white-space:nowrap;">\g<0></span>', part)
        if not part.startswith("<") else part
        for part in re.split(r'(<[^>]+>)', heading_html)
    )


def clean_episode_short_title(title: str) -> str:
    """Strip leading '第 X 期｜' prefix for clean display in sidebar and chrome."""
    return re.sub(r'^第\s*\d+\s*期[｜|：:\s]+', '', title).strip()


# =============================================================================
# 4. Episode Markdown -> WeChat Inline-CSS HTML Converter
# =============================================================================

def split_md_table_row(line: str) -> list[str]:
    """Split a Markdown table row on '|' while ignoring pipes inside $...$ math or `...` code spans."""
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    cells: list[str] = []
    buf: list[str] = []
    in_math = False
    in_code = False
    j = 0
    n = len(s)
    while j < n:
        ch = s[j]
        if ch == "\\" and j + 1 < n and s[j + 1] == "|":
            buf.append("|")
            j += 2
            continue
        if ch == "`" and not in_math:
            in_code = not in_code
            buf.append(ch)
        elif ch == "$" and not in_code:
            in_math = not in_math
            buf.append(ch)
        elif ch == "|" and not in_math and not in_code:
            cells.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
        j += 1
    cells.append("".join(buf).strip())
    return cells


def md_to_wechat_html(md_text: str, meta: dict, asset_prefix: str = "../assets/") -> dict:
    """Parse one Markdown episode into WeChat inline-CSS HTML and return metadata."""
    accent = meta["color"]
    glow = meta["glow"]
    soft = meta["soft"]
    border_col = meta["border"]
    ep_num = meta["ep"]
    roman = meta["roman"]
    part_name = meta["part"]
    tag_name = meta["tag"]

    # Extract H1 title
    m_title = re.search(r'^#\s+(.+)$', md_text, flags=re.MULTILINE)
    title = m_title.group(1).strip() if m_title else f"第 {ep_num:02d} 期"
    short_title = clean_episode_short_title(title)

    # Reading time estimation from prose (strip SVG/code tags first)
    plain_for_count = re.sub(r'<svg[\s\S]*?</svg>', '', md_text)
    plain_for_count = re.sub(r'\x60{3}[\s\S]*?\x60{3}', '', plain_for_count)
    cjk_chars = len(re.findall(r'[\u4e00-\u9fff]', plain_for_count))
    read_mins = max(7, round(cjk_chars / 270))

    # Strip H1 line and top series badge line (rendered cleanly in masthead)
    text = re.sub(r'^#\s+.+\n?', '', md_text, count=1, flags=re.MULTILINE)
    text = re.sub(r'^>\s*\*\*《掀开大模型的黑盒子》.*?\n(?:>.*?\n)*', '', text.lstrip(), count=1)

    # Protect raw <svg>...</svg> blocks — borderless soft ceramic stage
    svg_blocks: list[str] = []
    def save_svg(m):
        idx = len(svg_blocks)
        svg_clean = harmonize_svg(m.group(0))
        wrapper = (
            f'<figure style="margin:28px 0 26px 0;padding:0;text-align:center;">'
            f'<div style="padding:16px 12px 12px 12px;background:#FAF9F6;'
            f'border-radius:14px;overflow-x:auto;box-shadow:0 2px 12px rgba(24,32,44,0.04);">'
            f'{svg_clean}'
            f'</div>'
            f'<figcaption style="margin-top:10px;font-size:12.5px;color:{INK_MUTE};letter-spacing:0.15px;">'
            f'<span style="font-family:{FONT_MONO};font-size:11.5px;font-weight:700;color:{accent};margin-right:6px;">DIAGRAM</span>'
            f'第 {ep_num:02d} 期核心机理结构图解</figcaption></figure>'
        )
        svg_blocks.append(wrapper)
        return f"\n@@SVG_BLOCK_{idx}@@\n"

    text = re.sub(r'<svg[\s\S]*?</svg>', save_svg, text)

    # Protect fenced code blocks — borderless optical slate mist with crisp accent bar
    code_blocks: list[str] = []
    def save_code(m):
        idx = len(code_blocks)
        lang = (m.group(1) or "code").strip().upper()
        code_raw = html.escape(m.group(2).strip())
        box = (
            f'<section style="margin:22px 0;border-radius:12px;overflow:hidden;'
            f'border-left:3.5px solid {accent};background:#F3F6FA;">'
            f'<div style="background:#E9EFF8;padding:8px 16px;'
            f'font-size:12px;color:{INK_SUB};font-family:{FONT_MONO};'
            f'display:flex;align-items:center;justify-content:space-between;letter-spacing:0.4px;">'
            f'<span style="font-weight:700;color:{accent};">{lang}</span>'
            f'<span>DEEPSEEK-CODER-1.3B 实操清单</span></div>'
            f'<pre style="margin:0;padding:15px 18px;overflow-x:auto;font-family:{FONT_MONO};'
            f'font-size:13px;line-height:1.7;color:{INK};white-space:pre;">{code_raw}</pre></section>'
        )
        code_blocks.append(box)
        return f"\n@@CODE_BLOCK_{idx}@@\n"

    text = re.sub(r'\x60{3}([a-zA-Z0-9_\-]*)\n([\s\S]*?)\x60{3}', save_code, text)

    # Protect display math blocks $$...$$ — airy translucent ceramic-indigo mist
    math_blocks: list[str] = []
    def save_display_math(m):
        idx = len(math_blocks)
        rendered = render_latex_to_html(m.group(1).strip(), display=True)
        box = (
            f'<section style="margin:22px 0;padding:18px 20px;'
            f'background:linear-gradient(180deg,#F5F8FC 0%,#FAF8F4 100%);'
            f'border-radius:12px;text-align:center;overflow-x:auto;">'
            f'<div style="font-family:{FONT_MATH};font-style:italic;font-size:16.5px;'
            f'line-height:1.85;color:{INK};letter-spacing:0.2px;">{rendered}</div></section>'
        )
        math_blocks.append(box)
        return f"\n@@MATH_BLOCK_{idx}@@\n"

    text = re.sub(r'\$\$([\s\S]*?)\$\$', save_display_math, text)

    out_html: list[str] = []

    # Open Editorial Masthead (Airy, Luminous, Borderless Ceramic Typography)
    masthead = f"""
    <section style="margin-bottom:28px;padding-bottom:18px;border-bottom:1px solid {LINE_SOFT};">
      <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;margin-bottom:16px;">
        <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
          <span style="display:inline-block;background:{accent};color:#FFFFFF;font-family:{FONT_MONO};font-size:11.5px;font-weight:700;padding:3.5px 11px;border-radius:999px;letter-spacing:0.7px;">ISSUE {ep_num:02d} / {TOTAL_EPS:02d}</span>
          <span style="font-size:12.5px;font-weight:600;color:{accent};letter-spacing:0.25px;">{tag_name}</span>
        </div>
        <span style="font-size:12px;color:{INK_MUTE};letter-spacing:0.2px;">{roman} · {part_name}</span>
      </div>
      <h1 style="margin:0 0 14px 0;font-family:{FONT_SERIF};font-size:23.5px;line-height:1.4;font-weight:700;color:{INK};text-wrap:balance;">{keep_heading_terms_together(html.escape(short_title))}</h1>
      <div style="width:54px;height:3px;border-radius:99px;background:linear-gradient(90deg,{accent} 0%,{WARM_GLOW} 100%);margin-bottom:14px;"></div>
      <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:4px 12px;font-size:12.5px;color:{INK_SUB};">
        <span>《掀开大模型的黑盒子》 · 约 {read_mins} 分钟（{cjk_chars:,} 字）</span>
        <span style="color:{INK_MUTE};">DeepSeek-Coder-1.3B 真机实测</span>
      </div>
    </section>
    """
    out_html.append(masthead.strip())

    raw_lines = text.splitlines()
    i = 0
    n = len(raw_lines)

    while i < n:
        ln = raw_lines[i].strip()
        if not ln:
            i += 1
            continue

        # Protected block restorations
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

        m_math = re.match(r'^@@MATH_BLOCK_(\d+)@@$', ln)
        if m_math:
            out_html.append(math_blocks[int(m_math.group(1))])
            i += 1
            continue

        # Horizontal rule -> delicate warm-tech fading hairline
        if re.match(r'^-{3,}$', ln) or re.match(r'^\*{3,}$', ln):
            out_html.append(
                f'<section style="margin:30px auto;max-width:260px;height:1px;'
                f'background:linear-gradient(90deg,transparent 0%,#DBD5CA 28%,{WARM_GLOW} 50%,#DBD5CA 72%,transparent 100%);"></section>'
            )
            i += 1
            continue

        # H2 Heading & Special Editorial Columns
        if ln.startswith("## "):
            h2_text = ln[3:].strip()

            if "本节核心要点" in h2_text or "核心要点" in h2_text:
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
                    f'<li style="margin:8px 0;line-height:1.82;color:{INK_BODY};font-size:14.8px;">{item}</li>'
                    for item in kp_items
                )
                card = (
                    f'<section style="margin:18px 0 26px 0;padding:11px 14px 8px 14px;'
                    f'background:linear-gradient(135deg,{soft} 0%,{PAPER_BG} 72%);'
                    f'border-left:2px solid {accent};border-radius:0 10px 10px 0;">'
                    f'<div style="font-family:{FONT_SERIF};font-size:16.5px;font-weight:700;color:{accent};margin-bottom:7px;">'
                    f'本期核心要点 · 1 分钟先抓主干</div>'
                    f'<ul style="margin:0;padding-left:20px;">{li_html}</ul></section>'
                )
                out_html.append(card)
                continue

            elif "科学史故事" in h2_text or "故事栏" in h2_text:
                story_title = re.sub(r'^.*?科学史故事栏[：:\s]*', '', h2_text).strip() or h2_text
                i += 1
                story_paras = []
                while i < n and not raw_lines[i].strip().startswith("## "):
                    s = raw_lines[i].strip()
                    if s and not re.match(r'^-{3,}$', s):
                        story_paras.append(
                            f'<p style="margin:11px 0;font-size:15px;line-height:1.88;color:#352D28;text-align:justify;">'
                            f'{format_inline(s, TERRACOTTA, asset_prefix)}</p>'
                        )
                    i += 1
                card = (
                    f'<section style="margin:32px 0;padding:22px 22px 16px 22px;'
                    f'background:linear-gradient(145deg,{PAPER_SUN} 0%,#FAF2E8 100%);'
                    f'border-top:3px solid #D97A4A;border-radius:14px;">'
                    f'<div style="font-family:{FONT_MONO};font-size:12px;font-weight:700;letter-spacing:0.8px;'
                    f'color:{TERRACOTTA};margin-bottom:6px;">HISTORY OF SCIENCE · 科学史故事专栏</div>'
                    f'<h3 style="margin:0 0 13px 0;font-family:{FONT_SERIF};font-size:18px;line-height:1.45;'
                    f'font-weight:700;color:#5A2B16;">{html.escape(story_title)}</h3>'
                    f'{"".join(story_paras)}</section>'
                )
                out_html.append(card)
                continue

            elif "下期预告" in h2_text or "毕业挑战" in h2_text:
                is_final = "毕业挑战" in h2_text
                eyebrow = "FINAL CHALLENGE · 毕业动手挑战" if is_final else "NEXT ISSUE · 下期预告"
                clean_h = re.sub(r'^[🔮🚀📌\s]+', '', h2_text).strip()
                i += 1
                hook_paras = []
                while i < n and not raw_lines[i].strip().startswith("## "):
                    s = raw_lines[i].strip()
                    if s and not re.match(r'^-{3,}$', s):
                        s_clean = re.sub(r'^>\s*', '', s)
                        hook_paras.append(
                            f'<p style="margin:10px 0;font-size:14.8px;line-height:1.84;color:{INK_BODY};text-align:justify;">'
                            f'{format_inline(s_clean, INDIGO, asset_prefix)}</p>'
                        )
                    i += 1
                card = (
                    f'<section style="margin:28px 0;padding:20px 22px 16px 22px;'
                    f'background:linear-gradient(135deg,{PAPER_TECH} 0%,{PAPER_SUN} 100%);'
                    f'border-left:3.5px solid {INDIGO};border-radius:0 14px 14px 0;">'
                    f'<div style="font-family:{FONT_MONO};font-size:12px;font-weight:700;letter-spacing:0.8px;'
                    f'color:{INDIGO};margin-bottom:5px;">{eyebrow}</div>'
                    f'<div style="font-family:{FONT_SERIF};font-size:16.5px;font-weight:700;color:{INK};margin-bottom:8px;">'
                    f'{html.escape(clean_h)}</div>'
                    f'{"".join(hook_paras)}</section>'
                )
                out_html.append(card)
                continue

            elif "拓展资源" in h2_text:
                i += 1
                res_items = []
                while i < n and not raw_lines[i].strip().startswith("## "):
                    s = raw_lines[i].strip()
                    if s and not re.match(r'^-{3,}$', s):
                        s_clean = re.sub(r'^[\-\*\+]\s+', '', s)
                        s_clean = re.sub(r'^\d+\.\s+', '', s_clean)
                        res_items.append(
                            f'<li style="margin:8px 0;font-size:14px;line-height:1.78;color:{INK_SUB};">'
                            f'{format_inline(s_clean, accent, asset_prefix)}</li>'
                        )
                    i += 1
                card = (
                    f'<section style="margin:28px 0 14px 0;padding:20px 22px 16px 22px;'
                    f'background:{PAPER_TINT};border-radius:14px;">'
                    f'<div style="font-family:{FONT_MONO};font-size:12px;font-weight:700;letter-spacing:0.8px;'
                    f'color:{INK_MUTE};margin-bottom:5px;">REFERENCES &amp; LAB</div>'
                    f'<div style="font-family:{FONT_SERIF};font-size:16px;font-weight:700;color:{INK};margin-bottom:10px;">'
                    f'拓展资源加油站（课后动手实验室）</div>'
                    f'<ol style="margin:0;padding-left:20px;">{"".join(res_items)}</ol></section>'
                )
                out_html.append(card)
                continue

            else:
                out_html.append(
                    f'<h2 style="margin:36px 0 16px 0;'
                    f'font-family:{FONT_SERIF};font-size:19.5px;line-height:1.42;font-weight:700;color:{INK};'
                    f'display:flex;align-items:center;gap:10px;">'
                    f'<span style="display:inline-block;width:4px;height:19px;'
                    f'background:linear-gradient(180deg,{accent} 0%,{WARM_GLOW} 100%);'
                    f'border-radius:99px;flex-shrink:0;"></span>'
                    f'<span style="min-width:0;text-wrap:pretty;">{keep_heading_terms_together(format_inline(h2_text, accent, asset_prefix))}</span></h2>'
                )
                i += 1
                continue

        # H3 Heading
        if ln.startswith("### "):
            h3_text = ln[4:].strip()
            out_html.append(
                f'<h3 style="margin:26px 0 10px 0;padding-left:11px;border-left:2.5px solid {accent};'
                f'font-family:{FONT_SANS};font-size:16px;line-height:1.45;font-weight:700;color:{INK};">'
                f'{format_inline(h3_text, accent, asset_prefix)}</h3>'
            )
            i += 1
            continue

        # Blockquote (底层思想提炼 vs standard editorial quotation)
        if ln.startswith(">"):
            bq_lines = []
            while i < n and raw_lines[i].strip().startswith(">"):
                bq_lines.append(re.sub(r'^>\s?', '', raw_lines[i].strip()))
                i += 1
            bq_raw = "\n".join(bq_lines)
            if "底层思想提炼" in bq_raw:
                bq_cleaned = re.sub(r'🧠\s*', '', bq_raw)
                bq_paras = [
                    f'<p style="margin:6px 0;font-size:15px;line-height:1.84;color:{INK_BODY};text-align:justify;">'
                    f'{format_inline(p.strip(), INDIGO, asset_prefix)}</p>'
                    for p in bq_cleaned.splitlines() if p.strip()
                ]
                out_html.append(
                    f'<section style="margin:24px 0;padding:17px 20px 15px 20px;'
                    f'background:linear-gradient(135deg,{PAPER_TECH} 0%,#F7FAFE 100%);'
                    f'border-left:3.5px solid {INDIGO};border-radius:0 14px 14px 0;">'
                    f'<div style="font-family:{FONT_MONO};font-size:12px;font-weight:700;letter-spacing:0.8px;'
                    f'color:{INDIGO};margin-bottom:6px;">FIRST PRINCIPLES · 底层思想</div>'
                    f'{"".join(bq_paras)}</section>'
                )
            else:
                bq_paras = [
                    f'<p style="margin:6px 0;font-size:14.8px;line-height:1.82;color:{INK_SUB};text-align:justify;">'
                    f'{format_inline(p.strip(), accent, asset_prefix)}</p>'
                    for p in bq_lines if p.strip()
                ]
                out_html.append(
                    f'<blockquote style="margin:20px 0;padding:14px 18px;background:{PAPER_TINT};'
                    f'border-left:3px solid #D9B79A;border-radius:0 12px 12px 0;">{"".join(bq_paras)}</blockquote>'
                )
            continue

        # Markdown Table (Modern Optical Booktabs Style)
        if ln.startswith("|") and i + 1 < n and re.match(r'^\|\s*[:\-]+', raw_lines[i + 1].strip()):
            headers = split_md_table_row(ln)
            i += 2
            rows = []
            while i < n and raw_lines[i].strip().startswith("|"):
                r_cells = split_md_table_row(raw_lines[i])
                rows.append(r_cells)
                i += 1
            is_wide_tbl = len(headers) >= 6
            th_pad = "8px 8px" if is_wide_tbl else "10px 11px"
            td_pad = "8px 8px" if is_wide_tbl else "9px 11px"
            th_fs = "11.5px" if is_wide_tbl else "12.5px"
            td_fs = "12px" if is_wide_tbl else "13px"
            th_html = "".join(
                f'<th style="padding:{th_pad};background:#F1F5FC;color:{INK};font-weight:700;font-size:{th_fs};'
                f'line-height:1.4;vertical-align:bottom;text-align:left;border-top:2px solid {INDIGO};border-bottom:1.5px solid #C6D6EC;">'
                f'{format_inline(h, accent, asset_prefix)}</th>'
                for h in headers
            )
            tr_html = []
            for r_idx, r in enumerate(rows):
                bg = PAPER_BG if r_idx % 2 == 0 else "#FAF9F6"
                b_bot = f"1.5px solid {INDIGO}" if r_idx == len(rows) - 1 else f"1px solid {LINE_SOFT}"
                tds = "".join(
                    f'<td style="padding:{td_pad};border-bottom:{b_bot};font-size:{td_fs};line-height:1.54;'
                    f'color:{INK_BODY};background:{bg};font-variant-numeric:tabular-nums;vertical-align:top;">'
                    f'{format_inline(c, accent, asset_prefix)}</td>'
                    for c in r
                )
                tr_html.append(f"<tr>{tds}</tr>")
            tbl_min_w = "min-width:780px;" if len(headers) >= 9 else ("min-width:610px;" if len(headers) >= 7 else "")
            hint_scope = "可左右滑动查看完整数据" if len(headers) >= 9 else "窄屏可左右滑动查看"
            scroll_hint = (
                f'<div style="font-size:12px;color:{INK_MUTE};text-align:right;margin-top:6px;">'
                f'↔ 数据表含 {len(headers)} 列，{hint_scope}</div>'
            ) if len(headers) >= 7 else ""
            table_block = (
                f'<section style="margin:24px 0;">'
                f'<section style="overflow-x:auto;-webkit-overflow-scrolling:touch;border-radius:8px;">'
                f'<table style="width:100%;{tbl_min_w}border-collapse:collapse;font-size:{td_fs};">'
                f'<thead><tr>{th_html}</tr></thead><tbody>{"".join(tr_html)}</tbody></table></section>'
                f'{scroll_hint}</section>'
            )
            out_html.append(table_block)
            continue

        # Ordered List (WeChat-proof explicit editorial numbering, preserves numbers across block math)
        if re.match(r'^\d+\.\s+', ln):
            items = []
            while i < n and re.match(r'^\d+\.\s+', raw_lines[i].strip()):
                m_ol = re.match(r'^(\d+)\.\s+(.*)$', raw_lines[i].strip())
                num_str = m_ol.group(1)
                s = m_ol.group(2)
                items.append(
                    f'<section style="display:flex;align-items:baseline;gap:9px;margin:10px 0;">'
                    f'<span style="flex-shrink:0;min-width:22px;font-family:{FONT_MONO};font-size:13.5px;'
                    f'font-weight:700;color:{accent};font-variant-numeric:tabular-nums;">{num_str}.</span>'
                    f'<section style="flex:1;min-width:0;font-size:15.2px;line-height:1.86;color:{INK_BODY};">'
                    f'{format_inline(s, accent, asset_prefix)}</section></section>'
                )
                i += 1
            out_html.append(f'<section style="margin:15px 0;">{"".join(items)}</section>')
            continue

        # Unordered List
        if re.match(r'^[\-\*\+]\s+', ln):
            items = []
            while i < n and re.match(r'^[\-\*\+]\s+', raw_lines[i].strip()):
                s = re.sub(r'^[\-\*\+]\s+', '', raw_lines[i].strip())
                items.append(
                    f'<li style="margin:8px 0;font-size:15.2px;line-height:1.86;color:{INK_BODY};">'
                    f'{format_inline(s, accent, asset_prefix)}</li>'
                )
                i += 1
            out_html.append(f'<ul style="margin:15px 0;padding-left:22px;">{"".join(items)}</ul>')
            continue

        # Standalone Image line
        if re.match(r'^!\[[^\]]*\]\([^)]+\)$', ln):
            out_html.append(format_inline(ln, accent, asset_prefix))
            i += 1
            continue

        # Standard paragraph
        out_html.append(
            f'<p style="margin:16px 0;font-size:15.5px;line-height:1.88;color:{INK_BODY};'
            f'letter-spacing:0.25px;text-align:justify;">{format_inline(ln, accent, asset_prefix)}</p>'
        )
        i += 1

    # Luminous Warm-Tech Colophon Footer
    footer = f"""
    <section style="margin-top:38px;padding-top:18px;font-size:12.5px;line-height:1.78;color:{INK_SUB};display:flex;flex-direction:column;gap:5px;">
      <div style="height:2px;border-radius:99px;background:linear-gradient(90deg,{accent} 0%,{glow} 52%,{WARM_GLOW} 100%);margin-bottom:14px;"></div>
      <div style="font-family:{FONT_SERIF};font-weight:700;color:{INK};font-size:14px;letter-spacing:0.3px;">《掀开大模型的黑盒子》 · 全 {TOTAL_EPS} 期硬核科普连载</div>
      <div>全部数据与图鉴均基于开源模型 <code style="font-family:{FONT_MONO};font-size:12px;background:#EEF3FA;color:{INDIGO_HOVER};padding:1.5px 6px;border-radius:4px;">deepseek-coder-1.3b-base</code>（32,256 词表 · 24 层 · 13.46 亿参数）真机前向实测生成。</div>
    </section>
    """
    out_html.append(footer.strip())

    top_ribbon = (
        f'<div style="height:3.5px;background:linear-gradient(90deg,{accent} 0%,{glow} 54%,{WARM_GLOW} 100%);"></div>'
    )
    wechat_inner_html = (
        f'<section id="wechat-article-body" style="max-width:677px;margin:0 auto;'
        f'background:{PAPER_BG};font-family:{FONT_SANS};color:{INK_BODY};box-sizing:border-box;">\n'
        f'{top_ribbon}\n'
        f'<section style="padding:28px 28px 36px;padding-inline:min(28px,5vw);">\n'
        + "\n".join(out_html)
        + "\n</section>\n</section>"
    )

    return {
        "ep": ep_num,
        "title": title,
        "short_title": short_title,
        "part_no": meta["part_no"],
        "roman": roman,
        "part": part_name,
        "tag": tag_name,
        "color": accent,
        "glow": glow,
        "soft": soft,
        "border": border_col,
        "cjk_chars": cjk_chars,
        "read_mins": read_mins,
        "wechat_html": wechat_inner_html,
    }


# =============================================================================
# 5. Standalone Episode Preview HTML (html/ep01.html .. html/ep15.html)
# =============================================================================

def write_standalone_episode_html(ep_data: dict):
    ep = ep_data["ep"]
    prev_link = f'<a href="ep{ep-1:02d}.html" class="pager-link">← 上一期（第 {ep-1:02d} 期）</a>' if ep > 1 else '<span class="pager-disabled">已是开篇第 01 期</span>'
    next_link = f'<a href="ep{ep+1:02d}.html" class="pager-link">下一期（第 {ep+1:02d} 期）→</a>' if ep < TOTAL_EPS else f'<span class="pager-disabled">已是最新第 {TOTAL_EPS:02d} 期</span>'

    page = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{html.escape(ep_data['title'])} · 《掀开大模型的黑盒子》</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; }}
  :root {{
    --desk: #F2EFE9;
    --bar: rgba(250, 249, 246, 0.86);
    --paper: #FFFEFC;
    --ink: #18202C;
    --ink-sub: #475569;
    --ink-mute: #556173;
    --indigo: #2B548A;
    --indigo-hover: #1F416E;
    --warm-glow: #E08B5A;
    --accent: {ep_data['color']};
  }}
  body {{
    margin: 0;
    min-height: 100vh;
    background:
      radial-gradient(58% 44% at 92% 4%, rgba(232, 160, 112, 0.19) 0%, rgba(232, 160, 112, 0) 68%),
      radial-gradient(50% 42% at 8% 92%, rgba(66, 125, 198, 0.11) 0%, rgba(66, 125, 198, 0) 65%),
      var(--desk);
    background-attachment: fixed;
    color: var(--ink);
    font-family: {FONT_SANS};
    -webkit-font-smoothing: antialiased;
  }}
  .toolbar {{
    position: sticky;
    top: 0;
    z-index: 100;
    background: var(--bar);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border-bottom: 1px solid rgba(43, 84, 138, 0.08);
    padding: 0 22px;
    height: 58px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }}
  .read-progress {{
    position: absolute;
    left: 0;
    bottom: -1px;
    height: 2.5px;
    width: 0%;
    background: linear-gradient(90deg, var(--indigo) 0%, #4C82C2 55%, var(--warm-glow) 100%);
    transition: width 0.08s linear;
    pointer-events: none;
  }}
  .toolbar-left, .toolbar-right {{
    display: flex;
    align-items: center;
    gap: 10px;
    min-width: 0;
  }}
  .back-link {{
    color: var(--ink-sub);
    text-decoration: none;
    font-size: 13px;
    font-weight: 600;
    padding: 7px 12px;
    border-radius: 9px;
    background: rgba(255, 255, 255, 0.85);
    box-shadow: 0 1px 2px rgba(24, 32, 44, 0.05), 0 0 0 1px rgba(43, 84, 138, 0.09);
    white-space: nowrap;
    transition: color 0.16s, box-shadow 0.16s, background 0.16s;
  }}
  .back-link:hover {{
    color: var(--indigo);
    background: #FFFFFF;
    box-shadow: 0 2px 8px rgba(43, 84, 138, 0.12), 0 0 0 1px rgba(43, 84, 138, 0.24);
  }}
  .issue-pill {{
    font-family: {FONT_MONO};
    font-size: 12px;
    font-weight: 700;
    color: var(--accent);
    background: {ep_data['soft']};
    padding: 4.5px 10px;
    border-radius: 999px;
    white-space: nowrap;
  }}
  .issue-title-mini {{
    font-size: 13.5px;
    font-weight: 600;
    color: var(--ink);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 340px;
  }}
  .seg {{
    display: inline-flex;
    background: rgba(43, 84, 138, 0.06);
    border-radius: 9px;
    padding: 3px;
  }}
  .seg button {{
    border: none;
    background: transparent;
    color: var(--ink-sub);
    font-size: 12.5px;
    font-weight: 600;
    padding: 5px 11px;
    border-radius: 7px;
    cursor: pointer;
    font-family: inherit;
    transition: all 0.16s;
  }}
  .seg button.active {{
    background: var(--paper);
    color: var(--ink);
    box-shadow: 0 1px 4px rgba(24, 32, 44, 0.09);
  }}
  .btn-copy {{
    background: linear-gradient(135deg, var(--indigo) 0%, #3768A6 100%);
    color: #FFFFFF;
    border: none;
    padding: 8px 16px;
    border-radius: 9px;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    font-family: inherit;
    white-space: nowrap;
    box-shadow: 0 2px 8px rgba(43, 84, 138, 0.22);
    transition: transform 0.15s, box-shadow 0.15s, background 0.15s;
  }}
  .btn-copy:hover {{
    transform: translateY(-0.5px);
    box-shadow: 0 4px 12px rgba(43, 84, 138, 0.30);
    background: linear-gradient(135deg, var(--indigo-hover) 0%, var(--indigo) 100%);
  }}
  .btn-copy.copied {{
    background: linear-gradient(135deg, #196473 0%, #247F91 100%);
  }}
  .preview-shell {{
    margin: 30px auto 26px auto;
    max-width: 677px;
    background: var(--paper);
    border-radius: 16px;
    box-shadow: 0 1px 2px rgba(24, 32, 44, 0.04), 0 18px 48px rgba(34, 52, 78, 0.09), 0 0 0 1px rgba(43, 84, 138, 0.06);
    overflow: hidden;
    transition: max-width 0.24s ease, border-radius 0.24s ease;
  }}
  .preview-shell.mobile {{
    max-width: 390px;
    border: 10px solid #1C2533;
    border-radius: 36px;
    box-shadow: 0 22px 52px rgba(24, 32, 44, 0.20);
  }}
  .bottom-nav {{
    max-width: 677px;
    margin: 0 auto 52px auto;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    padding: 0 2px;
  }}
  .pager-link {{
    color: var(--ink);
    text-decoration: none;
    font-size: 13px;
    font-weight: 600;
    padding: 10px 16px;
    background: var(--paper);
    border-radius: 10px;
    box-shadow: 0 1px 3px rgba(24, 32, 44, 0.05), 0 0 0 1px rgba(43, 84, 138, 0.08);
    transition: color 0.16s, box-shadow 0.16s, transform 0.16s;
  }}
  .pager-link:hover {{
    color: var(--indigo);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(43, 84, 138, 0.12), 0 0 0 1px rgba(43, 84, 138, 0.22);
  }}
  .pager-disabled {{
    color: var(--ink-mute);
    background: rgba(255, 255, 255, 0.55);
    border-radius: 10px;
    font-size: 13px;
    padding: 10px 16px;
  }}
  @media (max-width: 720px) {{
    .toolbar {{ padding: 0 14px; }}
    .issue-title-mini, .seg {{ display: none; }}
    .preview-shell, .preview-shell.mobile {{ max-width: 100%; margin: 0; border-radius: 0; border: none; box-shadow: none; }}
    .bottom-nav {{ padding: 18px 14px 0 14px; }}
  }}
</style>
</head>
<body>
  <header class="toolbar">
    <div class="toolbar-left">
      <a href="../index.html#ep{ep:02d}" class="back-link">← 返回全系列工作台</a>
      <span class="issue-pill">第 {ep:02d} / {TOTAL_EPS:02d} 期</span>
      <span class="issue-title-mini">{html.escape(ep_data['short_title'])}</span>
    </div>
    <div class="toolbar-right">
      <div class="seg" role="group" aria-label="视口宽度切换">
        <button id="btnDesktop" class="active" onclick="setWidthMode(false)">公众号 677px</button>
        <button id="btnMobile" onclick="setWidthMode(true)">手机 390px</button>
      </div>
      <button class="btn-copy" id="copyBtn" onclick="copyArticle()">复制公众号排版</button>
    </div>
    <div class="read-progress" id="readProgress"></div>
  </header>

  <main class="preview-shell" id="previewShell">
    {ep_data['wechat_html']}
  </main>

  <nav class="bottom-nav">
    {prev_link}
    {next_link}
  </nav>

<script>
function setWidthMode(isMobile) {{
  const shell = document.getElementById('previewShell');
  shell.classList.toggle('mobile', isMobile);
  document.getElementById('btnDesktop').classList.toggle('active', !isMobile);
  document.getElementById('btnMobile').classList.toggle('active', isMobile);
}}

function updateProgress() {{
  const doc = document.documentElement;
  const max = doc.scrollHeight - window.innerHeight;
  const pct = max > 0 ? Math.min(100, Math.max(0, (window.scrollY / max) * 100)) : 0;
  document.getElementById('readProgress').style.width = pct.toFixed(1) + '%';
}}
window.addEventListener('scroll', updateProgress, {{ passive: true }});
updateProgress();

async function copyArticle() {{
  const node = document.getElementById('wechat-article-body');
  const btn = document.getElementById('copyBtn');
  let ok = false;
  try {{
    if (navigator.clipboard && window.ClipboardItem) {{
      const htmlBlob = new Blob([node.outerHTML], {{ type: 'text/html' }});
      const textBlob = new Blob([node.innerText], {{ type: 'text/plain' }});
      await navigator.clipboard.write([new ClipboardItem({{ 'text/html': htmlBlob, 'text/plain': textBlob }})]);
      ok = true;
    }}
  }} catch (_) {{}}
  if (!ok) {{
    const range = document.createRange();
    range.selectNode(node);
    const sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(range);
    try {{ ok = document.execCommand('copy'); }} catch (_) {{}}
    if (ok) sel.removeAllRanges();
  }}
  btn.textContent = ok ? '已复制' : '请手动复制';
  btn.classList.toggle('copied', ok);
  setTimeout(() => {{
    btn.textContent = '复制公众号排版';
    btn.classList.remove('copied');
  }}, 2600);
}}
</script>
</body>
</html>"""
    (HTML_DIR / f"ep{ep:02d}.html").write_text(page, encoding="utf-8")


# =============================================================================
# 6. Master 12-Episode Editorial Workbench (index.html)
# =============================================================================

def write_master_portal(portal_eps: list[dict]):
    total_chars = sum(e["cjk_chars"] for e in portal_eps)
    unique_figs = len(set(re.findall(r'<img[^>]+src="([^"]+)"', "".join(e["wechat_html"] for e in portal_eps))))

    sidebar_parts_html = []
    for part_no in sorted(PART_PALETTE.keys()):
        group_eps = [e for e in portal_eps if e["part_no"] == part_no]
        if not group_eps:
            continue
        pinfo = PART_PALETTE[part_no]
        part_title = re.sub(r'^第[一二三四五六七八九十]+部分(?:（[^）]*）)?[：:\s]*', '', group_eps[0]["part"])
        items_html = []
        for e in group_eps:
            active_cls = "active" if e["ep"] == 1 else ""
            search_hay = html.escape(f"{e['ep']:02d} 第{e['ep']}期 {e['short_title']} {e['tag']} {e['part']}".lower())
            items_html.append(f"""
            <button type="button" class="ep-item {active_cls}" id="nav-ep-{e['ep']}"
                    data-ep="{e['ep']}" data-search="{search_hay}"
                    style="--ep-accent:{e['color']};--ep-soft:{e['soft']};" onclick="selectEp({e['ep']})">
              <span class="ep-num">{e['ep']:02d}</span>
              <span class="ep-body">
                <span class="ep-title">{html.escape(e['short_title'])}</span>
                <span class="ep-meta">{html.escape(e['tag'])} · {e['read_mins']} min · {e['cjk_chars']:,} 字</span>
              </span>
            </button>""")
        sidebar_parts_html.append(f"""
        <div class="part-group" data-part="{part_no}">
          <div class="part-heading">
            <span class="part-dot" style="background:{pinfo['accent']};"></span>
            <span class="part-roman">{pinfo['roman']}</span>
            <span class="part-name">{html.escape(part_title)}</span>
          </div>
          {"".join(items_html).lstrip()}
        </div>""")

    lab_items_html = []
    for d in INTERACTIVE_DEMOS:
        search_hay = html.escape(d["search"].lower())
        lab_items_html.append(f"""
            <a class="ep-item lab-item" href="{html.escape(d['href'])}" target="_blank" rel="noopener"
               data-search="{search_hay}" style="--ep-accent:{d['accent']};--ep-soft:{d['soft']};">
              <span class="ep-num">{html.escape(d['code'])}</span>
              <span class="ep-body">
                <span class="ep-title">{html.escape(d['title'])} <span class="lab-ext">↗</span></span>
                <span class="ep-meta">{html.escape(d['desc'])}</span>
              </span>
            </a>""")
    sidebar_labs_html = (
        f"""
        <div class="part-group lab-group" data-part="lab">
          <div class="part-heading">
            <span class="part-dot" style="background:#564787;"></span>
            <span class="part-roman">LAB</span>
            <span class="part-name">交互实验室 · 动手实验</span>
          </div>
          {"".join(lab_items_html).lstrip()}
        </div>"""
        if INTERACTIVE_DEMOS
        else ""
    )

    portal_articles = []
    for e in portal_eps:
        display_style = "block" if e["ep"] == 1 else "none"
        portal_articles.append(
            f'<div class="ep-pane" id="pane-ep-{e["ep"]}" style="display:{display_style};">{e["wechat_html"]}</div>'
        )

    ep_meta_json = json.dumps(
        [
            {
                "ep": e["ep"],
                "short_title": e["short_title"],
                "tag": e["tag"],
                "part": e["part"],
                "roman": e["roman"],
                "color": e["color"],
                "glow": e["glow"],
                "soft": e["soft"],
                "border": e["border"],
                "cjk_chars": e["cjk_chars"],
                "read_mins": e["read_mins"],
            }
            for e in portal_eps
        ],
        ensure_ascii=False,
    )

    portal_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>《掀开大模型的黑盒子》全 {len(portal_eps)} 期专刊排版工作台</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; }}
  :root {{
    --desk: #F2EFE9;
    --rail: #FAF9F6;
    --paper: #FFFEFC;
    --warm: #F5F1E9;
    --ink: #18202C;
    --ink-sub: #475569;
    --ink-mute: #556173;
    --line: #E5E0D6;
    --line-soft: #EFECE4;
    --indigo: #2B548A;
    --indigo-hover: #1F416E;
    --warm-glow: #E08B5A;
  }}
  html, body {{
    margin: 0;
    padding: 0;
    height: 100%;
    overflow: hidden;
    background: var(--desk);
    color: var(--ink);
    font-family: {FONT_SANS};
    -webkit-font-smoothing: antialiased;
  }}
  .app-shell {{
    display: flex;
    height: 100vh;
    width: 100vw;
    overflow: hidden;
  }}

  /* Left Porcelain Directory Rail */
  .sidebar {{
    width: 336px;
    background: linear-gradient(180deg, #FCFBF8 0%, #F7F5F0 100%);
    border-right: 1px solid rgba(43, 84, 138, 0.08);
    display: flex;
    flex-direction: column;
    height: 100vh;
    flex-shrink: 0;
    z-index: 30;
    position: relative;
  }}
  .sidebar::before {{
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--indigo) 0%, #4C82C2 55%, var(--warm-glow) 100%);
    z-index: 2;
  }}
  .sidebar-header {{
    padding: 24px 20px 16px 20px;
    border-bottom: 1px solid rgba(43, 84, 138, 0.07);
    background: transparent;
  }}
  .series-kicker {{
    font-family: {FONT_MONO};
    font-size: 11.5px;
    font-weight: 700;
    letter-spacing: 0.7px;
    color: var(--indigo);
    margin-bottom: 7px;
    display: flex;
    align-items: center;
    gap: 7px;
  }}
  .kicker-dot {{
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--indigo) 0%, var(--warm-glow) 100%);
    flex-shrink: 0;
  }}
  .sidebar-header h1 {{
    margin: 0 0 6px 0;
    font-family: {FONT_SERIF};
    font-size: 20px;
    font-weight: 700;
    color: var(--ink);
    letter-spacing: 0.15px;
    line-height: 1.32;
  }}
  .series-stats {{
    margin: 0 0 14px 0;
    font-size: 12.5px;
    color: var(--ink-sub);
    line-height: 1.5;
    font-variant-numeric: tabular-nums;
  }}
  .search-wrap {{
    position: relative;
  }}
  .search-input {{
    width: 100%;
    padding: 8.5px 30px 8.5px 13px;
    font-size: 13.5px;
    color: var(--ink);
    background: #FFFFFF;
    border: none;
    border-radius: 10px;
    outline: none;
    font-family: inherit;
    box-shadow: 0 1px 2px rgba(24, 32, 44, 0.04), 0 0 0 1px rgba(43, 84, 138, 0.12);
    transition: box-shadow 0.16s;
  }}
  .search-input:focus {{
    box-shadow: 0 0 0 3px rgba(43, 84, 138, 0.13), 0 0 0 1px var(--indigo);
  }}
  .search-input::placeholder {{
    color: var(--ink-mute);
  }}
  .search-clear {{
    position: absolute;
    right: 7px;
    top: 50%;
    transform: translateY(-50%);
    border: none;
    background: transparent;
    color: var(--ink-mute);
    font-size: 16px;
    cursor: pointer;
    display: none;
    padding: 2px 6px;
  }}
  .ep-list {{
    flex: 1;
    overflow-y: auto;
    padding: 14px 12px 26px 12px;
  }}
  .ep-list::-webkit-scrollbar {{ width: 5px; }}
  .ep-list::-webkit-scrollbar-thumb {{ background: rgba(43, 84, 138, 0.16); border-radius: 99px; }}
  .part-group {{
    margin-bottom: 16px;
  }}
  .part-heading {{
    display: flex;
    align-items: center;
    gap: 7px;
    padding: 4px 10px 7px 10px;
    font-size: 12px;
    color: var(--ink-mute);
  }}
  .part-dot {{
    width: 6px;
    height: 6px;
    border-radius: 50%;
    flex-shrink: 0;
  }}
  .part-roman {{
    font-family: {FONT_MONO};
    font-size: 11.5px;
    font-weight: 700;
    letter-spacing: 0.4px;
    color: var(--ink-sub);
  }}
  .part-name {{
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }}
  .ep-item {{
    position: relative;
    width: 100%;
    text-align: left;
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 10px 12px 10px 14px;
    margin-bottom: 4px;
    border-radius: 11px;
    border: none;
    background: transparent;
    cursor: pointer;
    font-family: inherit;
    transition: background 0.16s, box-shadow 0.16s, transform 0.14s;
  }}
  .ep-item::before {{
    content: "";
    position: absolute;
    left: 4px;
    top: 10px;
    bottom: 10px;
    width: 3px;
    border-radius: 99px;
    background: transparent;
    transition: background 0.16s;
  }}
  .ep-item:hover {{
    background: rgba(255, 255, 255, 0.72);
  }}
  .ep-item.active {{
    background: #FFFFFF;
    box-shadow: 0 2px 10px rgba(34, 52, 78, 0.07), 0 0 0 1px rgba(43, 84, 138, 0.08);
  }}
  .ep-item.active::before {{
    background: var(--ep-accent, var(--indigo));
  }}
  .ep-num {{
    font-family: {FONT_MONO};
    font-size: 12.5px;
    font-weight: 700;
    color: var(--ep-accent, var(--indigo));
    line-height: 1.45;
    padding-top: 1px;
    flex-shrink: 0;
    font-variant-numeric: tabular-nums;
  }}
  .ep-body {{
    display: flex;
    flex-direction: column;
    gap: 3px;
    min-width: 0;
  }}
  .ep-title {{
    font-size: 13.5px;
    font-weight: 600;
    color: var(--ink);
    line-height: 1.42;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }}
  .ep-meta {{
    font-size: 12px;
    color: var(--ink-mute);
    font-variant-numeric: tabular-nums;
  }}
  .lab-group {{
    margin-top: 18px;
    padding-top: 14px;
    border-top: 1px dashed rgba(43, 84, 138, 0.14);
  }}
  .lab-item {{
    text-decoration: none;
    background: linear-gradient(135deg, rgba(243, 241, 250, 0.72) 0%, rgba(255, 255, 255, 0.88) 100%);
    box-shadow: 0 1px 4px rgba(34, 52, 78, 0.05), 0 0 0 1px rgba(86, 71, 135, 0.14);
  }}
  .lab-item:hover {{
    background: #FFFFFF;
    box-shadow: 0 4px 12px rgba(86, 71, 135, 0.14), 0 0 0 1px rgba(86, 71, 135, 0.30);
    transform: translateY(-0.5px);
  }}
  .lab-item .ep-num {{
    font-size: 11px;
    padding: 1.5px 6px;
    border-radius: 6px;
    background: var(--ep-soft);
    line-height: 1.5;
    margin-top: 1px;
  }}
  .lab-ext {{
    color: var(--ep-accent);
    font-weight: 700;
    margin-left: 2px;
  }}
  .empty-filter {{
    display: none;
    text-align: center;
    padding: 28px 12px;
    font-size: 13px;
    color: var(--ink-mute);
  }}

  /* Right Luminous Reading Studio */
  .main-stage {{
    flex: 1;
    display: flex;
    flex-direction: column;
    height: 100vh;
    min-width: 0;
    background:
      radial-gradient(62% 48% at 92% 4%, rgba(232, 160, 112, 0.19) 0%, rgba(232, 160, 112, 0) 68%),
      radial-gradient(52% 44% at 8% 92%, rgba(66, 125, 198, 0.11) 0%, rgba(66, 125, 198, 0) 65%),
      var(--desk);
  }}
  .stage-toolbar {{
    position: relative;
    height: 58px;
    flex-shrink: 0;
    background: rgba(250, 249, 246, 0.84);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border-bottom: 1px solid rgba(43, 84, 138, 0.08);
    padding: 0 22px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    z-index: 10;
  }}
  .read-progress {{
    position: absolute;
    left: 0;
    bottom: -1px;
    height: 2.5px;
    width: 0%;
    background: linear-gradient(90deg, var(--indigo) 0%, #4C82C2 55%, var(--warm-glow) 100%);
    transition: width 0.08s linear;
    pointer-events: none;
  }}
  .tb-left, .tb-right {{
    display: flex;
    align-items: center;
    gap: 10px;
    min-width: 0;
  }}
  .btn-drawer {{
    display: none;
    border: none;
    background: #FFFFFF;
    color: var(--ink);
    font-size: 13px;
    font-weight: 600;
    padding: 6px 12px;
    border-radius: 9px;
    box-shadow: 0 1px 3px rgba(24, 32, 44, 0.06), 0 0 0 1px rgba(43, 84, 138, 0.10);
    cursor: pointer;
    font-family: inherit;
  }}
  .cur-pill {{
    font-family: {FONT_MONO};
    font-size: 12px;
    font-weight: 700;
    padding: 4.5px 10px;
    border-radius: 999px;
    white-space: nowrap;
  }}
  .cur-title {{
    font-size: 13.5px;
    font-weight: 600;
    color: var(--ink);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 320px;
  }}
  .nav-arrows {{
    display: inline-flex;
    border-radius: 9px;
    overflow: hidden;
    background: rgba(255, 255, 255, 0.86);
    box-shadow: 0 1px 2px rgba(24, 32, 44, 0.04), 0 0 0 1px rgba(43, 84, 138, 0.09);
  }}
  .nav-arrows button {{
    border: none;
    background: transparent;
    color: var(--ink-sub);
    font-size: 13.5px;
    padding: 5px 10px;
    cursor: pointer;
    transition: background 0.14s, color 0.14s;
  }}
  .nav-arrows button:first-child {{ border-right: 1px solid rgba(43, 84, 138, 0.09); }}
  .nav-arrows button:hover:not(:disabled) {{ background: #F0F5FC; color: var(--indigo); }}
  .nav-arrows button:disabled {{ color: #9BA5B4; cursor: default; }}

  .seg {{
    display: inline-flex;
    background: rgba(43, 84, 138, 0.06);
    border-radius: 9px;
    padding: 3px;
  }}
  .seg button {{
    border: none;
    background: transparent;
    color: var(--ink-sub);
    font-size: 12.5px;
    font-weight: 600;
    padding: 5px 11px;
    border-radius: 7px;
    cursor: pointer;
    font-family: inherit;
    transition: all 0.16s;
  }}
  .seg button.active {{
    background: var(--paper);
    color: var(--ink);
    box-shadow: 0 1px 4px rgba(24, 32, 44, 0.09);
  }}
  .btn-ghost {{
    color: var(--ink-sub);
    text-decoration: none;
    font-size: 12.5px;
    font-weight: 600;
    padding: 6.5px 11px;
    border-radius: 9px;
    background: rgba(255, 255, 255, 0.85);
    box-shadow: 0 1px 2px rgba(24, 32, 44, 0.04), 0 0 0 1px rgba(43, 84, 138, 0.09);
    white-space: nowrap;
    transition: color 0.16s, box-shadow 0.16s, background 0.16s;
  }}
  .btn-ghost:hover {{
    color: var(--indigo);
    background: #FFFFFF;
    box-shadow: 0 2px 8px rgba(43, 84, 138, 0.12), 0 0 0 1px rgba(43, 84, 138, 0.24);
  }}
  .btn-copy {{
    background: linear-gradient(135deg, var(--indigo) 0%, #3768A6 100%);
    color: #FFFFFF;
    border: none;
    padding: 8px 15px;
    border-radius: 9px;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    font-family: inherit;
    white-space: nowrap;
    box-shadow: 0 2px 8px rgba(43, 84, 138, 0.22);
    transition: transform 0.15s, box-shadow 0.15s, background 0.15s;
  }}
  .btn-copy:hover {{
    transform: translateY(-0.5px);
    box-shadow: 0 4px 12px rgba(43, 84, 138, 0.30);
    background: linear-gradient(135deg, var(--indigo-hover) 0%, var(--indigo) 100%);
  }}
  .btn-copy.copied {{
    background: linear-gradient(135deg, #196473 0%, #247F91 100%);
  }}

  .stage-scroll {{
    flex: 1;
    overflow-y: auto;
    padding: 30px 22px 60px 22px;
  }}
  .stage-scroll::-webkit-scrollbar {{ width: 7px; }}
  .stage-scroll::-webkit-scrollbar-thumb {{ background: rgba(43, 84, 138, 0.16); border-radius: 99px; }}
  .wechat-frame {{
    max-width: 677px;
    margin: 0 auto;
    background: var(--paper);
    border-radius: 16px;
    box-shadow: 0 1px 2px rgba(24, 32, 44, 0.04), 0 18px 50px rgba(34, 52, 78, 0.09), 0 0 0 1px rgba(43, 84, 138, 0.06);
    overflow: hidden;
    transition: max-width 0.24s ease, border-radius 0.24s ease;
  }}
  .wechat-frame.mobile {{
    max-width: 390px;
    border: 10px solid #1C2533;
    border-radius: 36px;
    box-shadow: 0 22px 54px rgba(24, 32, 44, 0.20);
  }}
  .stage-pager {{
    max-width: 677px;
    margin: 22px auto 0 auto;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
  }}
  .stage-pager button {{
    background: var(--paper);
    border: none;
    color: var(--ink);
    font-size: 13px;
    font-weight: 600;
    padding: 9px 16px;
    border-radius: 10px;
    box-shadow: 0 1px 3px rgba(24, 32, 44, 0.05), 0 0 0 1px rgba(43, 84, 138, 0.08);
    cursor: pointer;
    font-family: inherit;
    transition: color 0.16s, box-shadow 0.16s, transform 0.16s;
  }}
  .stage-pager button:hover:not(:disabled) {{
    color: var(--indigo);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(43, 84, 138, 0.12), 0 0 0 1px rgba(43, 84, 138, 0.22);
  }}
  .stage-pager button:disabled {{
    background: #EFECE5;
    color: var(--ink-mute);
    box-shadow: none;
    cursor: default;
  }}
  .kbd-hint {{
    font-family: {FONT_MONO};
    font-size: 12px;
    color: var(--ink-mute);
  }}

  /* Drawer backdrop for narrow viewports */
  .drawer-backdrop {{
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(24, 32, 44, 0.30);
    backdrop-filter: blur(2px);
    z-index: 25;
  }}
  @media (max-width: 980px) {{
    .sidebar {{
      position: fixed;
      left: 0;
      top: 0;
      bottom: 0;
      transform: translateX(-100%);
      transition: transform 0.22s ease;
      box-shadow: 10px 0 36px rgba(24, 32, 44, 0.16);
    }}
    .sidebar.open {{ transform: translateX(0); }}
    .drawer-backdrop.open {{ display: block; }}
    .btn-drawer {{ display: inline-flex; align-items: center; }}
    .cur-title, .kbd-hint {{ display: none; }}
    .search-input {{ font-size: 16px; }}
  }}
  @media (max-width: 640px) {{
    .stage-toolbar {{ padding: 0 14px; }}
    .seg, .btn-ghost, .nav-arrows {{ display: none; }}
    .stage-scroll {{ padding: 0 0 44px 0; }}
    .wechat-frame, .wechat-frame.mobile {{ max-width: 100%; border-radius: 0; border: none; box-shadow: none; }}
    .stage-pager {{ padding: 0 14px; }}
  }}
</style>
</head>
<body>
<div class="app-shell">
  <div class="drawer-backdrop" id="drawerBackdrop" onclick="closeDrawer()"></div>
  <aside class="sidebar" id="sidebar">
    <div class="sidebar-header">
      <div class="series-kicker"><span class="kicker-dot"></span>DEEPSEEK-1.3B · 真机实测专刊</div>
      <h1>《掀开大模型的黑盒子》</h1>
      <p class="series-stats">全 {len(portal_eps)} 期连载 · 累计 {total_chars:,} 字 · {unique_figs} 张图鉴 · {len(INTERACTIVE_DEMOS)} 个交互实验</p>
      <div class="search-wrap">
        <input type="text" class="search-input" id="searchInput" placeholder="筛选期数、主题或交互实验…" oninput="filterEpisodes()" />
        <button type="button" class="search-clear" id="searchClear" onclick="clearSearch()" aria-label="清空筛选">×</button>
      </div>
    </div>
    <div class="ep-list" id="epList">
      {"".join(sidebar_parts_html)}
      {sidebar_labs_html}
      <div class="empty-filter" id="emptyFilter">没有匹配的期数或实验</div>
    </div>
  </aside>

  <main class="main-stage">
    <header class="stage-toolbar">
      <div class="tb-left">
        <button type="button" class="btn-drawer" onclick="openDrawer()">目录</button>
        <div class="nav-arrows">
          <button type="button" id="tbPrev" onclick="stepEp(-1)" title="上一期 (←)" aria-label="上一期">←</button>
          <button type="button" id="tbNext" onclick="stepEp(1)" title="下一期 (→)" aria-label="下一期">→</button>
        </div>
        <span class="cur-pill" id="curEpPill">第 01 / {len(portal_eps):02d} 期</span>
        <span class="cur-title" id="curEpTitle"></span>
      </div>
      <div class="tb-right">
        <div class="seg" role="group" aria-label="视口宽度切换">
          <button type="button" id="btnDesktop" class="active" onclick="setWidthMode(false)">公众号 677px</button>
          <button type="button" id="btnMobile" onclick="setWidthMode(true)">手机 390px</button>
        </div>
        <a class="btn-ghost" id="standaloneLink" href="html/ep01.html" target="_blank">独立页 ↗</a>
        <button type="button" class="btn-copy" id="copyBtn" onclick="copyCurrentEp()">复制公众号排版</button>
      </div>
      <div class="read-progress" id="readProgress"></div>
    </header>

    <div class="stage-scroll" id="stageScroll">
      <div class="wechat-frame" id="wechatFrame">
        {"".join(portal_articles)}
      </div>
      <div class="stage-pager">
        <button type="button" id="footPrev" onclick="stepEp(-1)">← 上一期</button>
        <span class="kbd-hint">快捷键：← / → 切换期数 · 样式已内联可直接粘贴至公众号</span>
        <button type="button" id="footNext" onclick="stepEp(1)">下一期 →</button>
      </div>
    </div>
  </main>
</div>

<script>
const EP_META = {ep_meta_json};
let currentEp = 1;

function updateProgress() {{
  const sc = document.getElementById('stageScroll');
  const max = sc.scrollHeight - sc.clientHeight;
  const pct = max > 0 ? Math.min(100, Math.max(0, (sc.scrollTop / max) * 100)) : 0;
  document.getElementById('readProgress').style.width = pct.toFixed(1) + '%';
}}

function selectEp(ep, pushHash = true) {{
  const meta = EP_META.find(e => e.ep === ep);
  if (!meta) return;
  currentEp = ep;
  document.querySelectorAll('.ep-item').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.ep-pane').forEach(el => el.style.display = 'none');
  const nav = document.getElementById('nav-ep-' + ep);
  const pane = document.getElementById('pane-ep-' + ep);
  if (nav) {{
    nav.classList.add('active');
    nav.scrollIntoView({{ block: 'nearest' }});
  }}
  if (pane) pane.style.display = 'block';

  const pad = String(ep).padStart(2, '0');
  const pill = document.getElementById('curEpPill');
  pill.textContent = '第 ' + pad + ' / ' + String(EP_META.length).padStart(2, '0') + ' 期';
  pill.style.color = meta.color;
  pill.style.background = meta.soft;

  document.getElementById('curEpTitle').textContent = meta.short_title;
  document.getElementById('standaloneLink').href = 'html/ep' + pad + '.html';

  document.getElementById('tbPrev').disabled = ep <= 1;
  document.getElementById('tbNext').disabled = ep >= EP_META.length;
  document.getElementById('footPrev').disabled = ep <= 1;
  document.getElementById('footNext').disabled = ep >= EP_META.length;

  document.getElementById('stageScroll').scrollTop = 0;
  updateProgress();
  closeDrawer();
  if (pushHash) history.replaceState(null, '', '#ep' + pad);
}}

function stepEp(delta) {{
  const next = currentEp + delta;
  if (next >= 1 && next <= EP_META.length) selectEp(next);
}}

function setWidthMode(isMobile) {{
  document.getElementById('wechatFrame').classList.toggle('mobile', isMobile);
  document.getElementById('btnDesktop').classList.toggle('active', !isMobile);
  document.getElementById('btnMobile').classList.toggle('active', isMobile);
  requestAnimationFrame(updateProgress);
}}

function openDrawer() {{
  document.getElementById('sidebar').classList.add('open');
  document.getElementById('drawerBackdrop').classList.add('open');
}}
function closeDrawer() {{
  document.getElementById('sidebar').classList.remove('open');
  document.getElementById('drawerBackdrop').classList.remove('open');
}}

function filterEpisodes() {{
  const input = document.getElementById('searchInput');
  const q = input.value.trim().toLowerCase();
  document.getElementById('searchClear').style.display = q ? 'block' : 'none';
  let visibleTotal = 0;
  document.querySelectorAll('.part-group').forEach(group => {{
    let groupVis = 0;
    group.querySelectorAll('.ep-item').forEach(btn => {{
      const match = !q || btn.dataset.search.includes(q);
      btn.style.display = match ? 'flex' : 'none';
      if (match) {{ groupVis++; visibleTotal++; }}
    }});
    group.style.display = groupVis > 0 ? 'block' : 'none';
  }});
  document.getElementById('emptyFilter').style.display = visibleTotal === 0 ? 'block' : 'none';
}}
function clearSearch() {{
  document.getElementById('searchInput').value = '';
  filterEpisodes();
}}

async function copyCurrentEp() {{
  const pane = document.getElementById('pane-ep-' + currentEp);
  const article = pane.querySelector('#wechat-article-body') || pane;
  const btn = document.getElementById('copyBtn');
  let ok = false;
  try {{
    if (navigator.clipboard && window.ClipboardItem) {{
      const htmlBlob = new Blob([article.outerHTML], {{ type: 'text/html' }});
      const textBlob = new Blob([article.innerText], {{ type: 'text/plain' }});
      await navigator.clipboard.write([new ClipboardItem({{ 'text/html': htmlBlob, 'text/plain': textBlob }})]);
      ok = true;
    }}
  }} catch (_) {{}}
  if (!ok) {{
    const range = document.createRange();
    range.selectNode(article);
    const sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(range);
    try {{ ok = document.execCommand('copy'); }} catch (_) {{}}
    if (ok) sel.removeAllRanges();
  }}
  btn.textContent = ok ? '已复制' : '请手动复制';
  btn.classList.toggle('copied', ok);
  setTimeout(() => {{
    btn.textContent = '复制公众号排版';
    btn.classList.remove('copied');
  }}, 2600);
}}

document.getElementById('stageScroll').addEventListener('scroll', updateProgress, {{ passive: true }});

document.addEventListener('keydown', (ev) => {{
  if (document.activeElement && ['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) return;
  if (ev.key === 'ArrowLeft') stepEp(-1);
  if (ev.key === 'ArrowRight') stepEp(1);
}});

function syncFromHash() {{
  const m = location.hash.match(/^#ep(\\d{{1,2}})$/i);
  const targetEp = m ? Math.min(EP_META.length, Math.max(1, parseInt(m[1], 10))) : 1;
  selectEp(targetEp, false);
}}
window.addEventListener('hashchange', syncFromHash);
syncFromHash();
</script>
</body>
</html>"""
    (ROOT / "index.html").write_text(portal_html, encoding="utf-8")


def main():
    portal_eps = []
    for meta in EPISODE_META:
        ep = meta["ep"]
        md_file = MD_DIR / f"ep{ep:02d}.md"
        if not md_file.exists():
            print(f"[WARN] Missing {md_file}")
            continue
        md_text = md_file.read_text(encoding="utf-8")

        standalone_data = md_to_wechat_html(md_text, meta, asset_prefix="../assets/")
        write_standalone_episode_html(standalone_data)

        portal_data = md_to_wechat_html(md_text, meta, asset_prefix="assets/")
        portal_eps.append(portal_data)

        print(f"[OK] html/ep{ep:02d}.html ({standalone_data['cjk_chars']:,} 字, ~{standalone_data['read_mins']} min) - {standalone_data['short_title']}")

    if portal_eps:
        write_master_portal(portal_eps)
        print(f"[DONE] index.html rebuilt with {len(portal_eps)} episodes.")


if __name__ == "__main__":
    main()
