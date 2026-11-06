# W3 Human补验完成：真实刷新干预的机制正结果

2026-10-05。已完成用户批准的唯一WC-W3-SMALL-HUMAN-COMPLEMENT-R1-20261005-A：1母轨、6完整后缀、4新视频。GPU source为8a46fcce95dee7f0b2ddeca8fd273a223c147c49；额外CPU路径修复source为bbff172e83bcf94239f4b48ee34454b0693e5d05，原GPU源码和原件不变。

## 已确认结果

Human199、seed0、曝光CAL index2，step22恢复、target call46/CFG1。36次UniPC/Karras更新/72CFG，768×432、93帧、16fps。C强制复用，D完整刷新，其余仍由原WorldCache自适应续推。

| 指标 | C复用（也是原WorldCache选择） | D刷新 |
|---|---:|---:|
| 相对匹配Native35的全93帧LPIPS | 0.4247454244603393 | 0.4128185776613092 |
| 后缀完整调用，两CFG分别计数 | 10 / 8 | 8 / 8 |
| 第一次后缀控制wall秒，含诊断开销 | 326.503529 | 320.992239 |
| 第二次后缀控制wall秒，含诊断开销 | 328.487381 | 321.037228 |

**C−D=+0.01192684679903011，D的Native相对感知失真降低2.8079989%。** C视频SHA与历史WorldCache完全一致；D输出不同。D不仅改变当前计算，还让后续两个CFG的合计完整调用从18减为16，减少的是CFG0的两次完整调用；CFG1总数仍8。这支持“当前刷新会改变后续计算需求”的机制解释，但不是固定刷新配额实验。

控制wall含快照恢复、哈希、同步和记录，不能作为干净加速；LPIPS为原生参考保真，不能升级为物理或整体语义质量提升。这里是一个已曝光场景/一个seed/一个CFG动作点的真实反事实诊断，尚无在线规则、独立确认或方法质量—时间前沿。

## 完整控制与来源

OFF1/OFF2、C_first/C_second、D_first/D_second各自28CFG/14更新的全部输入、输出、deep、banks、solver和最终latent/完整state逐项相同。C/D干预输入相同，实际deep分别0/26；已支付probe、过去自身同CFG真full历史、不用当前deep truth、父恢复及完整pipeline均通过。母轨36/72与OFF continuation/编码和历史WorldCache严格SHA桥通过。四新输出加一历史Native均完整解码93帧。

[GPU原件](../reports/wc_w3_small_human_original_receipts_20261005.json)、[终态审计](../reports/wc_w3_small_human_terminal_audit_20261005.json)、[全帧评分](../reports/wc_w3_small_human_lpips_cpu_20261005.json)、[150项native SHA回查](../reports/wc_w3_small_human_lpips_cpu_audit_20261005.json)绑定原件。GPU runner解压SHA51697e502930a9713e86dfe993b38822fdb68f4f9ab167cc005ae56b06a34923，GPU supervisor SHAeed04cc543f01bbfcc38614a212acc8a7691c6edfd8a035b24e83206d8bfb7ac。全帧CPU评分保持LPIPS0.1.4/v0.1 Alex、FP32、无裁剪/缩放/抽帧，CUDA未初始化。

首次CPU终态13.971205秒因expected输出根未resolve、项目实际为符号链接而失败；失败回执和日志保留。修复仅将根也resolve：普通/符号链接两接受及七越界/缺来源拒绝通过。新独立CPU入口逐字校验新旧eval只差这一行，仍使用原冻结CLI/依赖和全部科学合同。修复版实际终态18.969837秒，CPU评分主体34.855632秒、含初始化监督全wall44.392275秒；GPU及首次失败原件未覆盖。这是审计实现修复，不是放宽路径或科学门槛。旧gt_frames前缀SHA差异及未知原因仍保留，不改同状态C/D要求。

## 费用、跨卡口径及下一步

