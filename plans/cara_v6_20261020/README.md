# CARA 下一轮实验：v5评审闭环，2026-10-20

入口供实验与写论文的对话共同读取。原评审包逐字归档在[reviews/cara_v5_20261019](../reviews/cara_v5_20261019/README.md)，新方案编号v6仅为实验设计版本；不表示论文或算法结果已升级完成。

**中心问题：连续修正与共享刷新位置，在直接修正近邻、强前密规则和调优缓存基线面前，能否形成可复现的终点保真—真实时间优势。** 当前最强新证据来自四CAL：固定25D的A3比纯C失真低26.63%；固定26D的纯C共享计划比前密C低15.36%。两条尚未联合，也没有独立TEST或新配置的clean测速。

| 顺序 | 工作 | 当前实态与完成标准 |
|---|---|---|
| 0 | 原BANK24继续 | scope、gate、CPU证明、资源自动化不改；其D21/A21银行不验证A3或新布局 |
| 1 | R0方法/数据/身份 | 本目录与本地区间编译器已整理；真实新入口、B1/B2秒数和TEST身份仍待 |
| 2 | R1有限开发＋R2-A等次数消融 | 首轮合并32路径草案：12个新候选正式＋8个Single22/23正式＋12完整预热/桥接；不重复已有A3/G01/纯C端点 |
| 3 | R2-N直接近邻＋R3开发前沿 | 先审RFC；同D/同覆盖读出适配与原方法分开命名；近邻8正式上限；R3逻辑48格先去重再报价 |
| 4 | 冻结最终版本后R4-A | 12全新prompt×双seed×7角色＝168正式；含warm/load/post/评分的整卡价格与实际CPU未完成 |
| 5 | 条件R4-B/R5 | 6提示词B2子集在R4-A结果前固定，最多72新增；另窗口16、第二骨干/设置48均为条件待项 |
| 6 | R6/R7 | 最终方法自己的30正式＋建议10预热重复测速、新TEST视频质量评价、校准费用与正文收束 |

[执行设计与缺口](PRIORITIZED_EXECUTION_PLAN.md) · [方法规格](METHOD_SPEC_V6.md) · [Algorithm 1](ALGORITHM_1.md) · [数据协议](DATA_PROTOCOL_V6.md) · [证据复用](REV_EVIDENCE_REUSE_MAP.md) · [问题闭环](REVIEW_ISSUE_CLOSURE_MATRIX.md) · [近邻适配审计](NEIGHBOR_ADAPTATION_NOTE.md)

机器入口：[TASK_REGISTRY_V6.yaml](TASK_REGISTRY_V6.yaml)、[paper_variant_map.yaml](paper_variant_map.yaml)、[首张32路径草案及完整工程估价](FIRST_DEV_UNION32_DRAFT.json)、[开发候选与原端点联合清单](DEVELOPMENT_UNION_V6.json)、[TEST保留协议](TEST_V6_RESERVATION_PROTOCOL.json)。YAML文件采用兼容YAML1.2的JSON表示。

本轮只有本地设计/结构CPU控制，无SSH、服务器新CPU、GPU或新质量结果。32路径工程预估与拟议cap见机器草案，实际新生产入口/完整CPU通过前不可派发。cap226与严格单卡<12GPUh自主规则保持；≥12或余额不足，待具体整卡可审阅后再询问，不拆卡规避。新长卡仍一次半程技术检查＋预计结束后一次验收。
