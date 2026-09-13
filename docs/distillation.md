# 蒸馏技术与证据说明

这份说明对应 `lab-ultra-unified-20260910-r2` 的运行时资源，以及开发仓库中已经记录的离线工作。发行目录包含 20 模块运行时，下面提到的离线研究源码路径属于开发仓库，未全部复制到本目录。

## 版式数据如何产生

开发仓库的 `layout-lab/` 负责解析和研究，排版 Skill 负责运行时应用。原生 PDF 提取文字、页码、块、行、span、边界框、字体、字号和基线；扫描件使用 OCR。共同几何重测对两类来源采用统一的坐标归一化和文字筛选，同时保留来源差异。

语义模型收到结构化文本及其已有测量，判断块的角色、关系和置信度。坐标、字号、缩进等值不由文本模型估计。原生几何可支持细粒度字体分析；OCR 宏观几何的证据能力较弱，像素行高不能直接充当 pt 字号。

| 信息 | 表示 | 用途 |
| --- | --- | --- |
| 内容在做什么 | 多轴语义与 SemanticGraph | 描述结构角色和内容关系 |
| 排版器可以改什么 | 有边界的 Style Tokens | 控制字体比例、行距、间隔等 |
| 页面表现怎样 | 多项布局指标 | 检查密度、留白、溢出和其他质量属性 |

统计先在每篇论文内汇总，再按篇比较。对语义关联进行同文、同角色控制，按整篇论文分组验证，降低出版模板混杂的影响。代表样式使用实际观测的多变量 medoid，保留对应的样本身份。

源码定位：`layout-lab/src/layout_lab/`、`tools/redistill_layout.py`、`tools/redistill_award_layout.py`、`tools/redistill_layout_weighting.py`。依赖定义位于 `layout-lab/pyproject.toml`：Python 3.12+、NumPy、pandas、pdfplumber、Pillow、Pydantic，Parquet / DuckDB 为可选依赖。

## 两个布局口径

国赛优先的共同几何校准纳入 64 篇获奖展示稿和 752 个期刊身份，分别分配 0.60 / 0.40 总质量，组内按篇等权。64 篇国赛稿全部有正文候选几何，期刊为 750 / 752，两篇缺失没有填零。

在 0.60 权重下，文本外包络面积的加权中位数为 0.5108075，左右文本边界比例为 0.112 / 0.115。外包络不等于实际墨迹面积，边界比例也不能直接替换 LaTeX 页边距。权重敏感性和逐年留出已经计算，但 `runtime_transfer_eligible` 仍为 `false`。具体方法及限制见[国赛布局校准](../skills/lab-ultra-typesetter/references/award-layout-calibration.md)。

期刊发现语料中的 752 个身份，只有 21 个达到 `publisher-final` 来源锚点要求。后续 v2.1 研究没有得到符合运行时导出条件的新共识因子或语义效应。当前使用的 `journal-dense-cn-v1` 是作者明确选择的旧版投影，记录为 `legacy_unverified_v1`，不能称作 v2.1 认证结果。参见[默认策略](../skills/lab-ultra-typesetter/references/aesthetic-policy.md)。

## 内容蒸馏的处理单元

资料先登记角色和来源。题面、论文正文、教师评述、附录、书籍章节以及混排的其他文章分别处理；同一作品的多个 OCR 版本不会自动变成多个独立支持。

`full-distillation/api_distill.py` 为转换文本建立任务。长文按连续字符区间切分，保留全局行号；map 阶段生成局部论证与候选，reduce 阶段汇总，audit 阶段复核。程序检查引用的起止区间、引文匹配和实际输入块，汇总时检查引文是否继承自上游证据。

候选对象包括以下字段，名称来自实际提取代码：

| 字段 | 内容 |
| --- | --- |
| `start` / `end` | 原文起止行号 |
| `quote` | 对应区间内的短引文 |
| `observation` | 作者具体使用的表达动作 |
| `reader_benefit` | 帮助读者理解什么 |
| `transfer` | 可以迁移的写法 |
| `limits` | 适用边界与反例 |

文档报告还包含 `identity`、`argument_map`、`roles`、`do_not_inherit` 和 `unresolved`。没有合适的写作动作时，允许候选为空。

SQLite 保存文档和任务状态，配合并发执行、重试与预算预留。输入、输出和来源以哈希关联。JSON 和引文检查能发现格式错误与定位错误，语义是否正确仍须另行回读原文。

