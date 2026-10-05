# W3 小卡直接批准、累计24 GPUh与真实执行（2026-10-05）

用户直接批准：`批准 WC-W3-SMALL-CD-R1-20261004-A，把累计 gpuh 限制提升到 24`。

## 当前阶段与科学结果

**本卡BOUNDED_TIMEOUT/exit124：实际3872.2579837469384秒、未超过3900秒；累计12.0979429045467/24GPUh、46jobs，无inflight，余额11.9020570954533h。原三PIDs、f1锁和GPU已释放。** 首场景完整36更新/72CFG、六后缀、四视频及历史WC/Native来源桥通过；human_199到step22后OFF1未完成，0新视频。整卡2父/12后缀/8视频/2科学点未通过，第二场景保留缺失。

[真实GPU原件](../reports/wc_w3_small_cd_original_receipts_20261005.json)与[严格终态审计](../reports/wc_w3_small_cd_failed_terminal_audit_20261005.json)已取回。首场景含全部控制parent wall3033.4391295053065秒，六后缀control约318–324秒；名义单后缀120秒代理失准。失败属于费用估计与限时完成问题，不是W3科学负结果；不延长旧cap或重提旧UID。

[服务器实际只读CPU](../reports/wc_w3_small_cd_failed_postrun_actual_cpu_20261005.json)完成9项拒绝控制及终态/5视频各93帧审计，共5.253280秒；[全帧评分](../reports/wc_w3_small_cd_failed_card_lpips_cpu_20261005.json)31.683951秒，监督全wall38.412868秒。[独立103项SHA回读](../reports/wc_w3_small_cd_failed_card_lpips_cpu_audit_20261005.json)确认原源、资产、GPU回执、全部视频与账本不变。CPU源266a8b5与冻结GPU源c12a3ca分开，CUDA未初始化、评分GPU提交0。仅严格完整行进入评分，失败整卡仍保持原分母。

| 真实科学点 | C相对Native LPIPS | D相对Native LPIPS | C−D | 后缀full调用（CFG0/1） |
|---|---:|---:|---:|---|
| common_sense，call45/CFG0 | 0.36344045753120097 | 0.33315327443102355 | +0.030287183100177417 | C=8/8；D=8/7 |
| human_199，call46/CFG1 | 缺失 | 缺失 | 未完成 | 原OFF1未完成 |

协议为LPIPS 0.1.4包/v0.1 Alex、CPU FP32、93帧完整432×768 RGB与对应PTS，无缩放/裁剪/抽帧；参考是来源桥通过的同输入同初始噪声Native35。正差说明此处D更接近Native，相对C失真下降8.3335%。C迫使当前复用，却使后缀完整调用净增一次；六次重复不是六独立科学样本。

**原WorldCache在call45已选择D，且D的完整轨迹/视频与OFF及官方WC相同。因此这是原刷新价值的机制确认，不能报新方法优于官方WorldCache。** 不是同配额/同秒数、正式训练标签、独立CONF或物理质量通过；对Human点和W3一般有效性尚无结论。

下一优先准备独立human-only补验卡1父/6完整后缀/4新输出和1历史Native，仍call46/CFG1/step22、OFF/OFF/C/D/D/C，完整重复、父桥、释放与全帧CPU评分均保留。原失败和常识成果不覆盖、不重跑；如果新卡通过，分别陈列两卡费用后才形成原两点的跨卡证据矩阵。新scope/core/生产入口与CPU验证须显式绑定单场景身份，禁止伪造第二场景通过旧2父合同。新卡尚未提交或取得独立单次GPU范围确认，累计24h不等于已批准任意下一卡。

下述启动/在跑段落均保留为历史观察。

## 预算与来源

