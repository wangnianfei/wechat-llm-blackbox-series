# 《掀开大模型的黑盒子》全 15 期微信公众号硬核科普连载

> **面向高中理科基线读者的大语言模型底层原理与真机实验科普系列**  
> 实验底座：`deepseek-ai/deepseek-coder-1.3b-base`（32,256 词表 · 24 层 Transformer · 16 注意力头 · SwiGLU FFN · 13.46 亿参数）

---

## 🌐 在线预览与微信公众号一键排版工作台

- **在线总目录（GitHub Pages）**：<https://wangnianfei.github.io/wechat-llm-blackbox-series/>
- **全 15 期交互式预览 & 一键复制公众号富文本工作台**：[`index.html`](./index.html)
  - 支持 **手机视图 (390px)** 与 **微信公众号标准宽视图 (677px)** 一键切换；
  - 所有 CSS 样式均已内联化（`style="..."`），点击顶部 **「复制公众号排版」** 即可直接粘贴至微信公众号后台编辑器（`mp.weixin.qq.com`）。
- **全套创作 Prompt 指南（总控系统提示词 + 15 期连载大纲 + 单期生成模板）**：[`prompts/wechat_llm_series_prompt.md`](./prompts/wechat_llm_series_prompt.md)

---

## 🔬 交互实验室（Interactive Labs）

可直接在浏览器打开的零依赖交互演示网页，适合配合第 10–13 期科普文章与视频演示动手实验：

| 编号 | 实验名称 | 核心演示内容 | 在线体验（GitHub Pages） | 本地源码 |
| :--- | :--- | :--- | :--- | :--- |
| **LAB 01** | **2→2→1 神经网络激活函数直观演示** | 切换无激活 / ReLU / Sigmoid / SiLU / GELU / Tanh，实时看公式坍缩证明、2D 空间折弯与 XOR 梯度下降训练 | [在线打开演示 ↗](https://wangnianfei.github.io/wechat-llm-blackbox-series/demos/activation-221.html) | [activation-221.html](./demos/activation-221.html) |

---

## 📚 全 15 期连载目录（零倒挂因果丝滑流）

| 期数 | 所属模块 | 标题 | 微信公众号 HTML 排版页 | Markdown 源码 |
| :--- | :--- | :--- | :--- | :--- |
| **第 01 期** | 第一部分：破除黑盒与底层基石 | 大模型到底是什么？脱掉神秘外衣，它其实只是一个“超级函数” | [ep01.html](./html/ep01.html) | [ep01.md](./markdown/ep01.md) |
| **第 02 期** | 第一部分：破除黑盒与底层基石 | 别被满天飞的 AI 新词吓住！给高中生与初学者的 5 条硬核破局忠告 | [ep02.html](./html/ep02.html) | [ep02.md](./markdown/ep02.md) |
| **第 03 期** | 第二部分：从二进制到 Token 诞生 | 计算机为什么偏爱“反人类”的二进制？从电门开关到 UTF-8 的 243 字节之谜 | [ep03.html](./html/ep03.html) | [ep03.md](./markdown/ep03.md) |
| **第 04 期** | 第二部分：从二进制到 Token 诞生 | 为什么“我在”是一个词，“商店”却被劈成两半？揭秘大模型的 BPE 滚雪球造词法 | [ep04.html](./html/ep04.html) | [ep04.md](./markdown/ep04.md) |
| **第 05 期** | 第二部分：从二进制到 Token 诞生 | BPE、WordPiece 与 Unigram 三大流派华山论剑：透过算法差异看“底层思想” | [ep05.html](./html/ep05.html) | [ep05.md](./markdown/ep05.md) |
| **第 06 期** | 第三部分：张量与几何空间表示语义 | 从 1 个数字到 45 个词的三维魔方：一文看懂大模型里的“张量（Tensor）”是如何堆叠出来的 | [ep06.html](./html/ep06.html) | [ep06.md](./markdown/ep06.md) |
| **第 07 期** | 第三部分：张量与几何空间表示语义 | 大模型的数学秘密：为什么说千亿参数的本质，只是空间里的“拉伸、旋转”与“点积靠近”？ | [ep07.html](./html/ep07.html) | [ep07.md](./markdown/ep07.md) |
| **第 08 期** | 第四部分：分层解剖 Transformer | 词语接龙的灵魂：每一层如何把前文语境“注入”当前词？（分层输入输出全追踪） | [ep08.html](./html/ep08.html) | [ep08.md](./markdown/ep08.md) |
| **第 09 期** | 第四部分：分层解剖 Transformer | 真机解剖“我在苹果公司吃了一个苹果”：16 个注意力头究竟在看什么？（附实测全表） | [ep09.html](./html/ep09.html) | [ep09.md](./markdown/ep09.md) |
| **第 10 期** | 第五部分：FFN 知识库与激活函数本质 | 上完课还要回家复习：为什么说大模型 2/3 的世界知识都藏在 FFN 前馈层？ | [ep10.html](./html/ep10.html) | [ep10.md](./markdown/ep10.md) |
| **第 11 期** | 第五部分：FFN 知识库与激活函数本质 | 为什么叫“激活”？亲手解剖 2→2→1 极简网络，看清 100 层坍缩成 1 层的真相 | [ep11.html](./html/ep11.html) | [ep11.md](./markdown/ep11.md) |
| **第 12 期** | 第六部分：训练、梯度进化与终极闭环 | 万物始于一张“随机噪音表”：大模型是怎么从胡言乱语练出真实语义的？ | [ep12.html](./html/ep12.html) | [ep12.md](./markdown/ep12.md) |
| **第 13 期** | 第六部分：训练、梯度进化与终极闭环 | 从 Sigmoid 到 SwiGLU：一场围绕“梯度生死”的激活函数十年进化史 | [ep13.html](./html/ep13.html) | [ep13.md](./markdown/ep13.md) |
| **第 14 期** | 第六部分：训练、梯度进化与终极闭环 | 训练与推理大不同！为什么聊天时大模型的 Embedding 词表早已“彻底冻结”？ | [ep14.html](./html/ep14.html) | [ep14.md](./markdown/ep14.md) |
| **第 15 期** | 第六部分：训练、梯度进化与终极闭环 | 大结局·一句话的奇幻漂流：从敲下键盘的二进制电流，到吐出下一个词的完整张量之旅 | [ep15.html](./html/ep15.html) | [ep15.md](./markdown/ep15.md) |

---

## 🗂️ 仓库目录结构

```text
├── index.html                        # 全 15 期微信公众号排版预览与一键复制总工作台
├── demos/                            # 独立交互演示实验室网页 (activation-221.html 等)
├── html/                             # 15 期独立微信公众号内联 CSS 推文网页 (ep01.html ~ ep15.html)
├── markdown/                         # 15 期 Markdown 源文件 (含内联 SVG 矢量图与实验数据表)
├── assets/                           # 300-DPI 高清真机实验配图 (R ggplot2/patchwork 渲染)
├── data/                             # DeepSeek-1.3B 真机实验导出数据集 (JSON & CSV)
├── prompts/                          # 全系列创作总控 System Prompt 与 15 期课程规划蓝图
└── scripts/                          # 复现实验、R 制图与微信公众号 HTML 排版构建脚本
```
