#!/usr/bin/env python3
"""
Prepare comprehensive experimental materials from local DeepSeek-Coder-1.3B-Base
for all 12 episodes of the WeChat Official Account popular science series:
《掀开大模型的黑盒子》
"""
import json
import math
import pathlib
import csv
import torch
import torch.nn.functional as F
from transformers import AutoModelForCausalLM, AutoTokenizer

ROOT = pathlib.Path(__file__).resolve().parent
MODEL_DIR = ROOT / "ds13b"
OUT_DIR = ROOT / "wechat_articles" / "data"
OUT_DIR.mkdir(parents=True, exist_ok=True)

torch.manual_seed(42)
device = "mps" if torch.backends.mps.is_available() else "cpu"
print(f"[INFO] Running material preparation on device={device}")

tok = AutoTokenizer.from_pretrained(str(MODEL_DIR))
model = AutoModelForCausalLM.from_pretrained(
    str(MODEL_DIR),
    dtype=torch.bfloat16,
    low_cpu_mem_usage=True,
    attn_implementation="eager",
).to(device).eval()

E = model.model.embed_tokens.weight.detach().cpu().float()  # [32256, 2048]

def cos_sim(a, b):
    return float(F.cosine_similarity(a.float().view(1, -1), b.float().view(1, -1)).item())

def angle_deg(a, b):
    c = max(-1.0, min(1.0, cos_sim(a, b)))
    return round(math.degrees(math.acos(c)), 2)

# ==============================================================================
# 1. Episode 3 Material: Binary & UTF-8 243 vs 13 Illegal Bytes Breakdown
# ==============================================================================
sample_chars = ["A", "0", "我", "在", "苹", "果"]
utf8_table = []
for ch in sample_chars:
    raw = ch.encode("utf-8")
    hex_str = " ".join(f"0x{b:02X}" for b in raw)
    bin_str = " ".join(f"{b:08b}" for b in raw)
    dec_list = [int(b) for b in raw]
    utf8_table.append({
        "char": ch,
        "unicode_codepoint": f"U+{ord(ch):04X}",
        "byte_count": len(raw),
        "decimal_bytes": dec_list,
        "hex_bytes": hex_str,
        "binary_bits": bin_str,
    })

# ==============================================================================
# 2. Episode 6 Material: 0D Scalar -> 1D Token -> 2D [45, 2048] -> 3D Tensor Cube
# ==============================================================================
# Construct a clean Chinese passage that tokenizes to EXACTLY 45 tokens in DeepSeek 1.3B
base_passage = (
    "我在苹果公司吃了一个苹果，发现大模型其实并不神秘：它只是一个把词元转化为高维语义张量、"
    "再通过层层注意力计算预测下一个词概率的超级数学函数。"
)
p_ids = tok(base_passage, add_special_tokens=False).input_ids
# Adjust to exact 45 tokens
while len(p_ids) < 45:
    base_passage += "加油！"
    p_ids = tok(base_passage, add_special_tokens=False).input_ids
p_ids_45 = p_ids[:45]
p_tokens_45 = [tok.decode([i]) for i in p_ids_45]
passage_45_text = "".join(p_tokens_45)

with torch.no_grad():
    t_45 = E[p_ids_45]  # [45, 2048]

apple_tid = tok("苹果", add_special_tokens=False).input_ids[0]
fruit_tid = tok("水果", add_special_tokens=False).input_ids[0]
scalar_dot = float(torch.dot(E[apple_tid], E[fruit_tid]).item())

