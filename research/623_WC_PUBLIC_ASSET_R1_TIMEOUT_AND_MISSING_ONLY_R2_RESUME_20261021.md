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
