# 扩展预印本平台与 Fuji 补录

检索截止到 **2026-11-07 UTC**，历史补查按 2023、2024、2025、2026 年分别执行。
本轮新增 **40 篇**，合并 **8 个跨平台身份链接**，总计 **4,932 条**。
发表迁移和删除均为 0。主页保留介绍和索引，维护记录集中在本目录。

## 漏收原因与修复

Fuji 的题名能够通过原有 258 个主题词筛选。漏收涉及原先固定的三个平台及历史时间范围。
论文于 2026-08-06 首次发布在 Research Square，早于原滚动检索起点 2026-09-21。
本次核实原始页面、Crossref、PubMed 和 PMC 后，放入 2026 年 Research Square 栏目。
原始页面的投稿期刊信息不构成正式出版证据，本次标注为预印本。
[Research Square](https://www.researchsquare.com/article/rs-9949149/v1)

## 实际结果

| 年份 | 新增 |
| --- | --- |
| 2023 | 2 |
| 2024 | 2 |
| 2025 | 7 |
| 2026 | 29 |

| 原始平台 | 新增 |
| --- | --- |
| Research Square | 28 |
| Preprints.org | 4 |
| SSRN | 3 |
| Authorea | 3 |
| ScienceOpen Preprints | 1 |
| SciELO Preprints | 1 |

补充的工作包括 Fuji、PathVista、CellPlexer、PATH-SparseD、CervixFM、MicroSC、spaGFM，
以及 GigaTIME 的独立外部验证。OmiCLIP、spEMO、PanoSpace、SPACEL、scCobra、PathBench、
BRIGHT 和 Histo-VL 已有条目，本轮合并其 Research Square 或 SSRN 身份链接。
标题和有无正面结果均不作为单独的质量或准入门槛。

## 网站、关键词和准入

保留 arXiv、bioRxiv、medRxiv 原有检索，并加入 Europe PMC 的其他预印本索引。
本轮执行四个年度区间、每年 10 组标题/摘要查询及完整分页，共返回 33,372 个不同
索引记录。版本规范化后有 24,939 个宽召回关键词候选，这些数量均不等于相关论文数。
对 Research Square、SSRN、Preprints.org、Authorea、TechRxiv、OSF、ScienceOpen 和 SciELO
执行官方域名补查。PubMed、PMC、Crossref 与原始平台用于核实身份和发表状态。
索引和网站搜索存在覆盖差异，本轮确认部分 SSRN 病理基础模型论文未被 Europe PMC 检出。
逐年网页搜索中的年份词只是线索，论文年份依照原始发布日期核实。

关键词仍覆盖 histopathology、histology、cytology、WSI、whole slide、H&E、pathomics、
virtual staining、pathology report、foundation model、spatial transcriptomics/proteomics、
single-cell、scRNA/scATAC、cell annotation、cell-cell interaction、tissue microenvironment、
multimodal omics，以及 Visium、Xenium、CosMx、CAMELYON、PanNuke 等平台和数据集别名。
方法词用于候选排序，不要求所有论文题名包含 pathology 或同时出现某个方法词。
[完整词表](../../config/literature-keywords.json)

主题按计算组织/细胞图像、空间与单细胞组学、微环境和癌症多模态组学判断。要求计算方法、
可复用资源、基准、实质性组织或细胞分析，或直接相关综述。空间与单细胞方法无需病理图像。
正式期刊仍要求已核实的 SCIE 和中科院 2025 升级版大类 1 区。预印本标注其真实平台，
核实首次年份和版本。已正式发表于不合格或尚未核实刊物者不通过预印本重新纳入。
本轮 18 个候选记录因此未加入，其中包含重复指向同一正式论文的记录。
白名单外的排除不代表已经证明该刊低于 1 区，资格未完成核实的刊物也按现有规则暂缓。
[准入与标注说明](../search-method.md)

## 审阅进度与后续

本轮保存 82 条审阅备注，对其中 74 条执行出版身份核查。审阅依据为题名、
可用摘要及相关段落，并对拟纳入条目核实原始页面或注册元数据，未将全部候选称为全文精读。
尚有 24,878 个索引候选需要逐条或身份复核，公开分片保存稳定索引 ID，可通过 Europe PMC
重新获取元数据。完整摘要和原始响应保留于本地缓存，未将大量摘要复制进仓库。
站点搜索的新增线索和缺摘要 SSRN 记录另保留于查询与决定清单。

SSRN 直接页面批量访问出现 HTTP 403，已使用其官方域名检索结果和 Crossref 核实本轮收录项。
Research Square 临时连接失败已重试恢复。四年 Europe PMC 分页检索完成，逐条审阅仍未完成，
扩展来源成功检查点保持空值。原三平台本轮未重跑，其 2026-11-01 检查点和原待审队列保留。
现有每周任务已加入扩展来源、官方域名补查及 Fuji、SSRN BRIGHT 覆盖检查，继续优先恢复待办。
本轮作为完成核实部分的增量发布，不表示全平台所有相关论文均已补齐。

PR 评审后的修复覆盖空摘要、正式版本关联身份、年度输出保留、独立检索游标和缓存刷新。
本轮 40 篇新条目均无未处理的索引正式版本关联，条目数量未受这些检索修复影响。
完整且候选已持久保存的检索进度用于下次增量查询，审阅成功检查点保持独立。
本地校验包括期刊门槛、索引刷新、34 项测试和原有条目及辅助链接保留检查。
[机器审计](2026-11-08-platforms.json) · [实际查询](2026-11-08-platforms-queries.json) · [逐条决定](2026-11-08-platforms-decisions.json)
