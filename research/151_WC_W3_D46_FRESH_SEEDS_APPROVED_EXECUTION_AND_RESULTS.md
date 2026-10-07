# W3 D46 两个新 seed 完整复验：直接批准与执行

2026-10-08。用户直接答复“好的 允许这次实验”，对应已说明的完整卡 `WC-W3-D46-FRESH-SEEDS-R1-20261008-A`：seed1/2、2条Native+2条WC父轨迹、12条完整后缀、10段新视频和两组有符号质量/成本比较。单次预计2.422930905 GPUh的例外已经获得，累计24 GPUh及18.906279766h旧费用保持，不再等待该卡授权。

冻结的新科学/运行/监督/评分源码与实际CPU通过原件保持；本次只新增具体批准、选择配置和部署绑定。BASE保留原生自适应，REFRESH只在call46完整计算一次后继续同一策略；原生已D的no-op、失败和拒绝保留，不换seed/调用，不增加训练、稀疏搜索或人评。LPIPS为原生相对保真，诊断wall不作干净加速，同prompt新seed不作跨场景独立CONF。

[直接授权](../manifests/wc_w3_d46_fresh_seeds_gpu_authorization_20261008.json) · [选择配置](../configs/wc_w3_d46_fresh_seeds_r1_selected_20261008.json) · [完整准备与设计](150_WC_W3_D46_FRESH_SEEDS_CPU_AND_CARD.md)。下一步为选择配置的实际授权/source/CPU原件门，以及fresh GPU/锁/预算的唯一准入；当前尚未GPU提交，无新科学结果。旧blocked为授权到达前的历史，goal工具当前active。

## 选择门通过，原GPU进程已启动

选择配置的实际source/assets/具体批准/同源CPU原件门exit0，19.415571秒，CUDA未初始化，未重复旧核心夹具或模型。source `fb890da58a21d7403ce23f98d2ca1b173cc69b25`，科学运行代码SHA与原实际CPU通过源保持。完整2Native+2WC父/12后缀/10新视频/两signed不缩减。

唯一run `wc-w3-d46-fresh-seeds-r1` 已按fresh目标A6000 24MiB/noapps、共享锁及18.906279766/24h账本准入提交。原supervisor **3190813** / runner **3190976** 的真实CLI、stage/source/目标GPU进程均确认，当前模型初始化中，目标占用24514MiB；未生成新视频或科学结果。具体GPU运行已开始，不把批准或healthy进程当成方法有效。

原CPU后处理driver **3193255** 只绑定这两个原GPU句柄和冻结13项载荷；当前WAITING、零评分。仅在原GPU成功结束、原PID退出、锁及GPU释放后，自动执行完整源/费用/状态恢复/视频审计与全部可用的93帧LPIPS，保留no-op/拒绝/负例。CPU失败也保留日志，不重复提交GPU。

服务器第56job在途，used=24h是持锁期间预留全部剩余余额的保护状态，非实际耗尽；最近已结算实费18.906279766h保持，结束后按全部wall实际结算。旧秒数deadline不恢复，累计24h保护仍在。goal active，仅跟踪本次原run，不修改冻结源或重启旧任务。

[实际选择CPU原件](../reports/wc_w3_d46_selected_preflight_native_20261008.json) · [唯一GPU提交](../reports/wc_w3_d46_fresh_seeds_gpu_launch_20261008.json) · [PID/GPU现场](../reports/wc_w3_d46_fresh_seeds_gpu_start_live_20261008.json) · [CPU接续绑定](../reports/wc_w3_d46_postrun_cpu_launch_20261008.json)。
