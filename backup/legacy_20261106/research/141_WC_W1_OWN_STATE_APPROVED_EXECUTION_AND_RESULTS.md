# W1 自身轨迹诊断完整结果：局部改善仍不能替代终点收益

2026-10-06，三场景完整结束并独立验收。**两个终点退化场景，在 W1 自身状态上的平均去噪预测误差仍改善。** 这使研究重点从“局部改善是否只存在于官方轨迹”进一步转向实际 CFG 更新、误差传播和计算位置；尚不能唯一归因于其中任何一项。

## 1. 完整观测与发现

`WC-W1-OWN-STATE-SHADOW-R1-20261006-A` 仅执行一次。misc、AV51、AV28/seed0，原 scalar 参数与固定 mask，calls45/46、67/68（第23、34次更新的两个CFG分支），三完整视频、12真实同状态teacher观测全部完成。teacher只评分，无写回。每场景新增视频与旧W1 OFF的72调用输出、trace、cache/校准、pipeline/decoder、MP4字节和完整93帧RGB身份桥通过，故可以复用已完成的终点LPIPS，无需重复评分。

下表百分比均为相对官方近似的误差降低，正号表示改善；局部只归约本卡每场景四个观测。终点是**同一视频已存在的分数**，不是本批新增质量收益。

| 场景 | 自身状态预测MSE降低 | 自身状态postwarp残差MSE降低 | 已有终点LPIPS降低 |
|---|---:|---:|---:|
| misc | +5.69% | +21.78% | -19.09% |
| AV51 | +49.06% | +48.37% | -16.11% |
| AV28 | +9.83% | +1.82% | +24.46% |

[冻结入口的signed汇总](../reports/wc_w1_own_state_signed_summary_cpu_r1_20261006.json)保存所有绝对MSE、比例和逐点有符号差值。[独立原件与终点连接审计](../reports/wc_w1_own_state_final_original_native_audit_20261006.json)重新计算均值，核对旧/新视频SHA并连接原分数。三场景均有局部平均预测正信号，但两个终点负例并没有被这些局部改善挽救。因此，不能把“局部误差降低”直接升级为端到端保真收益或训练刷新Head的标签。

## 2. 分阶段与旧调用对齐

[CPU描述性重分析](../reports/wc_w1_own_state_call_alignment_exploratory_20261006.json)保留两对调用而不只报平均：

| 场景 | 45/46预测MSE降低 | 67/68预测MSE降低 | 67/68残差MSE降低 |
|---|---:|---:|---:|
| misc | +1.00% | +12.30% | −78.37% |
| AV51 | +53.94% | +44.55% | −71.16% |
| AV28 | −16.24% | +15.54% | −41.21% |

晚位置三场景残差都恶化，预测却改善；AV28早位置预测恶化而终点改善。特征误差、最终网络预测误差和视频终点是不同对象，不用单个位置的正负作整个方向的否定线。当前观测是两次去噪更新，不能当作93帧视频内的两个时间区间。

旧官方状态诊断的观测位置并不全部匹配：misc为15/16、27/28、49/50、69/70，与本卡没有交集；AV51只匹配45/46；AV28匹配四个位置。AV51在匹配45/46位置，旧状态预测MSE降低44.12%，自身状态降低53.94%；AV28四个匹配位置旧状态降低32.59%，自身状态降低9.83%。这些是不同状态和历史上的描述性比较，不是单变量状态干预或迁移效果分解。misc的旧匹配误差明确为缺失。

还未测量真实CFG组合误差：本卡保存各分支误差，未保存两个误差向量的交叉内积。各分支MSE平均无法推导guidance组合后的MSE；不用缺失交叉项编造联合误差或传播收益。

## 3. 执行、成本和原件

实际GPU源固定为 `aa379cb14e087fbbf61e45fc45d3619e1e8dfc7b`。selected182文件实际CPU门通过；原R3生产CPU181文件/sourcef68bac4与通过原件保持。GPU唯一次运行exit0，**实际全wall 880.062774秒 = 0.244461882 GPUh**，低于1800总/1770child边界。1800预付已按实际结算，累计 **13.748764674/24 GPUh**、49jobs，无inflight，剩余 **10.251235326 GPUh**。

三原GPU句柄2975499/2975518/2975520全部退出，目标A6000释放为24MiB、无compute apps，f1共享锁自由。独立终态CPU运行3.781024秒，exit0，CUDA未初始化、预算不变；原CPU句柄2978874/2978875退出。独立read-only审计381项native SHA、通过CPU原件、费用、五句柄、日志、完整视频和signed均值通过。没有自动重提、重启、另一GPU、新训练或人工评价。

小回执：[GPU supervisor](../reports/wc_w1_own_state_supervisor_20261006.json)、[GPU runner](../reports/wc_w1_own_state_runner_20261006.json)、[CPU终态与汇总](../reports/wc_w1_own_state_terminal_and_summary_cpu_r1_20261006.json)。CPU原件SHA `7268c3b43465a231ff50d2b3dfb997cfa52f339e4cd36b60b40b5dc156d94f0e`；当前账本SHA `482b28890839937c6eeae76d9a508882ff1f05aa287cae3ee4c7eadf9233aa4b`。实际GPUsource不因后续报告提交改变。

## 4. 结论与下一步

