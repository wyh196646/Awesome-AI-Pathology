# 文献检索、准入与标注方法

这份说明描述实际维护规则。检索命中不等于收录，接口执行成功也不等于文献已经找全。
每次更新的区间、实际查询、来源状态和逐条决定保存在 `docs/updates/`，主页仅保留介绍与索引。

## 检索网站与用途

| 来源 | 实际用途 |
| --- | --- |
| [arXiv](https://arxiv.org/) | 标题和摘要检索；官方摘要页核实题名、首次提交、版本、DOI 和撤回状态 |
| [arXiv Atom API](https://info.arxiv.org/help/api/user-manual.html) | 按最后更新时间检索修订；分批查询并检查分页；失败必须单独报告 |
| [bioRxiv / medRxiv API](https://api.biorxiv.org/) | 分页拉取指定日期内各分类的完整元数据，再筛标题和摘要；逐年补查 Pathology 分类；按 DOI 核实版本历史 |
| [Crossref](https://www.crossref.org/) | 核对 DOI、作者、正式发表关系、出版社、卷期和年份；辅助发现改题名的正式版本 |
| [PubMed](https://pubmed.ncbi.nlm.nih.gov/) | 补充生物医学摘要和出版身份；不能单独证明中科院分区 |
| [Europe PMC](https://europepmc.org/) | 按年检索其他平台已索引预印本的标题与摘要，保留分页、版本及正式版本线索 |
| Research Square、SSRN、Preprints.org、Authorea、TechRxiv、OSF、ScienceOpen、SciELO Preprints | 官方站点补查与原始论文状态核实，和索引检索并行执行 |
| 官方出版社、会议与作者代码库 | 核实正式题名、录用/出版状态、研究输入和代码；社交媒体仅提供线索 |

arXiv 接口限流时，可以使用官方检索网页补查，并记录查询条件、每页数量和公布总数。
这属于独立的回退检索，不能把接口失败改记为成功，也不能把网页某一关键词的结果声称为全站覆盖。
按首次公告日期检索的网页结果，不能替代对旧论文近期修订的检索。

周更以**前一 UTC 日**为截止日，从各平台成功检查点向前重叠 **14 天**；首次滚动窗口从
2026-09-21 开始。历史补查按 2023、2024、2025、2026 年分别进行。实际执行过的查询与
仅配置、尚未执行完的关键词必须区分，失败和待审记录不得记作零结果。

扩展平台从 2023-01-01 开始独立补查，不受原三平台 2026-09-21 首次滚动窗口限制。
Europe PMC 历史补查使用 `FIRST_PDATE`，周更使用 `UPDATE_DATE`，逐页核对结果总数。
索引未覆盖的 SSRN 等论文通过官方域名搜索补查，逐年结合关键词查询。域名搜索里的年份
只是检索线索，实际归档仍核实首次发布日期。PubMed 和 PMC 也用于追溯原始平台及正式版本。
Zenodo、OSF 的数据集、项目主页和代码存档须先区分文献类型，不能直接当作论文收录。

扩展来源的“已检索至”与“已审阅并发布至”分开记录。完整检索且候选已持久保存后，前者
可用于下一次增量查询并重叠 14 天，历史待审队列继续保留。审阅未完成时后者不推进。
默认按每次执行分别保存候选和缓存，指定旧缓存恢复时可用 `--refresh-cache` 重新联网补查。
索引关联的正式 DOI 参与排除和去重，只有 PMID 的关联先保留原始核实链接，再确认正式版本。

## 关键词如何组织

完整可执行词表见 [literature-keywords.json](../config/literature-keywords.json)。
除标题外必须检索摘要；泛方法论文可能只在实验说明里提及病理数据。

| 词族 | 代表性词语 |
| --- | --- |
| 病理与组织/细胞图像 | pathology, pathologist*, histopath*, histology, cytology, WSI, whole slide, H&E, virtual staining, nuclei, glands, mitosis, blood smear, bone marrow |
| 阅片和诊断流程 | diagnostic/pathology copilot, pathology agent, slide navigation, slide review, gaze, eye tracking, visual grounding, pathology report |
| 空间组学 | spatial transcriptomics/proteomics/multiomics, spatial gene expression, spatial domains, deconvolution, cell neighborhoods, deep visual proteomics, spatial glycomics |
| 单细胞与跨模态 | single-cell, single-nucleus, scRNA-seq, snRNA-seq, scATAC-seq, snATAC-seq, multiome, cell annotation, Perturb-seq, Cell Painting, morphological profiling |
| 微环境和癌症多模态 | tumor/tumour microenvironment, cell-cell communication, ligand-receptor, tissue niche, radiogenomics, pathology-genomics, missing modality, multimodal survival |
| 平台与数据集别名 | Visium, Xenium, CosMx, MERFISH, Stereo-seq, CODEX, IMC, CAMELYON, PanNuke, MoNuSeg, MoNuSAC, CoNSeP, BRACS, NCT-CRC-HE, JUMP-CP |

machine learning、foundation model、MIL、graph、diffusion、integration 等方法词用于排序和
发现相关方法，**不作为必须同时出现的过滤条件**。裸词 pathology 必须保留，即使它会带来
放射影像、言语治疗和数学“病态”等误命中；这些误命中由研究输入和贡献来排除。

## 准入标准

1. **主题**：计算病理、组织/细胞显微图像、病理阅片与报告工作流；空间转录组、蛋白组和
   多组学；单细胞/单核分子组学、跨模态注释；组织微环境、细胞互作和癌症多模态组学。
   空间与单细胞方法不要求输入病理图像。
2. **贡献**：计算方法、可复用软件或数据资源、基准、实质性的空间/单细胞组织或疾病分析，
   以及直接相关综述。仅出现“pathology”或“single cell”不够；常规大宗样本标志物相关分析、
   单纯湿实验、纯放射影像、纯药物/序列预测、无关植物/微生物研究、社论和评论不收录。
   临床相关的细胞显微诊断方法可按细胞图像标准判断。
3. **期刊**：所有年份的正式期刊文章都必须同时满足 **SCIE 收录**与**中科院 2025 升级版
   大类 1 区**，以 [journal-policy.json](../config/journal-policy.json) 中已核实白名单及证据为准。
   JCR Q1、小类 1 区、Top 标签不替代该条件。未核实刊物先不收录；不合格正式版本不得换成
   预印本重新纳入。独立核实的会议版本单独按会议规则判断。
4. **状态与年份**：未正式发表者放入其原始预印本平台栏目，明确标作 preprint。
   投稿和作者自行声称录用不能替代官方录用/出版证据。新预印本按首次公开年份归档，修订日期和
   DOI 字符串里的年份不能替代首次发布日期。正式版本按核实的会议或期刊出版年归档。
   Research Square 页面中的投稿期刊字段不证明录用。核查原始页面的正式 DOI、版本日期及
   撤回状态。已标录用但正式身份未核实时保留待办，不自行指定期刊和年份。
5. **身份**：联合核对 DOI、arXiv ID、题名变体、作者、版本史及正式出版链接。改题名、修订、
   跨平台发布不能重复计数；正式发表后保留代码、数据、项目网站与预印本身份链接。

预印本不适用 SCI 分区门槛；收录也不代表已通过同行评审、结果已独立复现，或获得质量背书。
引用量、作者名气和标题是否醒目不作为收录的必要条件。

## 发布与覆盖边界

流程为：宽召回 → 身份与主题初筛 → 逐条核实研究贡献 → 出版/年份/期刊门槛检查 →
去重与合并链接 → 更新逐年列表和索引 → 本地校验 → 分支 PR → 检查与评审通过后合并。
审计必须区分自动摘要初筛、逐条摘要/相关段落审阅、全文核实和元数据核实，不能混称为全文精读。

未审候选和未完成的出版核实必须保留为待办，不能为了清空列表而排除，也不能视为已完成来源。
检索词、平台分类、摘要缺失、索引延迟、接口故障及改题名都会影响召回。因此本库承诺保留
可核查的来源与决定、修复已知漏项，**不承诺已经穷尽所有相关论文**。

Fuji 和 SSRN BRIGHT 是新增的平台覆盖检查样例。Fuji 题名可被现有词表命中，漏收原因是
原先固定三平台和历史时间范围不足，因此本轮扩展检索来源，保留已有 258 个主题词。
固定样例用于发现流程缺口，完整词表检索仍需逐条审阅。每个扩展来源维护独立状态，审阅
未完成时不推进成功检查点，原三平台的更新进度也须单独报告。
