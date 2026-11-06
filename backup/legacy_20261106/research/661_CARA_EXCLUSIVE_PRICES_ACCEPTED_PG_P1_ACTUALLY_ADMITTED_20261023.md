# 独占价格完整接受，PG-P1已在GPU3实际准入

价格可信度补测已完成，PG-P1已于2026-10-23 **20:26:04.693013 Asia/Shanghai**单次启动。原GPU3硬件独占和唯一runner核验通过；初始技术状态为MODEL_LOADING、0失败。自动策略是否优于简单规则，仍待本卡及后续独立闭环比较。

## 价格终态接受与费用

[原完整终态](../reports/wc_policy_price_refresh_GPU_terminal_20261023_2020.json)实际20:20:45开始收件；[独立接受](../reports/wc_policy_price_refresh_GPU_accepted_20261023_2023.json)核对10/10完整路径、1624正式格/2030总格、24360读出、单load；所有36步、最终latent和93帧RGB与旧Native一致，三轮输出一致，source/input/older-anchor SHA及旧标签未改变。原runner、监督器、容器、guardian和UUID锁均释放，原计算模式安全恢复Default。

完整独占监测11392样本，最大相邻间隔2.994716秒，末次至结算也满足45秒门槛。实际费用 **6.916276265660094 GPUh**，原权威账本已结算。原1624的6.900543598864 GPUh保持，不重复运行或重复计费。价格结算后池used132.5628281559511、reserved16.5（旧两卡未知责任）、available76.93717184404889、cap226。

旧标签bundle SHA `66ea189aaaa7013693976cc337b80744d892359f749607b710dbb364ebecf2f0`；新独占价格bundle SHA `54a73d1e103846578af6a9752fb5eef3c65a08e15a19fd20e800f260fea0f4d2`。新bundle绑定两者，不覆盖旧原件。

## 全1624价格诊断

[完整描述分析](../reports/wc_policy_price_refresh_full1624_descriptive_analysis_20261023.json)由[独立CPU分析脚本](../scripts/analyze_wc_accepted_price_refresh_r1.py)重新核对接受原件后产生；全部1624格每动作3轮正式测量，14616次正式读出。另4872次正式路径内warm读出与4872次完整warm路径读出不混入正式统计。

| 动作 | 三轮CV中位数 | CV 95%分位 | CV最大值 | max-source/median-source中位数 | 聚合放大最大值 |
|---|---:|---:|---:|---:|---:|
| C | 0.391% | 0.996% | 4.127% | 1.0074 | 1.0279 |
| A_HALF | 0.358% | 0.908% | 99.418% | 1.0084 | 2.3304 |
| A_ONE | 0.388% | 0.945% | 2.817% | 1.0075 | 1.0194 |

第2/1、第3/1轮比值中位数都约1.000；各场景同格相对4场景中位数的总体中位落在0.9992–1.0013。轮次仍与动作顺序混杂，场景仍与执行位置混杂，不能据此声称消除了所有时间漂移。

**保留一个明确尖峰。** `misc_13398218_3840_2160_60fps`、source12→target25、A_HALF三次正式秒数为1.435333、0.284616、0.284724。没有删点、补跑、换均值或改max-source规则。按既定“每场景取最坏源，再4场景等权”聚合，target25 A_HALF报价0.383983秒；该最大源相对于同场景次大源对4CAL最终报价贡献0.093881秒差额。这个比较只描述影响，不生成替代价格。见[尖峰范围原件](../reports/wc_policy_price_refresh_outlier_scope_20261023.json)。独占接受来自完整硬件/原件/财务证据，不是来自低CV；没有事后增设阈值或抹去这处观测。

## PG-P1准备与一次实际派发

[新CAL_SELECT核查](../reports/cara_CAL_SELECT_exposure_before_P1_20261023_2022.json)：3193份本地JSON与53份四卡输出元数据，0未知提及、0读取错误、0 SELECT执行命中。该结论仅覆盖登记审计范围，不宣称覆盖无记录的外部执行；第一次SELECT前仍由原runner再次核查。