- 上限13→24 GPUh；已用11.022315686839217h、45jobs不重置，无inflight。余额12.977684313160783h。
- 单次总上限3900秒、child3870秒、kill grace5秒不变。预付一次3900秒，结束按含加载、失败、写盘和释放的实际wall结算。
- [直接授权](../manifests/budget_authorization_20261005_wc_24gpuh.json)与[迁移回执](../reports/wc_w3_small_cd_budget24_migration_20261005.json)。
- [批准配置](../configs/wc_w3_small_cd_approved_r1_20261005.json)与[83文件部署清单](../manifests/wc_w3_small_cd_approved_r1_20261005.json)。原V1/V2、67文件核心、历史CPU阶段和原full RV0保持其原身份。原scope里的13h设计字段是历史，新增 execution_budget_authority 明确绑定24h与本卡，不能用历史草案支出24h。
- 唯一生产逻辑变化是 rv0_small_execution 的预算权威校验；科学核心、运行/监督/审计/读取/评分代码不变。原80文件实际CPU回执原件及所有非预算代码SHA仍绑定；新增预算适配拒绝旧权限、重置、费用超限、并发账本修改、扩大单卡与缩减科学分母。

## 固定科学分母与边界

两个曝光CAL场景 common_sense 与 human_199，seed0；step22状态、target calls45/46分别CFG槽0/1；每场景OFF1/OFF2/C_first/D_second/D_first/C_second。共2父、12完整后缀、8新视频，后缀运行14更新/28CFG至终点。规格768×432/93帧/16fps。

必须验证本次官方WC与历史WC编码桥，再复用两个历史Native35。GPU释放后CPU评价4个完整93帧Native-relative LPIPS，形成2个有符号 C−D 诊断。未来继续原自适应策略，因此两臂费用可能不同；负值、失败与分母保留，不称同预算位置调度、正式RV训练标签或物理质量通过。原8父/24后缀/18输出full RV0不在本卡范围；不开始Head、LoRA、专家训练或扩大稀疏搜索。

## 执行后回填

服务器CPU、唯一GPU终态、按实费结算、首完整行及全帧评分均已回填。整卡限时未通过，human点仍缺。后续先完成独立缺失点补验的具体范围与CPU门，再依据两点证据和实费准备同配额交换；累计预算增加不改变原单卡范围。

## 原始启动句柄

冻结GPU source `c12a3cad2cefd3559d60a5256d74d802eb151bab`；supervisor2856696 / timeout2856713 / runner2856714。fresh selected UUID为 GPU-cebf7119-cf03-23b9-e192-cd196332b704，准入24MiB/noapps。输出目录 `/home/gaokuangda/data/gkd/worldcache_omr/outputs/wc-w3-small-cd-r1`。

[actual CPU](../reports/wc_w3_small_cd_budget24_actual_cpu_20261005.json) · [独立原件审计](../reports/wc_w3_small_cd_budget24_actual_cpu_audit_20261005.json) · [唯一启动](../reports/wc_w3_small_cd_launch_20261005.json) · [启动现场](../reports/wc_w3_small_cd_start_observation_20261005.json)。预算在途12.105649020172551/24h、46jobs，是3900秒预付；终态按实际全wall替换预付，尚非最终实费。

## 真实GPU检查点观察（进行中）

首个OFF1现已完成，下面保留此前快照观察的历史身份；最新结果见文末。

[原始检查点观察](../reports/wc_w3_small_cd_live_snapshot_20261005.json)：原runner2856714确认存活，首场景母轨迹到step22（44CFG），slot0/target45；真实Video2WorldCondition两槽位状态已捕获，首个OFF1完整后缀开始。逻辑张量复制2,828,989,246bytes，独占GPU快照存储2,319,184,538bytes；capture所需余量9,952,945,492bytes、当时GPU可用40,412,774,400bytes。该存储只含快照，不是总峰值显存；余量门通过不代表完整恢复控制或C/D终点已通过。当前无C/D评分，不据live改原任务或重提。

## 首个真实OFF后缀与实际成本（尚未整卡验收）

OFF2现已完成且与OFF1逐轨匹配，下面首个OFF观察保留历史身份；C/D及母轨比较仍待。

[首个OFF原件观察](../reports/wc_w3_small_cd_first_off_observation_20261005.json)：common_sense/slot0 的OFF1完成14更新/28CFG，完整调用按两槽位为8/7，parent_restored记录true；control wall318.15352621208876秒，解码/安全检查/编码38.81982713006437秒。531,916bytes视频原件重新读取SHA与冻结历史WC完全一致。

