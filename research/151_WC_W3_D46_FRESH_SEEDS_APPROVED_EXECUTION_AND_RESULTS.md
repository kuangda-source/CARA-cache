# W3 D46 两个新 seed 完整复验：直接批准与执行

2026-10-08。用户直接答复“好的 允许这次实验”，对应已说明的完整卡 `WC-W3-D46-FRESH-SEEDS-R1-20261008-A`：seed1/2、2条Native+2条WC父轨迹、12条完整后缀、10段新视频和两组有符号质量/成本比较。单次预计2.422930905 GPUh的例外已经获得，累计24 GPUh及18.906279766h旧费用保持，不再等待该卡授权。

冻结的新科学/运行/监督/评分源码与实际CPU通过原件保持；本次只新增具体批准、选择配置和部署绑定。BASE保留原生自适应，REFRESH只在call46完整计算一次后继续同一策略；原生已D的no-op、失败和拒绝保留，不换seed/调用，不增加训练、稀疏搜索或人评。LPIPS为原生相对保真，诊断wall不作干净加速，同prompt新seed不作跨场景独立CONF。

[直接授权](../manifests/wc_w3_d46_fresh_seeds_gpu_authorization_20261008.json) · [选择配置](../configs/wc_w3_d46_fresh_seeds_r1_selected_20261008.json) · [完整准备与设计](150_WC_W3_D46_FRESH_SEEDS_CPU_AND_CARD.md)。下一步为选择配置的实际授权/source/CPU原件门，以及fresh GPU/锁/预算的唯一准入；当前尚未GPU提交，无新科学结果。旧blocked为授权到达前的历史，goal工具当前active。