唯一Human GPU exit0，实际总wall3246.4923400320113秒=0.90180342778667GPUh，小于4500总上限；1522条monitor的峰值31932MiB。原supervisor/timeout/runner三PID退出、f1锁空闲、指定GPU24MiB/无compute进程。累计12.99974633233337/24GPUh、47jobs、无inflight，剩11.00025366766663h；不重置历史使用。

[跨卡R4](../reports/wc_w3_two_point_summary_r4_real_complete_20261005.json)确认2/2真实科学点：Common C−D=+0.0302871831、Human +0.0119268468，场景等权均值+0.0211070149496。Common原WorldCache本已选D，所以它验证原选择；Human原选择C，所以本点才显示改变原选择的局部调整空间。两场景均曝光，相关重复不是独立样本，均值不作总体显著性。正式RV训练标签、同配额和CONF接受仍未成立。

原双场景卡依然BOUNDED_TIMEOUT/124，其3872.2579837469384秒、未完成Human前缀和原2/12/8分母均保留。两卡实际总GPU费用7118.75032377895秒；累计物理计划3父/18后缀/12视频，实际开始3父/13后缀，完成12后缀/8新视频。跨卡补齐科学点不追认旧卡成功，也不能报同一干净批次。

**继续WorldCache W3，下一先完成同配额B位置交换的生产核心和CPU接线。** 保持原四对、2父/16后缀/10新输出及所有OFF/BASE/SWAP重复，测两位置联合收益。[完整实费重估](../reports/wc_w3_placement_cost_from_real_cd_r2_20261005.json)取两实际母轨含控制6115.563秒、四额外后缀、两额外编码及一次启动/退出代理，名义7684.635秒；加20%规划余量与30秒退出为9251.562秒。9600总/9570child/kill5仅下一新卡草案，费用不保证、GPU未选/未批准/未提交，旧3460秒代理不再用于准入。先真实B合法性与收益，再冻结廉价在线规则并做新seed/场景确认；Head/LoRA和稀疏扩大仍后置。非必要不新增人评。

---

以下为批准、执行与阶段观察的历史记录。

# W3 Human缺失点：直接批准与单次执行

## 最新观察：首个OFF完成，前缀差异保留

更新：OFF1/OFF2两完整后缀的输入、输出、deep、banks、14步solver、最终latent及完整state逐项相同，[独立重复核对](../reports/wc_w3_small_human_off_repeat_20261005.json)。OFF2 control326.342188秒。C_first完整后缀326.503529秒/full10/8，编码视频SHA与原WC及OFF1一致；原WC此处本已选C。第一个D（D_second）在跑，后续CC/DD重复、完整母轨桥和评分仍待；单卡4500秒及源码不变。

[OFF1原件](../reports/wc_w3_small_human_first_off_20261005.json)完整14更新/28CFG、full10/8，control329.272674秒、解码/guardrail/编码43.806264秒。新视频1100497字节、SHA4d0f0549dbabf04e7f217037c40f6a30f41cb240289162d6fb0fbec2dde982fb，与历史Human WC一致。重复控制、母轨桥及C/D整卡接受和评分仍待。

[step22前缀核对](../reports/wc_w3_small_human_prefix22_compare_20261005.json)保留实际差异：44个输入记录的gt_frames SHA不同，其余参数相同；44预测、deep执行和22solver输出逐项相同。固定MinimalV1LVGDiT.forward首句del kwargs，gt_frames不是显式参数且函数不读取kwargs，这个额外字段不进入实际net forward。差异原因为UNKNOWN，不能报全部输入字节相同；未修改在跑源码或同状态C/D合同。完整历史视频桥继续严格要求，OFF1桥不代替母轨桥。以下部署条目为当时观察。

2026-10-05。用户回复“允许”，对应此前提报的 **WC-W3-SMALL-HUMAN-COMPLEMENT-R1-20261005-A**。新卡范围确认门已解除，持续研究目标恢复active。