**继续WorldCache。** 本卡有效区分了一个关键解释：在这四个注册观测点，两个终点负例的局部预测优势仍存在于候选自身状态上。没有证明所有步骤都改善，也没有否定整个校准或缓存方向。W1七接受场景4改善/3退化、均值LPIPS仅降低0.4388%、旧MUSIQ/VQA混合结果、原8/7/1分母保持。

下一执行优先级仍是原W3-B固定各CFG完整调用配额的四交换，对照W3-A允许后续自适应的总效果；本次“允许”没有自动批准B，原单独范围问题不重复。W1暂不扩大分组/网络/训练/新确认；下一变体由B与本卡证据共同选择，先按[新v4.2计划](../plans/WORLD_CACHE_POST_OWN_STATE_WINDOW_20261006.md)完成目标与标签对齐，再冻结具体成本卡。现有观测来自三个已曝光CAL场景、一个seed，不是独立CONF；12观测和93帧都不是额外独立视频。带shadow/hash的本批时间只能作成本，不能作干净速度结论。

---

以下保留本卡批准、准入和启动时的历史快照，不能作为当前运行状态：

# W1 自身轨迹三场景诊断：直接批准与唯一执行

2026-10-06；当前为批准绑定和提交准备，尚未声称真实teacher观测或收益。

## 已批准的范围

用户直接回复“允许”，[来源绑定](../manifests/wc_w1_own_state_human_scope_source_20261006.json)关联当前turn `01a1110c-010f-75c3-816f-f4d5f71834d2` 与原独立范围问题。[批准原件](../manifests/wc_w1_own_state_gpu_authorization_20261006.json)只批准 `WC-W1-OWN-STATE-SHADOW-R1-20261006-A`：misc、AV51、AV28/seed0，原mask/scalar与calls45/46/67/68，三完整shadow ON视频、12同状态teacher观测；teacher只评分，不写部署。最大1800总/1770child/kill5，最大0.5GPUh计入原累计24h，旧费用不重置。

这是最近提报的[具体卡](../plans/WORLD_CACHE_OWN_STATE_DIAGNOSTIC_CARD_20261006.md)的范围答复；此前旧blocked解除，goal恢复active。W3-B9600完整卡没有因此自动批准，不重复其旧问题。CPU通过、全局预算余额和自动goal接续不再作为此卡批准的替代理由；本卡已获得直接批准。

## 冻结来源与必要准入

[通过生产CPU的R3](../research/140_WC_W1_OWN_STATE_PRODUCTION_CARD_AND_CPU.md)七步exit0/14.969秒、181payload/sourcef68bac4和720原件审计保留，核心13文件不改、不重跑。新[selected配置](../configs/wc_w1_own_state_approved_selected_20261006.json)仅增加UUID、直接批准及原CPU原件绑定；[新独立stage清单](../manifests/wc_w1_own_state_execution_20261006.json)共182文件，生产源与原CPU字节一致。

服务器原项目 `/home/gaokuangda/data/gkd/worldcache_omr`，新stage `.sync/wc-w1-own-state-gpu-r1-20261006`，唯一run `outputs/wc-w1-own-state-shadow-r1`。预备资源回读：原R3 receipt SHA匹配、181文件保持；根账本13.504302792/24h、48jobs无inflight；新run不存在。目标A6000 UUID `GPU-cebf7119-cf03-23b9-e192-cd196332b704` 初读24MiB/no compute process，数据盘557877370880空闲字节，另一GPU不用于本卡。这是预备状态，非最终GPU准入或实际运行。

下一selected-only CPU来源/原件/资产门，然后supervisor final fresh UUID/VRAM/compute process、f1共享锁、数据盘和整卡预算准入；排他submission marker、原supervisor/timeout/runner句柄和日志。未知transport结局只能查原stage/handle，不重提。1800秒统一预付，真实全wall按实费结算，失败、导入/加载、hash/teacher/解码/flush和释放均计费。

## 结果与验收边界

本卡必须通过每场景旧W1 OFF的全部72输出、cache/校准、trace、pipeline/decoder/video/93RGB身份桥，才能将对应同状态teacher观测解释为有效诊断并复用旧终点LPIPS。保留负值/零值/缺失；不要求三个场景全改善。CPU MockWriter和小网络不是实际视频、真实28层teacher或新质量结果。

实际GPU终态后先费用/三原句柄/f1锁/释放/源审计，再全93帧原件身份核对和三场景signed局部汇总。当前旧W1七场景4改善/3退化和平均LPIPS0.4388%保持；本轮真实视频、teacher、速度/质量结果尚未产生。后续结果将按原件补充本报告。

## 唯一启动现场

selected实际CPU门exit0/12.459729秒；source `aa379cb14e087fbbf61e45fc45d3619e1e8dfc7b`，生产182文件与R3原CPU绑定通过。[启动回读](../reports/wc_w1_own_state_start_observation_20261006.json)确认supervisor2975499、timeout2975518、runner2975520三原句柄存活，runner正在INITIALIZING。child截止北京时间 `2026-10-06T20:22:17.898257+08:00`；1800总/1770child/kill5保持，不能从观察超时重提。GPU上下文尚未初始化时不把PID存活称为已产生teacher或科学结果。

已单次预付1800秒，累计暂记14.004302792/24GPUh、第49job、`wc_w1_own_state_inflight`；旧13.504302792/48jobs保持，实际结算尚待。只观察原stage/原run；没有重跑fixture、扩大新scope或使用另一GPU。
