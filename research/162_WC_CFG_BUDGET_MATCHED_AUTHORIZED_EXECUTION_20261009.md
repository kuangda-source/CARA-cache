# 2026-10-09 同配额CFG位置交换：获批、文档先行与实际执行

**组会飞书报告已创建且完整回读；原完整同配额卡已实际启动并进入生成。当前没有本轮终点质量结果。** 本批区分原自适应CFG0的0.5152%保真改善，在各CFG完整计算18/17固定之后是否保留。该问题有明确价值，不据一次结果否定整个刷新调度方向。

## 已完成：用户要求的组会报告

通过Feishu CLI创建：[WorldCache组会汇报](https://lcnssrlun9lz.feishu.cn/docx/HTSIdK0uLofCG5xUI1IcTKaCnAh)。报告覆盖F1、W1/W2诊断、稀疏R4/H0/H1/位置/寿命/在线/公平基线、W3-A/B、新seed与CFG四组合：目标、方法、设计、全部阶段正负结果、限制及下一步。当前库只保留WorldCache，独立OMR/DRE不纳入本线。

原科学数据截至10月8日，明确W1七接受场景4正3负/均值LPIPS降0.439%，W3有位置和未来算量反馈正例但仍有no-op及负例；未声称稳定新方法端到端优势。报告正文、12章节/12表/3公式/21来源链接和本地XML完整一致，create/fetch无警告，修订4；[正文存档](161_WC_GROUP_MEETING_REPORT_20261009.md)、[完整回读回执](../reports/wc_group_meeting_feishu_verification_20261009.json)。文档核验实际在GPU提交之前，已独立确认顺序。

## 本轮授权与设计不变

用户直接“允许，但是先总结一下当前所有实验，形成一个组会汇报的飞书文档，用飞书 cli，讲清楚目标、方法、实验设计和当前已有的结果、下一步怎么推进，然后继续实验”，批准此前可审阅的完整2.082740046511187 GPUh单次>2h例外。[精确绑定权威](../manifests/wc_w3_cfg_budget_single_job_authorization_20261009.json)保留未来单次>2h仍直接确认的规则，累计50h与旧收费历史不改。

| 项目 | 冻结范围 |
| --- | --- |
| 卡/运行 | WC-W3-CFG-BUDGET-MATCHED-R1-20261008-A / wc-w3-cfg-budget-matched-r1 |
| 请求 | Human seed2；768×432/93帧/16fps；UniPC/Karras实际36更新72调用 |
| 完整规模 | 1新WC父、10完整后缀、6新视频、1旧Native、4主比较/1交互；全部五组严格重复 |
| 同配额 | 各细胞CFG0/CFG1均18/17，总35；只移动45/47和46/48位置，其他掩码/70reset/71–72尾保留 |
| 科学对象 | 同当前状态、固定每CFG配额的位置价值；单曝光CAL，不是独立CONF、物理/语义终审或清洁部署测速 |

[原CPU/完整预测](160_WC_CFG_BUDGET_MATCHED_CORE_AND_PRODUCTION_CPU.md)与所有控制保持。生产源4ff96ed的301份载荷不变，最终提交元数据源8457dfbb09bc7ff4890c0878bf846189f433cf47。

## 同源CPU与fresh资源实际确认

selected实际CPU16.380050762秒，PID3368608已退出；CPU无CUDA/GPU0。独立从原生产回执、selected原字节、源/配置、实际301文件哈希、累计50权威与新增单次权威重建通过，静态绑定7f5247cd保持。完整旧Native与模型/资源验证不变。见[selected独立验收](../reports/wc_w3_cfg_budget_selected_pre_gpu_independent_audit_20261009.json)。

外层启动器最初错误使用服务器默认python3，重复生产验证报torch缺失，发生在GPU子进程/输出与预算更新之前：新增GPU0，冻结生产载荷无变化。原错误记录保留于[CPU环境拒绝](../reports/wc_w3_cfg_budget_pre_gpu_launcher_cpu_environment_refusal_20261009.json)，外层已改用现有Cosmos生产venv；原卡未消耗后单次实际启动。不把该环境错误当方法负结果。

fresh准入核对原共享锁可用、目标A6000 GPU-cebf7119-cf03-23b9-e192-cd196332b704为sm8.6/24MiB/noapps、磁盘>12GiB、原账本23.7023661169283/50h、60jobs/noinflight；forecast在余26.297633883h内。

## 实际句柄与当前阶段

| 原句柄 | PID | 当前作用 |
| --- | --- | --- |
| GPU supervisor | 3368923 | 固定原源/锁/UUID/费用；单次完整卡 |
| GPU runner | 3368938 | 原301生产载荷的完整父与十后缀 |
| GPU释放后CPU driver | 3369011 | 等原GPU正常退出、原PID消失，再全93评分；没有新GPU |

[GPU原启动](../reports/wc_w3_cfg_budget_gpu_r1_launch_20261009.json)、[CPU后处理启动](../reports/wc_w3_cfg_budget_post_cpu_r1_launch_20261009.json)、[原始句柄](../reports/wc_w3_cfg_budget_live_handles_r1_20261009.json)及[独立范围/账本/句柄审计](../reports/wc_w3_cfg_budget_initial_scope_and_handles_independent_audit_20261009.json)均保存。最新[生成入口观察](../reports/wc_w3_cfg_budget_generation_started_r1_20261009.json)：三原PID均活、load101.860秒、提示词检查通过并进入生成，GPU进程确为3368938约24GiB；完整父/后缀尚未完成，0已评分。

服务器第61job在途将remaining全部预留，账本used=50是占用保护，不是已花完；真实底数23.702366117h保持，最终按原supervisor实费结算。原budget字节与授权历史已独立核对，所有旧失败费用保留。本卡只跟踪上述三个原句柄，禁止因观察/SSH短暂失败重投或修改在跑源。

## 结束后怎样推进

GPU正常终态释放后，已绑定driver自动跑原全93帧评分代码：四细胞loss、四有符号比较、一交互；验证两个CFG实际配额和全部重复。随后捕获原始终态/视频SHA/收费/资源释放，独立重算完整状态、动作和93帧指标，再形成科学报告。

若正信号保留，先预登记有限新seed/场景确认；若反向，优先利用本批原记录区分位置、后续路由和增算，不靠单项阈值判方向失败。不扩大训练Head、LoRA、稀疏搜索、OMR或非必要人工评审。重大方向共同讨论，累计50h/未来单次>2h确认规则保持。goal实际active，当前总体科学目标未完成。

## 部分执行进展：原首控制已结束，完整结论仍待

[首OFF对照观察](../reports/wc_w3_cfg_budget_off1_partial_video_progress_20261009.json)确认OFF1完整后缀15次full并保存接受视频，OFF2第二重复在跑。只完成1/10后缀、1/6新视频，父余段/全部重复与评分未结束；该技术进展不算新方法保真或速度结果。三个原PID仍活，无重投/改源；本轮为verified wait，继续原完整scope。
