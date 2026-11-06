# 指定 W3 提交已同步，实际服务器 CPU 验证通过

2026-10-04。用户直接允许将提交 `3f5c304b9d6ad3ba2da557bee96cdda0d7e04129` 中的 W3 运行、监督、审计、读取、评分代码及绑定配置/回执同步到既有服务器独立目录，**先仅 CPU 验证**。此前完整代码同步许可缺口已解决；本轮没有 GPU 准入、预付、提交或新生成视频。

## 范围与隔离

[直接授权记录](../manifests/wc_rv0_cpu_sync_authorization_20261004.json)、[R2 部署原件](../reports/wc_rv0_authorized_deployment_cpu_r2_20261004.json)、[独立回读审计](../reports/wc_rv0_authorized_deployment_cpu_audit_r2_20261004.json)。服务器新目录为：

`/home/gaokuangda/data/gkd/worldcache_omr/.sync/wc-rv0-causal-3f5c304b-cpu-r2`

62 份冻结 payload 全部与批准提交/草案 SHA 一致。`profile-config.json` 是该提交 `configs/wc_s0_profile.json` 的逐字节别名；另同步必要的草案别名、既有 CPU 原件、执行合同、两既有视频身份及本次授权记录。共 69 份清单文件，传输清单单独保存。新增 [CPU 验证入口](../scripts/check_wc_rv0_deployed_cpu.py) 只用于本次主机验证，不属于原批准提交的生成算法；其源码 SHA 单独记录。没有修改冻结的 40 份因果核心或 9 份官方源码，也没有重复原 274 秒完整核心回归。

所有新文件和日志留在独立目录。CPU 专用 `project-view` 映射现有配置、资源、预算及新绑定报告，既有项目根目录报告未写入。进程使用空 `CUDA_VISIBLE_DEVICES`、离线 Hugging Face、禁止字节码写入；评分进程禁止 CUDA lazy init 和权重下载，LPIPS 使用既有隔离包及本地预训练权重。生成器权重只做资产校验，没有加载或前向。

## 首次失败与修复

[R1 失败原件](../reports/wc_rv0_authorized_deployment_cpu_r1_20261004.json) 保留，CPU 子进程 0.732 秒停止于资产检查：独立视图未映射历史 `protocol.py`，并同样缺少 `guardrail_observation.py`。失败发生在实际生成器导入之前，不是 C/D 或方法负结果。

R2 在新的独立目录中补齐这两份**服务器既有文件**的只读视图映射，并逐个核对原 profile 配置中的固定 SHA。62 份 W3 payload 和 CPU 验证入口源码均未变；没有覆盖 R1、删除检查或修改共享代码。

## 实际 CPU 结果

- 新运行入口的 `--cpu-import-check` 通过完整阶段/输入/模式/实际 checkpoint 与 guardrail 资产校验；实际冻结 `Video2WorldCondition` 导入来源、类 AST、恢复及冻结行为通过，新因果核心从该独立目录导入。生成器无权重加载/前向，CUDA 未初始化。原有 CPU 专用 FlashAttention 可用性和 unused current-device 默认参数适配均仅在退出的导入子进程内使用并恢复，没有 GPU 路径适配。
- 运行、监督、终态审计、LPIPS 评分四个 CLI 的帮助入口通过；冻结 Python 文件语法通过；未选草案拒绝 GPU 执行。
- 实际主机执行合同通过 **35 项拒绝控制**，包括完整 8 父/24 后缀/18 输出的两组 mock 评分计划、错误源/预算归属/缺视频/错误帧与 PTS。预算预付与结算仅使用内存中的模拟字典，没有写权威账本。该合同仍不是实际 C/D 视频验收。
- 既有 LPIPS 隔离资源哈希审计通过。新服务器 reader 与预训练 CPU LPIPS 完整读取两份 112 恢复卡的既有 WC 视频，各 **93 帧、432×768、16fps**，保留全部源 PTS/timebase，没有 resize/crop/subsample。每份视频与自身配对的 93 个 LPIPS 距离全部为 **0**，平均值为 0；两份分别耗时 16.862、17.005 秒。这是读取/归一化/度量接口的自距控制，既不是匹配 Native 的质量分数，也不是新的 C/D 收益。
- R2 CPU 执行总墙钟 **79.753 秒**；验证入口自身 79.037 秒。生成器推理、端到端加速和质量结论均不由这两个时间产生。

独立审计重新从服务器读取全部 69 文件、3 份清单/CPU/部署回执及 4 份保护文件 SHA，核对返回原件 canonical SHA、完整帧分母、自距、拒绝控制和未选配置。两视频、权威预算及预算授权的前后 SHA 相同；新 GPU 提交、真实 C/D 视频和正式 RV 标签均为 0。

## 当前结论与下一边界

本次请求的**独立同步和实际 CPU 验证已完成**。累计账本仍为 **11.022315686839217/13 GPUh、45 jobs、无 inflight**；剩余 7119.663527 秒。原 104 点及 restore 单次身份不重提。107 稀疏净收益未成立的科学判断保持。

[原项目路径绑定检查](../reports/wc_rv0_cpu_view_production_root_bindings_20261004.json) 发现，当前原项目根目录还没有两份新准备审计报告；本轮使用的是独立 CPU 视图。这个视图不作为 GPU 监督器的账本/锁工作目录。后续正式执行需要在真实项目路径接好冻结报告绑定、独立执行身份与原全局锁/权威账本，并重新检查实际部署和现场 GPU 资源/完整预算。用户本轮明确仅 CPU，未进行这些 GPU 操作。

完整研究目标仍包含真实同状态 C/D 干预、最终视频有符号收益和同预算闭环验证。本轮自距及 mock 合同不提供它们；Head、训练、CONF、语义物理质量与新方法端到端优势仍未验证。
