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