## 从候选到运行时技巧

1. 对照来源检查候选，处理作者角色、公式缺失、结论夸大和引用错位。
2. 按表达动作归并通用技巧，保留不同适用条件的细分。
3. 给每个候选登记采用或排除去向。常见、同义或暂时分类困难，不自动构成排除理由。
4. 将采纳的规则写入技巧数据，生成可读视图，检查查询结果和跨模块引用。

2026-09-10 的统一归并审读涉及 6,230 条原候选、38 条分析字段补充及 8 条历史复盘补充，共 6,276 个输入。6,214 个采用成员进入 68 个通用技巧、145 个条件细分，62 条原候选被排除。全部输入都有一次明确处置。机器可读统计见[consolidation-summary.json](consolidation-summary.json)。

该轮使用 API 初审、原生模型归并与主代理复核，属于模型审读。API 第二轮复核中的截断响应没有按完整批次计入成功。不同轮次的模型与执行记录分别保留，不把一次工具配置写成全部蒸馏工作的实际执行者。

运行时的通用技巧源是 `exposition-cards.json`，条件规则及成员来源在 `technique-variants.json`。查询器按字面匹配返回少量相关规则，使用时保留 `rule`、`conditions`、`misuse`。来源定位方便维护者追溯，但本发行目录不包含原始论文和所有开发分析文件。

源码定位：`experiments/writing-corpus-20260909/full-distillation/api_distill.py`、`experiments/writing-corpus-20260909/skill-unification-002/`；随发行版提供的查询器见[query_variants.py](../skills/lab-ultra-writing/scripts/query_variants.py)。

## 覆盖和验证分别怎么算

| 记录 | 已有结果 | 不由该记录证明的事情 |
| --- | --- | --- |
| 64 篇获奖稿的早期专项审读 | 正文与参考文献 OCR 连续审读记录；253 个“论文×页”图像复核位置 | 全部附录代码逐行正确、全文科学结论可靠 |
| 1,585 份转换文本 API 批次 | 3,875 个任务完成；1,473 份全文二次机器复核，112 份完整分块后局部二次复核 | 整个原始资料库都已读完、原始页面全部核查 |
| 统一归并 | 全部 6,230 条原候选有去向，另吸收 46 条补充 | 所有源论文模型正确、规则在所有题目上有效 |
| 发行版回归 | 记录为包内及安装后分别 128 项通过 | 专家评审通过、获奖或真实工程验证 |
| 三个固定证据改稿案例 | 检查搜索、子样本指标、类比的结论边界 | 新旧版本整篇论文质量的统计优劣 |
| 本 README 的论文案例 | 作者提供的 285 页 PDF 和三个页面预览 | 一次调用的独立性能基准 |

64 篇专项审读、752 个期刊身份和 1,585 份转换文本使用不同口径，不能相加后称为独立论文总量。早期固定证据小试也存在平局、没有增益证据的记录；这些结果不支持“蒸馏后必然变好”的保证。

## 复核依据

这次 README 编写核对了发行版文件、查询输出、下列开发记录及作者提供的案例 PDF。开发路径从原仓库根目录起算：

| 开发记录 | 这次用于核对的内容 |
| --- | --- |
| `docs/architecture.md` | 三类空间、解析与语义边界、离线与运行时分工 |
| `experiments/cumcm-suite-2026-09-05/audits/award-full-distillation-v2-20260906.md` | 64 篇专项审读、共同布局、反例与验证范围 |
| `experiments/writing-corpus-20260909/full-distillation/README.md` | 1,585 份转换文本批次及原库未完成范围 |
| `experiments/writing-corpus-20260909/skill-unification-002/README.md` | 统一归并方法、计数和历史验证 |
| `experiments/writing-corpus-20260909/skill-unification-002/consolidation-summary.json` | 6,230 条候选、补充记录、68 卡和 145 细分 |
| `experiments/cumcm-suite-2026-09-05/INSTALL-LAB-ULTRA.md` | 完整安装范围和发行版验证记录 |

正文链接可直接打开本分发目录中的规则与策略。发行版原有 [manifest](../manifest.json) 继续只覆盖 Skill 资源；新增 README、案例与预览的记录位于 [README 核验记录](readme-verification.json)。