这是一个真实后缀/视频来源匹配观察；尚未完成OFF2、C/C、D/D与原母轨迹比较，不能代替整个parent历史桥或两场景因果验收。首次真实control成本明显高于名义单后缀代理，接近349.248秒压力代理；完整2父/12后缀/8输出仍可能触发单次3900秒限时。保持原任务与分母，不取消在跑工作、不延长上限、不根据预估重提。终态保存实际费用、完成/未完成矩阵，只有完整对应来源和控制通过的输出才解释评分。

## 首场景OFF重复的独立原始比较

OFF重复已匹配，C_first现已完成，D分支仍在运行，最新动作观察见文末。

[OFF1/OFF2原始重复比较](../reports/wc_w3_small_cd_first_off_repeat_20261005.json)：两个完整14更新/28CFG后缀的 inputs、outputs、deep、banks、solver_outputs、final_latent_sha256、final_state_components 逐项相同，两个parent_restored均true。实际control wall分别318.15352621208876/320.2690637977794秒，原runner仍活。当前已转入C_first；这里只确认OFF重复可恢复，不代替完整母轨原件桥、C/C与D/D、C/D因果结果及两场景最终验收。

## 首个C动作与后续成本观察

首对C/D现均完成完整后缀，以下C观察保留其阶段身份；最新同输入干预见文末。

[C_first原始动作观察](../reports/wc_w3_small_cd_first_c_observation_20261005.json)：call45/CFG0/solver23的native_skip=false，原启发式本会full；本次指定C实际deep=0，paid_probe=true、age=2、同槽位真实full历史17/21，全部事件current_deep_truth_used=false。完整14更新/28CFG与安全视频编码完成，parent_restored=true，control wall324.47217688988894秒。

后缀完整调用按槽位为8/8（总16），OFF原安排为8/7（总15）。这个局部干预虽跳过当前一次full，后续自适应轨迹仍可能增加总完整调用；不能把首步skip当成全后缀节约。C视频与OFF不同，尚不能仅凭差异或文件大小判断质量。当前D_second正在运行，需C/D同输入、C/C与D/D、完整母轨桥及最终评分后才解释刷新收益；不称本方法已改善调度。

## 首对真实C/D同输入动作与完整后缀

首场景全部六个后缀现已完成且重复匹配，以下首对动作观察保留历史身份；母轨迹与整卡验收仍待。

[独立原始动作比较](../reports/wc_w3_small_cd_first_pair_action_observation_20261005.json)：C_first/D_second在call45前及当前model输入前缀相同，paid_probe均true，age均2。C实际deep0，D实际deep26；全部28CFG事件均无current-deep-truth泄漏，两个parent_restored均true，两个完整后缀均14更新/28CFG。

C的full配额为8/8、D为8/7，实际control wall324.47217688988894/320.5572475194931秒。D与OFF的完整轨迹及最终状态逐项相同：此处原WorldCache已经选择full，D复现原安排，并非新调度方法取得收益。强制C导致其后自适应完整调用净增1，当前不是同配额实验。D_first重复及C_second、完整母轨视频桥与两个场景最终验收仍待；尚无C/D Native-relative评分，不产生正式RV训练标签。

## 首场景全部六后缀的重复与顺序控制

[独立原始重复比较](../reports/wc_w3_small_cd_first_scene_repeats_20261005.json)：OFF1/OFF2、C_first/C_second、D_first/D_second 各自的输入、输出、deep、banks、solver轨迹、最终latent与完整状态逐项相同；六后缀均14更新/28CFG，parent_restored均true。C/D同输入deep0/26再次核对通过。六control wall为318.154/320.269/324.472/320.557/319.746/322.803秒，C仍8/8、D仍8/7。

三个后缀视频已安全编码。母轨迹已经恢复继续运行，但尚未到终点并生成原母轨视频，因此这里只接受单场景六后缀的重复/动作控制观察，不称母轨完整桥、两场景整卡或最终质量通过；不将六次控制当作六个独立科学样本。
