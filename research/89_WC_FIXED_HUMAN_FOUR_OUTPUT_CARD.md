## 真实 D/D 独立通过，固定 D/S 原任务继续

[独立审计](../reports/wc_fixed_human_r1_dd_audit_20261004.json)/[CPU全帧控制](../reports/wc_fixed_human_r1_dd_metrics_20261004.json)：官方/固定D九门、五处各1216组件与最终pipeline全部一致；两mp4相同SHA、93帧完整解码、RGB MSE0/SSIM1/temporal0。九门D/D原件SHA fce12170d857d888d5f37f0417f831ca1b2062eb9a09eee9ad17732a968c4f3e单独gzip归档，不用终态覆盖。新增合同CPU15控制通过，真实artifact IO由独立审计另行验证，均无新GPU提交。

现场1791049930.3109043原三句柄匹配、3/4视频，固定D测量212.221秒，S最后一臂正在生成，尚无完整四输出或S质量结论。累计12h预付保持；下一仅跟踪原任务并做终态费用/释放和四输出/38共同动作/来源/视频及指标审计。以下为历史。

## 唯一提交与原句柄现场确认

[launch](../reports/wc_fixed_human_r1_launch_20261004.json)/[现场](../reports/wc_fixed_human_r1_start_observation_20261004.json)：实际部署与fresh准入后仅提交一次，supervisor2714273/timeout2714291/runner2714293现场存在且命令行匹配source4bd8951的冻结stage。1791049280.8881557第一官方D/D臂仍在生成，0/4视频，九门与新质量结果待验证。首次launch state null是监督器写状态前瞬间，不重提。

child1791048859.213845起算1770秒/kill5，全cost1800秒最大北京时间02:04:19.213845；1800秒预付0.5GPUh使累计含预留7.907626319933526/12h、39jobs，可用4.092373680066474h。原已结算7.407626319933526/38jobs保持历史，终态按实际替换预付。只跟踪原句柄，D/D不通过即止；不修改在跑payload、不自动下一卡/训练/人评。以下是卡选择和部署历史。

# 独立人物四输出卡：先验证固定 D 等价，再隔离稀疏近似

2026-10-04。基于[88 已完成 CPU 接线及成本](88_WC_FIXED_REFRESH_DIAGNOSTIC_CPU_AND_FOUR_OUTPUT_DRAFT.md)，依现有自主 goal 与累计12GPUh安排独立 `WC-FIXED-HUMAN-R1-20261004-A / wc-fixed-human-r1`，最多一次1800秒全cost/1770秒child/kill5。[选择依据与范围](../manifests/wc_fixed_human_r1_execution_20261004.json)。不是已消耗104点授权或轻量十输出身份的重提。

## 固定范围与问题

仅已曝光 human_199、seed0、原模型输入、35请求/36实际更新/72CFG、93帧768×432/16fps。原 shared eval、guardrail、decoder、probe2、sim0.1/cdf0.98/no-PV与层6/23/27 dense回退保持。源自原十输出官方重复 trace 的38次 deep 掩码与 model/condition/raw SHA绑定；是两臂共同离线解释性动作，不声称线上策略、Native full 或独立确认。

四输出全分母：官方 adaptive 与 fixed-dense 两次严格 D/D；通过九门、step13/21/33/35/36 原生组件和完整 pipeline 等价后，再 fixed-dense/fixed-sparse 两次轻量完整生成。每臂真实 prepare，D/D 与测量共用入口 RNG，无 prepared replay/前臂 cache复用。固定D三份 artifact 必须相同，四次 trace 全等于同一38-deep掩码；技术失败阻止或保留未完成分母，不缩减成三输出。

先回答相同刷新动作下的 S 是否仍产生人物差异，以及 fixed-S 与曝光 adaptive-S 的差异。单次轻量配对的时间仅作描述性成本；D/D诊断 wall 不参与速度比较。两个 fixed 测量臂都保留来源、掩码和真实核检查开销，移除 D/D 外挂诊断。语义/物理质量、强基线前沿和 CONF 仍未验证，RV 标签/训练后置。

## 实现与准入

[runner](../scripts/run_wc_fixed_output.py)在 Torch/CUDA 前校验新 scope、source/assets/package 与原完整 teacher 回执；实际样本metadata需匹配掩码的条件身份。[监督器](../scripts/supervise_wc_fixed_output.py)沿用共享 f1锁、唯一输出身份、fresh UUID/sm86/VRAM/compute/磁盘≥15GB、原12h账本无inflight/余额门；预付0.5GPUh，结束按实际包括导入/加载/失败/flush的全 wall 结算。只停止自己创建的进程组，不动他人作业。

[新范围 CPU19](../reports/wc_fixed_human_r1_scope_cpu_20261004.json)通过：四输出/单场景/固定动作身份、完整成本、累计12h/no-inflight/余额、实际原件与mask/model/condition/role和篡改拒绝。之前实际CPU37和本地mask28已通过；新的共享函数改动由当前四输出实际组合回执覆盖，失败原件保持。准备冻结[source配置](../configs/wc_fixed_human_r1.json)及43份payload，GitHub同步后验证实际原件CPU源绑定、官方prepare、native-meta mode/buffers、资产/import/package与single-human metadata；没有因为CPU成功就宣称真实模型 gate通过。

完整规划1635.704284秒（含20%余量与30秒结算）≤1800。当前7.407626319933526/12GPUh、38jobs、余4.592373680066474h；本卡已选择但尚未部署验证/GPU提交，无新 reservation。部署门通过后再做fresh资源/锁/账本准入，只提交此卡一次；无自动下一卡、参数扫描、训练或新增人评。

终态独立核验原四视频字节SHA、完整93帧解码、38/38实际动作/真实核/来源与真D隔离、source/实际费用/原句柄与锁/GPU释放。固定D与旧参考也需协议/资产绑定后才复用旧adaptive-S视频作开发比较，不能直接继承曝光指标为本次新结果。

## 实际部署门通过，待唯一现场提交

[实际部署回执](../reports/wc_fixed_human_r1_deployment_20261004.json)：冻结source `4bd8951aa660cafe6f95a0173714134c6e386e52`、deploy1 的43 payload与mid-config（44份）逐一绑定；当前实际组合CPU4/6原SHA和29依赖保持，之前固定CPU15/12的27依赖除可选dense factory外一致，该变更由当前实际组合原件覆盖。未把旧CPU追认为后改源码通过。新scope内部19项、官方prepare、native-meta1173默认mode→eval0与7 buffers、source/assets/import/package和human样本condition SHA均通过，CUDA未初始化、账本保持。磁盘约564GB，全局f1锁可获取；尚未GPU提交/预付。下一仅fresh准入后唯一提交，D/D不通过即止。
