# 预算更新：从当前起新增可用48 GPUh

2026-10-09。用户先要求“把 gpuh 预算提到 48h”，随后明确“是从当前开始 48gpuh”。按澄清执行为新的可支用窗口，而非累计48上限，也非旧50再加48。

## 已落实的额度

| 项目 | 数值 |
|---|---:|
| 变更前累计上限 | 50 GPUh |
| 窗口起点已实际使用 | 29.895246589658527 GPUh |
| 从当前起新授权可用额度 | 48 GPUh |
| 新累计上限：起点实费＋48 | 77.89524658965853 GPUh |
| GPU提交计数 | 65，未改变 |

[直接用户授权](../manifests/budget_authorization_20261009_wc_new_window_48gpuh.json)记录原始请求、澄清、窗口起点、旧预算SHA及单次规则；[服务器变更回执](../reports/wc_budget_new_remaining48_update_20261009.json)记录前后完整账本和SHA，原native字节压缩保存。服务器共享锁下核对账本、无在途/目标计算进程后，原子替换预算；本地回读同字节。

没有归零used_gpu_hours、清除失败/加载费用、改提交数或追认任何结果。旧四次预算授权完整保留，并追加本次授权，权威账本新SHA为 `ff46b7cb51f2e43bc78bc7c6a5c8a4e2026d9846d1fec5106e2e83ec8d231b35`。账本原科学status文字不因扩额伪改。

## 对新计划的影响

[统一方法设计](../plans/WORLD_CACHE_INTEGRATED_MULTI_FIDELITY_DEVELOPMENT_20261009.md)和[首窗口](../plans/WORLD_CACHE_MULTI_FIDELITY_FIRST_WINDOW_20261009.md)中的约20GPUh是首批开发提案，现在属于48新窗口的一部分，不再表示所有余额；其余28GPUh尚未分配为已注册作业。具体后续确认/修订根据实测结果和成本另登记，不为花完配额扩大矩阵。

实际费用仍从原used值递增，当前窗口耗费＝当前used−29.895246589658527；可用＝77.89524658965853−当前used。只使用新的权威授权/账本，不新建清零费用账本。

## 执行边界

单次完整任务预测≤2GPUh的原自主规则保留；>2GPUh仍须具体直接批准。此次仅更新预算，没有批准旧H-T63的6.704GPUh整卡、选择GPU、执行新算法或训练，也没有变更任何冻结实验分母。

旧生产源码/配置中绑定50上限与旧授权的严格检查保持封存，不能直接拿旧stage执行或绕过检查；新执行卡须绑定本次授权、新累计上限、完整成本，重新验证受预算/授权变化影响的CPU入口。原科学核心与CPU/真实历史结果不重写，预算变化不等于新方法验证。

交付回读：服务器与本地账本/授权逐字节相同，原费用、65次提交、旧授权、冻结配置和生产源码保持；10个入口旧正文与25处本地链接通过[独立核验](../reports/wc_budget_new_remaining48_independent_readback_20261009.json)。[组会飞书文档](https://lcnssrlun9lz.feishu.cn/docx/HTSIdK0uLofCG5xUI1IcTKaCnAh)由revision31更新为32，原165块完整保留，新增预算说明的文字与链接相符，见[CLI全量回读回执](../reports/wc_group_meeting_feishu_new_window48_verification_20261009.json)。本轮新增GPU提交为0。