ep06_tensor_stacking = {
    "passage_45_text": passage_45_text,
    "token_count": len(p_ids_45),
    "tokens_45_preview": [
        {"pos": idx + 1, "token": t, "id": int(i), "l2_norm": round(float(E[i].norm()), 3)}
        for idx, (t, i) in enumerate(zip(p_tokens_45, p_ids_45))
    ],
    "hierarchy": [
        {
            "dim": "0D 标量 (Scalar)",
            "shape": "()",
            "element_count": 1,
            "fp16_bytes": 2,
            "meaning": "单个数字（如“苹果”与“水果”的点积得分或温度参数）",
            "real_example": f"dot(E['苹果'], E['水果']) = {scalar_dot:.4f}",
        },
        {
            "dim": "1D 向量 (Vector)",
            "shape": "(2048,)",
            "element_count": 2048,
            "fp16_bytes": 2048 * 2,
            "meaning": "1 个 Token（如“苹果” id=17144）的 2048 维语义特征长条",
            "real_example": f"前6维: {[round(float(x), 4) for x in E[apple_tid][:6].tolist()]}",
        },
        {
            "dim": "2D 矩阵 (Matrix)",
            "shape": "(45, 2048)",
            "element_count": 45 * 2048,
            "fp16_bytes": 45 * 2048 * 2,
            "meaning": "1 段话 45 个 Token 并排堆叠成的“语义平面”",
            "real_example": f"45 行 × 2048 列 = 92,160 个浮点数 (约 180 KB)",
        },
        {
            "dim": "3D 张量·多头视角 (Multi-Head 3D Tensor)",
            "shape": "(45, 16, 128)",
            "element_count": 45 * 16 * 128,
            "fp16_bytes": 45 * 16 * 128 * 2,
            "meaning": "把 45 个词的 2048 维切分成 16 个注意力头（每头 128 维）堆成的三维魔方",
            "real_example": "45(词长) × 16(视角头) × 128(子空间维度) = 92,160 个浮点数",
        },
        {
            "dim": "3D 张量·批次视角 (Batch 3D Tensor)",
            "shape": "(4, 45, 2048)",
            "element_count": 4 * 45 * 2048,
            "fp16_bytes": 4 * 45 * 2048 * 2,
            "meaning": "GPU 同时并行处理 4 段长度为 45 的句子堆叠成的三维语义立方体",
            "real_example": "4(句子数) × 45(词数) × 2048(维度) = 368,640 个浮点数 (约 720 KB)",
        },
        {
            "dim": "4D 张量·批量多头 (Batch Multi-Head 4D Tensor)",
            "shape": "(4, 16, 45, 128)",
            "element_count": 4 * 16 * 45 * 128,
            "fp16_bytes": 4 * 16 * 45 * 128 * 2,
            "meaning": "4 句话在 16 个注意力头中同时计算 Q/K/V 时的四维超立方体",
            "real_example": "4(Batch) × 16(Heads) × 45(Tokens) × 128(HeadDim)",
        },
    ],
}