完整生产CPU沿用[657](657_CARA_PG_P1_FULL_CARD_COMBINATION_CPU_ACCEPTED_AND_PRICE_HANDOFF_20261023.md)已独立接受的R3，不重派。新[不可变stage](../reports/cara_PG_P1_full64_stage_ref_20261023.json)复制该闭包和已接受SM89端口，绑定旧标签、新价格、曝光原件与整卡报价。[fresh preflight](../reports/cara_PG_P1_full64_preflight_20261023_2027.json)通过：GPU3空闲、无MPS，盘约53.40GiB，MemAvailable约73.14GiB，余额覆盖10.5 GPUh。

首次控制器派发在授权文件写出后、intent与子进程创建之前遇到`NameError: name 'os' is not defined`。保存[原失败](../reports/cara_PG_P1_full64_GPU_launch_20261023_2025.json)、[原句柄恢复](../reports/cara_PG_P1_full64_GPU_recovery_20261023_2025.json)和[0 GPU证据](../reports/cara_PG_P1_preintent_failure_diagnostic_20261023.json)：无intent、launch、guardian/log、输出目录、账本job或容器，原授权SHA可复核。

只修复本地派发控制器导入，并增加受原失败及授权SHA约束的`resume-authorization`。原授权字节和launch ID保持；恢复先fresh准入，拒绝已有原intent/输出/账本/log，以独立恢复记录继续。新增测试实际执行派发body的CPU文件写入/fsync与恢复路径，子进程由fixture替代，不调用SSH/sudo/CUDA；[10项检查通过](../reports/cara_PG_P1_preintent_repair_CPU_20261023.json)，修复`9e80fa73`发布后才继续。生产stage、科学配置和CPU证明不变。原授权controller为`6bb8390a`，恢复controller为`9e80fa73`，不回填混同。

## 唯一当前原卡与检查

- [实际启动](../reports/cara_PG_P1_full64_GPU_actual_launch_20261023_2030.json)：launch `39b4481a-79a7-4dff-92aa-0498a03c3e78`；run `cara-pg-p1-cal-fit4-select2-full64-ada-r1`。
- source `170c50e6c289a93cb60d13ead918fdb258177746`；stage `/data20t/gaokuangda/worldcache_workspace/.sync/cara-pg-p1-full64-ada-r1-20261023`；注册 `31cc191345c36e31ed6dbad4109c859ffa0594da3ce87590beff46f1e774d4f7`。
- GPU3 `GPU-d4868f0a-29df-9077-82db-77f7bf0f9934`；guardian1148066/start954342805；supervisor1148129；runner1148184/start954343237/UID1000。
- [初始握手收件](../reports/cara_PG_P1_full64_GPU_admission_20261023_2031.json)、[真实active独占核验](../reports/cara_PG_P1_GPU3_exclusive_active_20261023_2027.json)、[MODEL_LOADING观测](../reports/cara_PG_P1_full64_GPU_initial_health_20261023_2029.json)：唯一原CUDA进程、无MPS、原句柄存活、锁持有、0错误。文件名是命名标签，时刻以observed_unix为准。
- 完整4CAL_FIT/2CAL_SELECT、64位置上限/40评分/2304pairs/4608CFG、单load、Q≤8首批4+一次细化4，forecast8.844444、limit10.5 GPUh。新预留10.5后池reserved27、available66.43717184404889。GPU保持期间搜索、评分与保存均计入实际费用。
- 半程最早10月24日00:51:24.693，安排**00:52**，新一次检查`cara-pg-p1`。终态最早05:31:44.693，复用`cara-bank24-2`为**05:32**。两项已读回同launch，见[准入与排程](../reports/cara_PG_P1_actual_admission_and_schedule_20261023.json)。

后续只capture/recover这个原句柄，绝不再次launch或resume。Native warm2+FIT4先建立干净完整请求时钟，固定B=.80；候选冻结后才接SELECT。终态独立复算原请求、全部93帧LPIPS、候选与最终排序，以及完整独占/费用/释放。失败或无可行策略保留原件与费用，不补查询。小规模历史窗口shadow与少步Native保持P2独立报价与生产接受，不塞入本64位置范围。

20:30补充只读复核：[原句柄进度](../reports/cara_PG_P1_full64_GPU_after_load_20261023_2030.json)仍为MODEL_LOADING、0失败，原guardian/supervisor/runner/container存活且无错误行。文件名after_load只是标签，不代表模型已加载完毕；按实际health陈述。未读取候选或部分质量结果。
