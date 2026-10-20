# WC主对照固定官方推荐配置：直接人类修订（2026-10-20）

用户明确要求“wc 不用调参吧，直接用官方配置对比就行了”。后续未冻结主对照固定为官方README推荐的Text2World算法配置；新增WC扫阈值从必要流程中移除。已有N05完整扫描、N07/N08的WC_HALF及其质量/时间/缺失原件保持原身份，作为补充或历史开发证据。

## 官方配置身份

固定WorldCache源commit `60a486df6d2e6d2aa3c21815895aac157a88e95d`。官方推荐命令明确开启flow/OSI/saliency/动态阈值，motion_sensitivity=2、flow_scale=2、saliency_weight=1；省略的rel_l1_thresh从入口config取0.06，probe_depth=2、ret_ratio=0.2、num_steps=35。不是只开worldcache_enabled后让推荐模块处于关闭的构造默认状态。完整12参数、官方README/config/inference原字节SHA与链接见[固定策略](../plans/cara_v6_20261020/WC_OFFICIAL_BASELINE_POLICY_20261020.json)。

WC_DEFAULT原阈值0.06与官方入口相同；能否复用其视频仍需全参数/输入/seed/模型/solver/runtime/计时身份兼容，不能只靠名称和阈值追认。WC_HALF=0.03和WC_DOUBLE=0.12始终是历史调参点，不能重新标成官方默认。

共同评测仍统一输入/seed/checkpoint/solver/规格/精度/计时，guardrails保持启用；README示例disable_guardrails不会覆盖原共同协议。torch.compile/offload等共同系统配置单独记录。该比较标为“WorldCache，官方推荐算法配置、共同评测协议”，不宣称完整复现原论文全部硬件和benchmark。

## 未来未冻结范围的调整

- R3不再以WC调参完成为前置；原两预算48逻辑格中的同一官方WC四CAL点只测/复用一次，先形成最多44个不同身份，再做其他兼容去重。官方WC点超出某预算时按实际点展示，不人为调整其阈值凑预算。
- R4-A保留12新prompt×双seed×7角色=168正式设计，WC角色由TUNED_WC改为WC_OFFICIAL_RECOMMENDED。R4-B原72逻辑格中相同12个WC端点复用A，先记新增≤60/联合≤228；原设计上限保留供追溯，实际完整卡仍需全链CPU、费用与权限门。
- R6最终角色尚未冻结，需确保官方WC重复时间覆盖；如增加角色，先完整重价/实际CPU，不能用旧WC_HALF代替，也不能悄悄删掉另一已登记对手。
- RA、直接近邻、强前密、候选自己的选择协议保持。以固定WC的实测对比支撑相应主张；单官方点不自动证明整个调参前沿都被支配。

本次仅本地源码核对和计划更新，0SSH/服务器CPU/GPU/新评分/账本写。原BANK24 stage/source/gate/CPU证明及其资源自动化完全不改，首轮32路径配置与报价草案不变；新方法生产CPU/GPU结果仍空。cap226、origin历史、整卡严格<12自主及≥12/余额不足具体整卡确认保持。