执行完整1父/6后缀/4新视频，Human199/index2/seed0、step22/call46/CFG1，36更新/72CFG；全部OFF/CC/DD、同状态/已支付probe/过去自身锚点、历史WC编码桥、费用与释放门保持。总4500秒/child4470/kill5，最多1.25GPUh，计入现有24GPUh；不重置原12.0979429045467h/46jobs、不重跑常识点，不重提旧run。

[授权原件](../manifests/wc_w3_small_human_gpu_authorization_20261005.json)保留直接回复与具体范围；[批准配置](../configs/wc_w3_small_human_approved_r1_20261005.json)绑定R2实际CPU原件4d59051a454265d834be834768ef3b8b1b5679e225bc7cbaba9b2ef016967d7a和冻结109文件。新GPU stage110文件，只换GPU选择/授权绑定及配置，全部生产源码保持。已通过的CPU核心/8生产步骤不重复，运行前实际selected validate-only再查授权/原件/来源。

预备现场已见单张A6000 UUID、24MiB、无compute进程、f1锁可用、数据盘约559GB空闲和无inflight；这不是最终准入。唯一提交前由监督器重新准入，预付4500秒一次，终态按实际全wall结算。原2/12/8旧卡失败与3872秒费用保留。

当前状态：批准及配置绑定完成，部署/selected门和实际GPU执行待完成；没有Human新科学结果。结束后真实GPU来源、1/6/4完整轨迹、5文件全93帧、费用/PID/锁/释放审计，再执行CPU两LPIPS及一有符号差值，按128跨卡口径合并。任何失败保留原分母和费用，不能将初始化或CPU通过报收益。

## 实际部署与唯一启动

selected前置门实际通过，12.254286秒、新授权与R2原件验证，110文件source冻结；原件SHA e172ec4f5f4d5464a1cf3785be3f2a5a29bf25211c82a7511dd91a3588e99797。GPU source **8a46fcce95dee7f0b2ddeca8fd273a223c147c49**。[启动回执](../reports/wc_w3_small_human_launch_20261005.json)与[现场](../reports/wc_w3_small_human_start_observation_20261005.json)确认 supervisor2882869 / timeout2882885 / runner2882887 三句柄存活，进入初始化/模型加载；不能据此称Human干预或质量已通过。

预算一次预付4500秒，当前在途13.3479429045467/24h、第47job，原已结算12.0979429045467h/46jobs保持；预付不是实际最终费用。child起算限时北京时间 **2026-10-05T19:25:45.905665+08:00**，总4500秒保持。只监测原句柄，不改在跑source/stage、延长或重新提交。完成/失败后按实费/原1/6/4分母审计，GPU释放后两全93帧CPU LPIPS。
## GPU终态与CPU审计路径修复

唯一Human GPU已exit0：实际总wall3246.492340秒，1父36更新/72CFG、六完整后缀、四新视频与历史WC桥完成。全部OFF/CC/DD重复及同输入C0/D26通过；C full10/8、D8/8。累计12.99974633233337/24GPUh、47jobs、无inflight，原三PIDs/锁/GPU已释放。GPU source仍8a46fcce95dee7f0b2ddeca8fd273a223c147c49；原件SHA见新original_receipts。

首次CPU终态审计13.971205秒exit1：expected root未resolve，而artifact已resolve；服务器project为/media数据盘的符号链接。[路径诊断](../reports/wc_w3_small_human_audit_path_failure_20261005.json)记录四文件canonical路径确实在本run根内、字节SHA和GPU原件/账本不变；[失败原件](../reports/wc_w3_small_human_failed_path_audit_originals_20261005.json)保留。修复只把expected输出根也resolve，不减控制、范围或来源门。本机两接受/七拒绝通过，无Torch或GPU。独立CPU修复入口明确核对新旧eval源码仅一行差异，然后使用原冻结CLI/dependencies；原GPU stage、config及回执保持不改。实际修复CPU终态/评分/2点汇总仍待，不能把完整GPU执行报Human收益。以下为阶段观察。
