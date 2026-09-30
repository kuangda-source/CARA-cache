# 开发judge输入控制：重复/全黑/错配，非物理有效性金标准

2026-10-01；控制协议在看过原方法开发VQA后、生成任何控制答案前冻结，非盲/独立确认。目的：核验同视频重复的答案稳定性，以及视频内容明显改变时judge是否响应。不修改原候选/提示/参数、不把控制答案当质量label accuracy或方法接受标准，不要求人评/付费/新权重。

[原VQA结果](28_W1_DEVELOPMENT_VQA_RESULTS.md)：原8/81严格有效，7可比6平1misc降、scene等权-3.174603pp、robot拒绝保留。所有原PIDs退出/锁/GPU释放，累计3.629295697609584/4GPUh、余0.370704302390416h（1334.535秒），无在途。

## 冻结范围与判定

[控制协议](../manifests/w1_vqa_controls_protocol.json)绑定原VQA完整raw receipt及原输入/安装runtime锁hash。原8官方WC reference视频/42原题，三条件各42题，共126个新答案：

- matched_repeat：同原WC视频、精确10采样帧/timestamps/geometry/seed/model/prompt/generation；sampled tensor SHA必须与原VQA相同，比较parse/raw与旧42参考答案。
- blank：decode原WC视频后torch.zeros_like原10帧tensor，再processor；全零真实性、shape/原metadata记录。仅数值输入反事实，不保存生成视频、不造ground-truth。
- cyclic_mismatch：按冻结原8序列循环后一位的视频配给当前原问题，无固定点，真实源video/tensor SHA核验；不择优选错配，不更换题/标签。

每scene三条件顺序由SHA256(scene)%3旋转；每道原题单独生成，原提示/标签不入prompt不变。模型/版本/安装source/checkpoint/greedy/BF16/SDPA/max_new_tokens1024与原VQA相同，每题raw tokens/原始答/四字段strict parser/inputhash/时间即时保存；无重问或prompt tuning。控制回执不包含correct/expected answer/quality accuracy字段。

完整覆盖后，只汇总对旧参考答案的parsed/raw改变数与YES/NO/invalid分布。冻结决策：有invalid→INCONCLUSIVE_PARSE_INVALID；matched parsed变动→REPEAT_INSTABILITY_IN_SCOPE；blank或cyclic任一个0变化→CONTENT_INSENSITIVITY_SUSPECT_IN_SCOPE；否则REPEAT_STABLE_AND_RESPONDS_TO_CONTENT_NOT_PHYSICAL_VALIDITY。即使对照通过也不证明物理推理正确、标准235B Joint、非劣或最终方法质量。未完成/partial不能给完整决策。

## CPU准备与未执行项

已实现scripts/run_w1_vqa_controls.py、src/wcomr/vqa_controls.py与supervise_f1 --w1-vqa-controls（单300秒cap）。[本地35](../reports/w1_vqa_controls_local_cpu_20261001.json)/[Linux35](../reports/w1_vqa_controls_linux_cpu_20261001.json)同范围不相加，覆盖原题顺序/拒绝变更、不稳定/无响应/invalid不能过度判断，以及实际fake-GPU互斥单任务/300秒cap/计账。

[24真实输入CPU](../reports/w1_vqa_controls_input_cpu_20261001.json)：原8文件重新hash，全部三条件/scene第一道原题的processor输入通过；matched tensor与旧原run一致，blank全零，cyclic无固定点且tensor改变，精确10采样帧/metadata/finite pixels，CUDA未初始化。未载模型权重/未生成126控制答案。

[资源root检查](../reports/w1_vqa_controls_resource_probe_20261001.json)：固定官方生成数据revision根目录仅condition_image/vqa/metadata，无这8对应gold视频目录；这不是所有外部gold资源不存在的结论。常YES基线只偏置诊断，生成WC视频不是gold。

下一需源码Git同步/hash部署与Linux最终CPU、旧GPU终态/锁/预算/freshGPU UUID+VRAM+compute apps核验，唯一outputs/w1-vqa-controls-r1，cap300秒（timeout290预留kill/flush），全hash/load/诊断/失败/评分/flush计入原4h余额。未实测控制成本，不保证300秒完成，不自动扩额。当前尚未部署或GPU执行；不能写控制通过。终态后核验PIDs/锁/GPU/monitor/source/资产原raw token decode/coverage/recomputed decision与实际ledger。
