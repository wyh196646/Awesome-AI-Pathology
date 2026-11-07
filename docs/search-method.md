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
| 官方出版社、会议与作者代码库 | 核实正式题名、录用/出版状态、研究输入和代码；社交媒体仅提供线索 |

arXiv 接口限流时，可以使用官方检索网页补查，并记录查询条件、每页数量和公布总数。
这属于独立的回退检索，不能把接口失败改记为成功，也不能把网页某一关键词的结果声称为全站覆盖。
按首次公告日期检索的网页结果，不能替代对旧论文近期修订的检索。

周更以**前一 UTC 日**为截止日，从各平台成功检查点向前重叠 **14 天**；首次滚动窗口从
2026-09-21 开始。历史补查按 2023、2024、2025、2026 年分别进行。实际执行过的查询与
仅配置、尚未执行完的关键词必须区分，失败和待审记录不得记作零结果。

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
4. **状态与年份**：未正式发表者放入 arXiv、bioRxiv 或 medRxiv 栏目，明确标作 preprint。
   投稿和作者自行声称录用不能替代官方录用/出版证据。新预印本按首次公开年份归档，修订日期和
   DOI 字符串里的年份不能替代首次发布日期。正式版本按核实的会议或期刊出版年归档。
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
