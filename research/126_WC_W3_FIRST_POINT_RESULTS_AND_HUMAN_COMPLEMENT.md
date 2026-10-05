# W3 首个真实刷新点结果与缺失 Human 点补验

2026-10-05。继续 WorldCache/W3，先完成原两个科学点，不增加 Head、LoRA、稀疏搜索或人评。

## 已完成结果

原批准卡 WC-W3-SMALL-CD-R1-20261004-A/source c12a3cad2cefd3559d60a5256d74d802eb151bab 按限时退出124。实际3872.257984秒，累计12.0979429045467/24GPUh、46jobs、无inflight；资源释放及费用独立审计通过。原2父/12后缀/8新输出/2科学点保留，整卡失败不改写。

常识点call45/CFG0完成完整父轨迹、全部六后缀、四输出、历史WC与Native来源桥及CPU独立回读。两条相对Native的视频均为完整93帧、432×768 RGB、匹配PTS；LPIPS v0.1 Alex/CPU FP32，无缩放/裁剪/抽帧。

| 分支 | Native-relative LPIPS | 后缀full调用（CFG0/CFG1） |
|---|---:|---:|
| C：强制当前复用 | 0.36344045753120097 | 8/8 |
| D：当前完整刷新 | 0.33315327443102355 | 8/7 |

C−D=+0.030287183100177417，D相对C失真少8.33%。D完全复现原WorldCache在此处本已选择的动作与结果；强制C使后续完整调用净增1。这个结果确认原刷新有价值，不是新调度方法胜出，也不是同预算、正式训练标签、独立确认或物理正确性结论。Human点缺失，不补零、不从两点分母删除。

[CPU全帧原件](../reports/wc_w3_small_cd_failed_card_lpips_cpu_20261005.json) · [103项独立审计](../reports/wc_w3_small_cd_failed_card_lpips_cpu_audit_20261005.json) · [原卡完整记录](125_WC_W3_SMALL_CD_APPROVAL24_AND_EXECUTION.md)。

## 独立缺失点补验草案

新身份 **WC-W3-SMALL-HUMAN-COMPLEMENT-R1-20261005-A**，run `wc-w3-small-human-complement-r1`，只补human_199/seed0/CAL index2/step22/call46/CFG1。1完整父轨迹36更新72CFG，6完整后缀各14更新28CFG，4新输出（父WC、OFF1、C_first、D_first），1已登记匹配Native35；顺序OFF1/OFF2/C_first/D_second/D_first/C_second及全部重复、同输入、已支付probe、自身CFG历史和父恢复规则不变。

原常识点和失败卡不覆盖、不重跑。原进程的内存快照未保存为可重启全状态，本卡重新支付Human父轨迹成本。新卡完成后分别陈列两卡费用与来源，再形成原两科学点的跨卡矩阵；不会把原GPU卡改判成功，跨卡证据也不冒充同一批次的干净加速计时。

[显式1/6/4/1范围](../configs/wc_w3_small_human_complement_r1_draft.json)与[独立核心来源差异](../manifests/wc_w3_small_human_core_derivation_20261005.json)：原2父核心不改，独立Human核心只改变父数/目标/标识/计数与对应文字，全部采样、恢复、控制、编码和历史桥AST保持原逻辑；严格行校验复用原函数。禁止复制Human成两个伪场景去满足旧2父合同。

## 完整费用与执行边界

同一诊断控制的实测常识parent-with-controls为3033.439130秒，加载98.382509秒，覆盖全部六后缀/三个后缀编码与原父编码。额外登记60秒bookkeeping、30秒退出释放，名义费用3221.821638秒；父诊断费用乘1.3的压力代理4131.853377秒。Human的自适应C/D后续费用尚未实测，两者都不是硬上界。

拟单次总上限**4500秒**、child4470秒、kill grace5秒、释放余量30秒，准入另留15秒。最大GPU支出1.25h；当前余额42847.405544秒，按4515秒准入包络扣后余38332.405544秒，若花满4500秒累计13.3479429045467/24h。只作算术可容纳，不选择GPU、不预付。见[完整费用](../reports/wc_w3_small_human_complement_cost_r1_20261005.json)。

原已批准的3900秒卡已执行；24h是累计上限，直接批准绑定原card/run，不构成新4500秒单次授权。新卡必须独立生产入口、监督/预算/终态/评分绑定及实际CPU门准备齐备，再取得具体执行确认与fresh GPU UUID/VRAM/compute/f1锁/无inflight准入；不得直接调用旧3900秒启动脚本或复用旧run。

## 当前准备状态

本地14项范围拒绝、原核心SHA与允许差异AST、完整费用重算通过；独立单场景核心和沿用冻结Video2World类的CPU完整管线夹具已写入。服务器实际单场景CPU尚待，生产入口/新卡授权/新GPU/新视频/第二点收益均未完成。旧2父GPU回执与评分已经完成，不重复其CPU回归。

下一顺序：单场景核心实际CPU及独立原件回读 → 新1/6/4生产/终态/评分接线 → 缺失点完整GPU卡及全帧CPU评分 → 按真实成本与两点证据准备B四对同CFG配额交换。C/D首动作实验测的是自适应后续策略的后果；B才检查相同完整调用配额的计算位置。任何一层有益都不自动证明在线方法或论文优势。
