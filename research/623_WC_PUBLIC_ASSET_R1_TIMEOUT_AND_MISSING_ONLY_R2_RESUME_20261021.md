# 623 — 公开辅助模型R1超时，SigLIP缺失文件独立R2续传

## 原R1完整收件与接受边界

14:08计划收件延后到14:13实际执行，只捕获一次新原件。source e8d1d426、原PID389727/start934248913、worker/manifest及job文件SHA均一致；原进程和本人容器已退出。原result为`PUBLIC_FIXED_ASSET_PREPARATION_FAILED_RETAINED`、`TimeoutExpired`，wall5410.236570秒；原最长5400秒未改，额外为自身容器退出时间。第一条下载命令尚未正常返回，因此两命令全0没有成立，独立接受为false。

全部14文件仍逐项保留：13件完整Git-blob/SHA256通过，包含Qwen3Guard全部文件；唯一缺失为固定`google/siglip-so400m-patch14-384/model.safetensors`。缓存技术字节3,200,103,508/5,034,332,532，尚未验证的剩余部分1,834,229,024字节。技术字节不充完整文件接受，不将13/14称作两模型完整接受。原R1源码、job、失败result和partial保留，没有重启或延长原任务。

## 独立R2实际单次启动

人类原授权是完成四卡全部资源准备。新worker只续传注册缺失文件，不重跑整套已验资源：先完整核对现存文件，PASS直接复用；仅允许上述固定SigLIP权重缺失时调用官方`hf_hub_download`恢复原安全partial。若出现其他缺失或现存完整文件哈希损坏，停止并保留，不覆盖。全部下载后仍对原14分母独立完整重读。

本地4项资源控制均通过：13件复用/唯一缺失请求、14件全在/0请求、未注册缺失拒绝/0请求、损坏现存文件拒绝且不覆盖。这些是轻量实现控制，不是新机scope生产CPU或模型通过。

GitHub source **88ebc004b039eae003a93f390f30d79b11a99dc2** 已发布；从服务器已验79源码只转运71,648字节delta，在新独立项目完整SHA/HEAD接受后删除外盘临时包。旧c9/e8/79项目保持，没有重克隆base或转运凭据。

R2于**14:21:31.718**实际单次启动，原PID**397742/start934875508**，job `wc-fourcard-public-model-assets-resume-r2-20261021`。worker SHA `c003b45555a5a028a2c6f84d1dddfbbe0ab87f33071ca9e6009c219d8020f5af`，manifest SHA `296e27452fd71e1ac57ca21fc4bbb2d8689b063a4dd9177f48f8aff9b24f2ac7`。一次admission核对原句柄活、source/worker/manifest/job文件全部匹配，处于现存文件验证/下载阶段；当时尚无result，不提前接受。容器仍2CPU/16GiB/隐藏GPU/只读root，0CUDA、0模型加载、0GPU、0账本写。

## 两次真实检查与接续

| 检查 | not-before | 实际app安排 | automation |
|---|---|---|---|
| 技术半程 | 14:51:31.718 | **14:52** | `siglip` |
| 完整原件和全SHA验收 | 16:22:31.718 | **16:23** | `automation-2` |

以上按R2真实launch+1800/+7260秒；R2最长7200秒并留60秒退出余量。原R1上限未改。半程只技术，即使退出也不提前接受；终态保存原件后离线接受，额外核对`resume_summary`只请求注册缺失文件、13件复用（或14件全在/0请求），全部14独立原件/两命令0/退出均满足才称公开辅助文件接受。

原触发`automation-3`完成原R1失败收件后已删除，独立R2两次检查已实际读回。外盘96件生产模型中转PID87082的17:11/21:11保持，21:11的`sha`已补入R2三件套读取与资源接续；本次未代收或修改该任务。两卡只读4小时检查仍17:48，不在两卡派新GPU。

本人SSH master85709和63606入口仍给资源任务使用，不关闭；未碰两卡88068/33620或其他FRPC。模型不落Mac内盘，外盘中转只在服务器完整SHA后删除。本次仅删除已验源码delta临时副本，没有删除partial或未验模型。

四卡完整固定模型、LPIPS、全推理CPU、CUDA兼容、各scope实际生产CPU/整卡报价及共同权威v2交接仍待完成；公开两模型完成也不充GPU-ready。后续仍按[622清单](../plans/WC_FOUR_CARD_EXPERIMENT_QUEUE_20261021.md)的BANK24→完整1624→生成器推进，完整1624具体12批准、cap226/origin历史和所有旧科学范围不变。

## 原件与实现

- [R1原终态新回执](../reports/wc_four_card_public_model_assets_R1_terminal_recheck_20261021_1408.json)、[独立不接受](../reports/wc_four_card_public_model_assets_R1_independent_acceptance_20261021.json)、[超时/13件接受边界](../reports/wc_four_card_public_model_assets_R1_terminal_timeout_boundary_20261021.json)
- [R2 worker](../scripts/prepare_wc_four_card_model_assets_resume_r2.py)、[独立配方](../manifests/wc_four_card_public_model_resume_r2_20261021.json)、[4项本地控制](../reports/wc_four_card_public_resume_R2_local_controls_20261021.json)
- [GitHub delta与外盘包清理](../reports/wc_four_card_GitHub_public_model_resume_R2_source_transfer_20261021.json)
- [R2实际launch](../reports/wc_four_card_public_model_assets_resume_R2_launch_20261021.json)、[一次admission原件](../reports/wc_four_card_public_model_assets_resume_R2_admission_20261021.json)、[独立技术准入](../reports/wc_four_card_public_model_assets_resume_R2_independent_admission_20261021.json)
- [实际两次检查与其他任务读回](../reports/wc_four_card_public_model_assets_resume_R2_actual_schedules_20261021.json)

