# B36执行承接：双端CPU已接受

用户要求补齐B36执行承接的CPU验证，并保留实际基线选择直到A32完整验收后冻结。2026-10-29已接受[双端CPU回执](../../../../reports/cara_fast_B36_CPU_acceptance_r1_20261029.json)。本次未读取A32实际输出、未冻结实际基线、未启动B36 GPU，原A32源/配置和自动检查未改。

[共享源复核](../../../../reports/cara_fast_B36_common_source_QA_r1_20261029.json)确认14个共享源码与A32实际启动的`9eaa5eb3`逐字节相同，16个runtime源码SHA与A32接受记录相同；复用未改动的采样、度量与终态控制证据。

## 已实现的承接

`src/wcomr/cara_fast_b36_r1.py` 复用原R2请求路由与收集器，只补A32到B36的边界：

1. `read_handoff` 显式读取六个原件：完整A32 terminal capture、中央实际费用settlement、12对评分manifest、评分容器终态capture、已接受scores和原一次冻结文件；不搜索或读取部分运行结果。
2. `bind_handoff` 重新核对原件字节与完整接受链，要求A32技术接受、中央费用已结算、GPU已释放；B必须使用同一host和物理UUID。共享14个采样/校验源码SHA必须与A32一致。它在临时文件中核对原确定性冻结规则与已有冻结文件完全一致，不创建、修改或覆盖实际A冻结文件。
3. `make_requests` 将已验证冻结结果交给原 `cara_fast_requests_r2.Requests`，保留原模型/采样器/WC/RA/Native实现。B adapter拒绝A槽位；CPU合成包拒绝生产GPU上下文。生产使用仍需调用方提供另外获批且已准入的B36上下文，绑定新launch、36条、原freeze SHA和同一UUID；本库不授予GPU权限。
4. `execute_B36` 用原收集器一次执行原6预热+24正式+6重复，完整36分母不可拆分。已存在的输出目录在执行前拒绝；写出异常保留完整分母、失败和未到达位置，失败槽位不可重试。
5. `check_complete_B` 核对有序36条、实际选中角色、Native请求22/24对应实际更新23/25、双时钟与零研究计数。`formal_sources` 解析32个正式来源：24个B新正式与8个A复用，不重复计新样本。

## 双端实际CPU覆盖

| 项目 | 四卡Ada主机 | 两卡A6000主机 |
|---|---:|---:|
| metadata边界控制 | 3项通过 | 3项通过 |
| flow OFF / ON完整B36 | 各36成功 | 各36成功 |
| 成功tiny路径合计 | 72 | 72 |
| 声明写出失败前缀 | 两次各9尝试 | 两次各9尝试 |
| 单次失败分母 | 8完成、1失败、27未到达 | 8完成、1失败、27未到达 |
| 重复B正式latent/RGB/RNG相等 | 每flow4对 | 每flow4对 |
| 容器终态 | exited / 0 / 无OOM | exited / 0 / 无OOM |

两个flow分别覆盖WC_T006/RA_T1/Native22与WC_T008/RA_T15/Native24，合计六个有限候选。使用完整合成A32终态、临时CPU账本及已有合成评分元数据构造测试冻结包，不执行A32模型、不重跑旧评分模型。测试同时覆盖部分A、活动评分、未结算、原件字节/源篡改、手改冻结决定、缺分数、跨host/UUID、部分/乱序B、错误角色/步数、脏计时与CPU冒充GPU等拒绝路径。

两个容器分别固定1CPU、4GiB、禁swap、core26、无网、root只读、无GPU，工作alarm600秒/退出60秒；A32原GPU进程使用cores24,25。本次既未触及其源，也未为测试占用其CPU核。实际独占/MPS/NVML/进程观测在合成A元数据中明确模拟，不能作为B36 GPU接受。

## 下一边界

本次未生成实际A32冻结文件。本库的CPU测试冻结文件全部位于独立测试目录，含CPU fixture标记，不能用于生产。A32真实终态、释放、中央实际结算及12对实际CPU评分接受后，才执行原一次冻结；然后将原六文件交给上述承接。B36完整报价/单独授权、全新宿主预算与硬件准入、最终GPU终态仍后置，`GPU_dispatch_ready=False`。本次不修改旧方法、mask、alpha、评分协议或历史科学记录。

后续更新：A32实际完整链与一次冻结已经接受，真实六份原件已通过同一承接validator，见 [A32_TO_B36_BOUND_HANDOFF.json](A32_TO_B36_BOUND_HANDOFF.json) 和 [745结果记录](../../../../research/745_CARA_A32_COMPLETE_FIT_SCORES_AND_FROZEN_BASELINES_20261029.md)。WC_T006/RA_T1的UNMATCHED保持，实际承接不是CPU夹具，但仍不授予B36 GPU启动。