# Save CSV for Ep06 plotting
with open(OUT_DIR / "ep06_tensor_45_tokens.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["pos", "token", "token_id", "l2_norm", "dim1", "dim2", "dim3", "dim4"])
    for idx, (t, i) in enumerate(zip(p_tokens_45, p_ids_45)):
        vec = E[i]
        w.writerow([
            idx + 1, t, int(i), round(float(vec.norm()), 4),
            round(float(vec[0]), 4), round(float(vec[1]), 4),
            round(float(vec[2]), 4), round(float(vec[3]), 4)
        ])

# ==============================================================================
# 3. Episode 7 Material: Math & Geometry (Linear Stretch/Rotate, Non-linear, Dot Product)
# ==============================================================================
def tid_of(w):
    return tok(w, add_special_tokens=False).input_ids[0]

torch.manual_seed(42)
E_rand = torch.randn_like(E) * E.std()

geo_pairs = [
    ("苹果", "水果", "同属水果语义簇"),
    ("苹果", "公司", "科技巨头搭配簇"),
    ("苹果", "手机", "数码产品语义簇"),
    ("吃", "喝", "饮食动作高频共现"),
    ("猫", "狗", "宠物名词高频共现"),
    ("北京", "上海", "中国核心城市共现"),
    ("大", "小", "反义词共享修饰语境"),
    ("苹果", "微积分", "跨界无关词对"),
    ("吃", "二进制", "跨界无关词对"),
]

dot_product_table = []
for w1, w2, note in geo_pairs:
    i1, i2 = tid_of(w1), tid_of(w2)
    v1, v2 = E[i1], E[i2]
    r1, r2 = E_rand[i1], E_rand[i2]
    dot_tr = float(torch.dot(v1, v2).item())
    cos_tr = cos_sim(v1, v2)
    ang_tr = angle_deg(v1, v2)
    dot_ra = float(torch.dot(r1, r2).item())
    cos_ra = cos_sim(r1, r2)
    ang_ra = angle_deg(r1, r2)
    dot_product_table.append({
        "pair": f"{w1} ↔ {w2}",
        "w1": w1, "w2": w2,
        "id1": int(i1), "id2": int(i2),
        "norm1": round(float(v1.norm()), 2),
        "norm2": round(float(v2.norm()), 2),
        "trained_dot": round(dot_tr, 2),
        "trained_cos": round(cos_tr, 4),
        "trained_angle_deg": ang_tr,
        "random_dot": round(dot_ra, 2),
        "random_cos": round(cos_ra, 4),
        "random_angle_deg": ang_ra,
        "note": note,
    })

with open(OUT_DIR / "ep07_dot_product_geometry.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(dot_product_table[0].keys()))
    w.writeheader()
    w.writerows(dot_product_table)

# Measure actual Layer 0 Linear & Non-Linear transformations on "苹果" vector
with torch.no_grad():
    v_apple = E[apple_tid].to(device).to(torch.bfloat16)
    lyr0 = model.model.layers[0]
    v_normed = lyr0.input_layernorm(v_apple.unsqueeze(0)).squeeze(0)
    v_q = lyr0.self_attn.q_proj(v_normed)
    v_k = lyr0.self_attn.k_proj(v_normed)
    v_v = lyr0.self_attn.v_proj(v_normed)
    v_up = lyr0.mlp.up_proj(v_normed)
    v_gate = lyr0.mlp.gate_proj(v_normed)
    v_silu = F.silu(v_gate)

linear_nonlinear_stats = {
    "raw_embedding_norm": round(float(v_apple.float().norm()), 3),
    "after_rmsnorm_norm": round(float(v_normed.float().norm()), 3),
    "q_proj_linear": {
        "matrix_shape": "[2048, 2048]",
        "output_norm": round(float(v_q.float().norm()), 3),
        "stretch_factor_vs_normed": round(float(v_q.float().norm() / v_normed.float().norm()), 3),
        "rotation_angle_deg": angle_deg(v_normed.cpu(), v_q.cpu()),
    },
    "k_proj_linear": {
        "matrix_shape": "[2048, 2048]",
        "output_norm": round(float(v_k.float().norm()), 3),
        "stretch_factor_vs_normed": round(float(v_k.float().norm() / v_normed.float().norm()), 3),
        "rotation_angle_deg": angle_deg(v_normed.cpu(), v_k.cpu()),
    },
    "v_proj_linear": {
        "matrix_shape": "[2048, 2048]",
        "output_norm": round(float(v_v.float().norm()), 3),
        "stretch_factor_vs_normed": round(float(v_v.float().norm() / v_normed.float().norm()), 3),
        "rotation_angle_deg": angle_deg(v_normed.cpu(), v_v.cpu()),
    },
    "mlp_gate_to_silu_nonlinear": {
        "gate_linear_shape": "[2048 -> 5504]",
        "before_silu_negative_dims": int((v_gate.float() < 0).sum().item()),
        "before_silu_positive_dims": int((v_gate.float() > 0).sum().item()),
        "before_silu_min": round(float(v_gate.float().min()), 3),
        "after_silu_min": round(float(v_silu.float().min()), 3),
        "before_silu_norm": round(float(v_gate.float().norm()), 3),
        "after_silu_norm": round(float(v_silu.float().norm()), 3),
        "direction_change_deg": angle_deg(v_gate.cpu(), v_silu.cpu()),
    }
}

# ==============================================================================
# 4. Episode 8 & 9 Material: Layer-by-Layer Tensor I/O & Multi-Head Attention Full Table
# ==============================================================================
MAIN_SENT = "我在苹果公司吃了一个苹果"
main_ids = tok(MAIN_SENT, return_tensors="pt", add_special_tokens=False).input_ids.to(device)
main_tokens = [tok.decode([int(i)]) for i in main_ids[0]]
# Tokens: ['我在', '苹果', '公司', '吃', '了一个', '苹果'] (indices 0..5)

with torch.no_grad():
    out = model(main_ids, use_cache=False, output_hidden_states=True, output_attentions=True)

# Detailed single-layer internal tensor I/O trace on Layer 0 for "我在苹果公司吃了一个苹果" ([1, 6, 2048])
with torch.no_grad():
    h0 = out.hidden_states[0]  # [1, 6, 2048]
    l0 = model.model.layers[0]
    h_norm1 = l0.input_layernorm(h0)
    q0 = l0.self_attn.q_proj(h_norm1)
    k0 = l0.self_attn.k_proj(h_norm1)
    v0 = l0.self_attn.v_proj(h_norm1)
    # After attention block before MLP:
    att_weights_0 = out.attentions[0]  # [1, 16, 6, 6]
    h1_full = out.hidden_states[1]     # [1, 6, 2048]

layer0_internal_trace = [
    {
        "step": "0. 词表查表输出 (Embedding)",
        "math_type": "查表映射 (Lookup)",
        "input_shape": "[1, 6] (Token IDs)",
        "weight_shape": "[32256, 2048]",
        "output_shape": "[1, 6, 2048]",
        "apple1_norm": round(float(h0[0, 1].float().norm()), 2),
        "apple2_norm": round(float(h0[0, 5].float().norm()), 2),
        "apple12_cos": round(cos_sim(h0[0, 1].cpu(), h0[0, 5].cpu()), 4),
        "role": "把 6 个词编号变成 6 条 2048 维初始向量（此时两个“苹果”完全相同）",
    },
    {
        "step": "1. 层归一化 (RMSNorm)",
        "math_type": "非线性缩放 + 线性缩放",
        "input_shape": "[1, 6, 2048]",
        "weight_shape": "[2048]",
        "output_shape": "[1, 6, 2048]",
        "apple1_norm": round(float(h_norm1[0, 1].float().norm()), 2),
        "apple2_norm": round(float(h_norm1[0, 5].float().norm()), 2),
        "apple12_cos": round(cos_sim(h_norm1[0, 1].cpu(), h_norm1[0, 5].cpu()), 4),
        "role": "把每条向量长度校准到统一量级，防止多层计算数值爆炸",
    },
    {
        "step": "2. Q/K/V 线性投影 (Linear Projections)",
        "math_type": "纯线性变换 (拉伸+旋转)",
        "input_shape": "[1, 6, 2048]",
        "weight_shape": "3 × [2048, 2048]",
        "output_shape": "Q,K,V 各 [1, 6, 2048]",
        "apple1_norm": round(float(q0[0, 1].float().norm()), 2),
        "apple2_norm": round(float(q0[0, 5].float().norm()), 2),
        "apple12_cos": round(cos_sim(q0[0, 1].cpu(), q0[0, 5].cpu()), 4),
        "role": "把每个词旋转投影出三种身份：找人的问题(Q)、被找的标签(K)、携带的干货(V)",
    },
    {
        "step": "3. 切分 16 个注意力头 + RoPE 位置旋转",
        "math_type": "维度重排 + 几何旋转",
        "input_shape": "[1, 6, 2048]",
        "weight_shape": "无参数 (旋转角矩阵)",
        "output_shape": "[1, 16, 6, 128]",
        "apple1_norm": round(float(q0[0, 1].float().norm()), 2),
        "apple2_norm": round(float(q0[0, 5].float().norm()), 2),
        "apple12_cos": "按位置旋转分离",
        "role": "把 2048 维劈成 16 个 128 维独立视角，并按词的位置序号旋转不同角度",
    },
    {
        "step": "4. 注意力打分与 Softmax 概率化",
        "math_type": "点积 + 非线性变换(Softmax)",
        "input_shape": "Q,K: [1, 16, 6, 128]",
        "weight_shape": "因果掩码 (上三角 -∞)",
        "output_shape": "注意力矩阵 [1, 16, 6, 6]",
        "apple1_norm": "行概率和 = 1.00",
        "apple2_norm": "行概率和 = 1.00",
        "apple12_cos": "关注视野不同",
        "role": "计算前文每个词对当前词的影响权重（第 2 个苹果看到了“公司”和“吃”）",
    },
    {
        "step": "5. 语境加权求和 + 多头合并投影 + 残差相加",
        "math_type": "线性组合 + 线性投影",
        "input_shape": "[1, 16, 6, 6] × [1, 16, 6, 128]",
        "weight_shape": "W_o: [2048, 2048]",
        "output_shape": "[1, 6, 2048]",
        "apple1_norm": "语境已注入",
        "apple2_norm": "语境已注入",
        "apple12_cos": "开始分道扬镳",
        "role": "把 16 个头提取到的前文语境汇总，注入回每个词自己的向量里",
    },
    {
        "step": "6. SwiGLU 前馈网络 (MLP 升维激活再降维)",
        "math_type": "线性升维 -> SiLU非线性 -> 线性降维",
        "input_shape": "[1, 6, 2048] -> [1, 6, 5504]",
        "weight_shape": "up/gate [2048,5504], down [5504,2048]",
        "output_shape": "[1, 6, 2048] (第1层最终输出)",
        "apple1_norm": round(float(h1_full[0, 1].float().norm()), 2),
        "apple2_norm": round(float(h1_full[0, 5].float().norm()), 2),
        "apple12_cos": round(cos_sim(h1_full[0, 1].cpu(), h1_full[0, 5].cpu()), 4),
        "role": "在 5504 维高维空间做非线性知识加工，输出第 1 层崭新的语义张量",
    },
]

# Scan ALL 24 layers x 16 heads to build a comprehensive Multi-Head Attention Catalog for Ep 9!
# Sentence tokens: 0:'我在', 1:'苹果₁', 2:'公司', 3:'吃', 4:'了一个', 5:'苹果₂'
head_profiles = []
for l_idx, att_l in enumerate(out.attentions):
    mat = att_l[0].detach().cpu().float()  # [16, 6, 6]
    for h_idx in range(16):
        # Row 5 (苹果₂ at pos 5 looking at 0..5):
        r5 = [round(float(x), 4) for x in mat[h_idx, 5].tolist()]
        # Row 2 (公司 at pos 2 looking at 0..2):
        r2 = [round(float(x), 4) for x in mat[h_idx, 2].tolist()]
        # Row 3 (吃 at pos 3 looking at 0..3):
        r3 = [round(float(x), 4) for x in mat[h_idx, 3].tolist()]
        head_profiles.append({
            "layer": l_idx + 1,  # 1-indexed for high-school reader friendliness (Layer 1..24)
            "layer_0idx": l_idx,
            "head": h_idx + 1,   # 1-indexed (Head 1..16)
            "head_0idx": h_idx,
            # Where does 苹果₂ (pos 5) look?
            "apple2_to_wozai": r5[0],
            "apple2_to_apple1": r5[1],
            "apple2_to_gongsi": r5[2],
            "apple2_to_chi": r5[3],
            "apple2_to_leyige": r5[4],
            "apple2_to_self": r5[5],
            # Where does 公司 (pos 2) look?
            "gongsi_to_wozai": r2[0],
            "gongsi_to_apple1": r2[1],
            "gongsi_to_self": r2[2],
            # Where does 吃 (pos 3) look?
            "chi_to_wozai": r3[0],
            "chi_to_apple1": r3[1],
            "chi_to_gongsi": r3[2],
            "chi_to_self": r3[3],
        })

# Save all 384 heads to CSV so students/readers and R script have the full dataset
with open(OUT_DIR / "ep09_all_384_heads.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(head_profiles[0].keys()))
    w.writeheader()
    w.writerows(head_profiles)

# Select top representative heads across different functional archetypes for Episode 9 tables
top_chi_heads = sorted(head_profiles, key=lambda x: x["apple2_to_chi"], reverse=True)[:5]
top_leyige_heads = sorted(head_profiles, key=lambda x: x["apple2_to_leyige"], reverse=True)[:5]
top_gongsi_apple1_heads = sorted(head_profiles, key=lambda x: x["gongsi_to_apple1"], reverse=True)[:5]
top_apple2_apple1_heads = sorted(head_profiles, key=lambda x: x["apple2_to_apple1"], reverse=True)[:5]
top_apple2_gongsi_heads = sorted(head_profiles, key=lambda x: x["apple2_to_gongsi"], reverse=True)[:5]

# Also extract all 16 heads of Layer 1 (layer_0idx=0) and Layer 3 (layer_0idx=2) for a full 16-head table!
layer1_all_16_heads = [p for p in head_profiles if p["layer_0idx"] == 0]
layer3_all_16_heads = [p for p in head_profiles if p["layer_0idx"] == 2]

# ==============================================================================
# 5. Episode 10 Material: 4-Step Training Simulation (From Random Noise to Semantic Cluster)
# ==============================================================================
# Demonstrate on a mini 5-word embedding table (dim=2048, initialized with the exact random Gaussian std of ds13b)
# how 4 training iterations + 50 iterations of next-word prediction Loss & Gradient Descent
# pull "苹果" and "水果" / "吃" closer while pushing unrelated words apart!
torch.manual_seed(2026)
sim_words = ["吃", "苹果", "水果", "喝", "微积分"]
sim_emb = torch.nn.Parameter(torch.randn(len(sim_words), 2048) * float(E.std()))
opt = torch.optim.SGD([sim_emb], lr=2.5)

training_trace = []
for step in range(61):
    # Context "吃" (idx 0) should predict "苹果" (idx 1) or "水果" (idx 2), and "苹果" (1) aligns with "水果" (2)
    v_eat = sim_emb[0]
    logits_eat = v_eat @ sim_emb.T  # dot products with all 5 words
    probs_eat = F.softmax(logits_eat, dim=0)
    # Target: high score for "苹果"(1) and "水果"(2)
    loss = -0.5 * (torch.log(probs_eat[1] + 1e-9) + torch.log(probs_eat[2] + 1e-9))
    # Also context similarity between "苹果"(1) and "水果"(2)
    logits_apple = sim_emb[1] @ sim_emb.T
    probs_apple = F.softmax(logits_apple, dim=0)
    loss = loss - torch.log(probs_apple[2] + 1e-9)

    if step in (0, 1, 2, 5, 15, 30, 60):
        with torch.no_grad():
            c_eat_apple = cos_sim(sim_emb[0], sim_emb[1])
            c_apple_fruit = cos_sim(sim_emb[1], sim_emb[2])
            c_apple_calc = cos_sim(sim_emb[1], sim_emb[4])
            training_trace.append({
                "step": step,
                "loss": round(float(loss.item()), 4),
                "prob_eat_to_apple": round(float(probs_eat[1].item()) * 100, 2),
                "cos_eat_apple": round(c_eat_apple, 4),
                "angle_eat_apple_deg": angle_deg(sim_emb[0], sim_emb[1]),
                "cos_apple_fruit": round(c_apple_fruit, 4),
                "angle_apple_fruit_deg": angle_deg(sim_emb[1], sim_emb[2]),
                "cos_apple_calculus": round(c_apple_calc, 4),
                "angle_apple_calculus_deg": angle_deg(sim_emb[1], sim_emb[4]),
            })
    opt.zero_grad()
    loss.backward()
    opt.step()

# Combine with existing experiment_results.json
existing_json = json.loads((ROOT / "experiment_results.json").read_text(encoding="utf-8"))

materials = {
    "ep01_overview": {
        "model_name": existing_json["model_name"],
        "total_params": existing_json["param_budget"]["total_params"],
        "total_tensors": existing_json["param_budget"]["total_tensors"],
        "layers": existing_json["param_budget"]["layers"],
        "hidden_size": existing_json["param_budget"]["hidden_size"],
        "num_heads": existing_json["param_budget"]["num_heads"],
        "head_dim": existing_json["param_budget"]["head_dim"],
        "vocab_size": existing_json["param_budget"]["vocab_size"],
        "main_sentence": MAIN_SENT,
        "main_tokens": existing_json["main_tokens"],
        "generation_steps": existing_json["generation_steps"],
        "generation_full": existing_json["generation_full"],
    },
    "ep03_binary_utf8": {
        "utf8_table": utf8_table,
        "initial_utf8_bytes_count": 243,
        "forbidden_rfc3629_bytes_count": 13,
        "forbidden_bytes_hex": ["0xC0", "0xC1", "0xF5", "0xF6", "0xF7", "0xF8", "0xF9", "0xFA", "0xFB", "0xFC", "0xFD", "0xFE", "0xFF"],
        "forbidden_token_ids": "32000..32012",
    },
    "ep06_tensor_stacking": ep06_tensor_stacking,
    "ep07_math_geometry": {
        "dot_product_table": dot_product_table,
        "linear_nonlinear_stats": linear_nonlinear_stats,
    },
    "ep08_layer_tracking": {
        "layer0_internal_trace": layer0_internal_trace,
        "layer_evolution": existing_json["layer_evolution"],
        "param_buckets": existing_json["param_budget"]["buckets"],
    },
    "ep09_multihead_attention": {
        "tokens": main_tokens,
        "top_chi_heads": top_chi_heads,
        "top_leyige_heads": top_leyige_heads,
        "top_gongsi_apple1_heads": top_gongsi_apple1_heads,
        "top_apple2_apple1_heads": top_apple2_apple1_heads,
        "top_apple2_gongsi_heads": top_apple2_gongsi_heads,
        "layer1_all_16_heads": layer1_all_16_heads,
        "layer3_all_16_heads": layer3_all_16_heads,
        "best_eat_head_full": existing_json["attention"]["best_eat_head"],
    },
    "ep10_training": {
        "training_simulation_trace": training_trace,
        "random_vs_trained_pairs": existing_json["random_vs_trained"]["semantic_pairs"],
        "nn_random_mean": existing_json["random_vs_trained"]["nn_random_mean"],
        "nn_trained_mean": existing_json["random_vs_trained"]["nn_trained_mean"],
    },
    "ep11_frozen_inference": {
        "frozen_weights_proof": existing_json["frozen_weights"],
        "static_embedding": existing_json["static_embedding"],
        "context_control_disambig": existing_json["context_control_disambig"],
    },
    "ep12_finale": {
        "hallucination_probe": existing_json["hallucination"],
    },
}

out_file = OUT_DIR / "wechat_series_materials.json"
out_file.write_text(json.dumps(materials, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"[DONE] Wrote comprehensive materials JSON to {out_file} ({out_file.stat().st_size / 1024:.1f} KB)")
print("Top 3 Verb-Object ('苹果₂' -> '吃') Heads:", [(h['layer'], h['head'], h['apple2_to_chi']) for h in top_chi_heads[:3]])
print("Top 3 Brand-Modifier ('公司' -> '苹果₁') Heads:", [(h['layer'], h['head'], h['gongsi_to_apple1']) for h in top_gongsi_apple1_heads[:3]])
print("Top 3 Twin-Echo ('苹果₂' -> '苹果₁') Heads:", [(h['layer'], h['head'], h['apple2_to_apple1']) for h in top_apple2_apple1_heads[:3]])