## 14:52半程实际14:53技术核对

实际2026-10-21T14:53:07.942109+08:00仅一次捕获原R2半程。原PID397742/start934875508仍活，source/worker/manifest/job文件SHA全部一致；现存13件已完整核对复用，网络仅请求注册SigLIP权重，技术字节4,217,222,228/5,034,332,532，无错误、无最终result。只接受技术健康，不读最终结果或完整模型接受；16:23原全件验收保持。半程siglip已完成删除，其他17:11/21:11资源检查、两卡4小时17:48只读检查均实际读回保持；0重派/模型加载/GPU/账本写。

[原半程回执](../reports/wc_four_card_public_model_assets_resume_R2_midpoint_20261021.json)与[独立技术边界/排程保持](../reports/wc_four_card_public_model_assets_resume_R2_midpoint_technical_boundary_20261021.json)。

## 16:23一次终态收件未返回，17:25恢复原句柄

原16:23公开R2终态收件只执行一次，collector在55秒内未返回JSON后 `TimeoutExpired`；没有原result、当前原PID/容器终态或14文件全哈希观察，因此不运行accept、不将未知认作资源失败或完成。已保存本次UNKNOWN原件与独立边界；本机85709 SSH master、63606 FRPC进程及原control socket存在，仅核对本地身份，0重启/第二次SSH/重派。原worker/source/manifest/cache保持。

`automation-2`已实际改约 **17:25** 一次恢复，采用独立本地收件器将单次传输/全件收件上限由55改180秒并保存超时或JSON解析UNKNOWN，验收条件不变；17:25为恢复检查时点，不是worker预计结束时间。新原件使用 `terminal_recovery_20261021_1725.json`，不覆盖16:23回执。`sha`的21:11接续已补本次未知及新文件；原96件17:11技术半程/21:11全SHA与两卡每4小时17:48只读检查保持，不代收其任务、不开新GPU。只有原result、进程/容器退出和全部14原件/复用范围满足后才接受公开两模型文件；完整Cosmos/新机scope CPU/GPU准入仍待。

[本次UNKNOWN原件](../reports/wc_four_card_public_model_assets_resume_R2_terminal_20261021.json)、[本地边界与实际排程读回](../reports/wc_four_card_public_model_assets_resume_R2_terminal_unknown_boundary_20261021.json)。

## 17:25恢复槽延后17:55实际收件，公开两模型完整接受

本槽只执行一次180秒上限的有界原句柄收件，实际技术观察为 **2026-10-21 17:55:23.834**。原PID397742/start934875508和本人容器均已退出，source88ebc004、worker/manifest/job文件SHA及原c9/新88项目身份全部匹配。原result记录 **15:17:25.447** 完成、wall **3353.677414秒**；下载命令3274.687323秒、全部文件核验78.986449秒，两命令均exit0。旧16:23回执为55秒内未收到JSON的收件未知，保留其原件；此次真实成功原件不能反推旧超时唯一原因，也没有重复派发或修改原worker。

原分母 **14文件/5,034,332,532字节** 全部完整：Qwen3Guard7件、SigLIP7件，每件独立重读的尺寸和Git-blob/SHA256均与固定revision锁定原件精确匹配。SigLIP权重3,511,950,624字节，SHA256 `ea2abad2b7f8a9c1aa5e49a244d5d57ffa71c56f720c94bc5d240ef4d6e1d94a`。保存原件后仅离线运行原accept入口，12项接受检查全过；再以保存的resume_summary和登记integrity离线核对15项：全部14唯一身份、完整字节/哈希、worker原件一致，13已验文件复用、唯一注册SigLIP请求且完成、无未登记文件请求、分区无重复缺失、原进程/容器退出及0CUDA/模型加载/GPU/账本写。原R1失败与UNKNOWN留存；原R1未再远端查询，其留存边界由历史原件与冻结R2写入范围证明，不冒充新增实时哈希。

接受仅限 **两公开辅助模型文件**。完整96件生产模型、LPIPS、完整推理CPU、实际新机兼容、BANK24/1624各自生产CPU/完整报价与唯一权威v2仍待；未新增科研CPU/GPU或视频质量结果。资源任务的这一步已完成，`automation-2`已删除，避免重复下载或哈希检查。本人master85709/63606入口继续供生产资源R2使用，不关闭。

最新直接人类“现在就开始修复”已由[625](625_WC_AUTHORIZED_MODEL_RELAY_IMMEDIATE_REPAIR_AND_MISSING_ONLY_R2_20261021.md)执行：生产模型以source7f79ceef/PID94749于17:42单次启动独立缺失续传R2，**10月22日00:43**半程`r2`、**07:43**全SHA`sha`保持；本次只为sha补公开两模型真实launch/capture/accepted及复用证明，不再使用前文旧R1 21:11安排。两卡每4小时只读、原BANK24→完整1624与具体12批准/预算历史不变。

- [原R2成功收件](../reports/wc_four_card_public_model_assets_resume_R2_terminal_recovery_20261021_1725.json)
- [离线独立接受](../reports/wc_four_card_public_model_assets_resume_R2_independent_acceptance_20261021.json)
- [全14身份/字节/复用与只请求缺失范围](../reports/wc_four_card_public_model_assets_resume_R2_full14_resume_scope_acceptance_20261021.json)
- [完成删除与生产R2排程保持读回](../reports/wc_four_card_public_model_assets_resume_R2_completed_handoff_and_schedules_20261021.json)
