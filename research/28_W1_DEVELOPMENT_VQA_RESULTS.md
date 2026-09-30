> 2026-10-01后续状态：原8/126输入控制已完成并完整审计，[控制终态](30_W1_VQA_INPUT_CONTROLS_RESULTS.md)/[下一窗口成本方案](31_W1_NEXT_WINDOW_COST_AND_DECISION.md)。以下准备/拟运行描述为当时历史，不代表当前尚未运行；原冻结协议不倒改。

# W1开发VQA终态：原8/81答案完整，未显示代理收益

2026-10-01；source1f326b5；DEVELOPMENT_VQA_NO_GAIN_IN_PROXY。继续judge输入敏感性/重复稳定诊断，暂不加W2/生成或直接切换研究方向；没有整体质量/物理质量或clean速度正结果。

原[协议](../manifests/w1_development_vqa_protocol.json)与[运行时安装锁](../manifests/w1_vqa_runtime_protocol.json)保持：Qwen3-VL2B固定revision/官方10文件、BF16/SDPA/eval/inference/seed0/greedy，逐道原single-question提示，标签/方法名不入prompt。全部15输入93帧16fps源视频、精确10采样帧0..92/显式timestamp，全部原8/42参考39接受候选原题，机器人3题拒绝不插补。

| 场景 | WC正确/原题 | scalar正确/原题 | 场景差(pp) |
|---|---:|---:|---:|
| av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632 | 1/4 | 1/4 | +0.000000 |
| common_sense_6487f37f-ef57-49ca-afdc-d898922b5191 | 1/1 | 1/1 | +0.000000 |
| human_199 | 3/4 | 3/4 | +0.000000 |
| industry_084 | 2/3 | 2/3 | +0.000000 |
| misc_13398218_3840_2160_60fps | 6/9 | 4/9 | -22.222222 |
| physics_045 | 9/14 | 9/14 | +0.000000 |
| robot_054 | 3/3 | VIDEO_REJECTED | not imputed |
| av_51b45829-502e-4143-9c32-c026bd6ab191 | 1/4 | 1/4 | +0.000000 |

7可比scene等权mean delta **-0.031746031746031744（-3.174603pp）**；6平、misc1降。只有misc_Q1空间关系与misc_Q9时序YES→NO（原标签YES）；其余37可比题答案相同。misc6/9到4/9。参考all8 26/42，accepted7参考23/39/候选21/39是另一题权口径，不替代scene等权；问题/帧不能当独立样本。所有81回答strict整段YES/NO有效，0invalid，不使用substring或重问，raw与tokens保留并CPU重新decode核验一致。

原标签32YES/10NO，常YES基线32/42=0.761904762只是偏置诊断。生成视频不是gold，低于这个基线不等于judge无效，也不能当方法物理坏；未有judge有效性金标准/非劣界限/独立确认。本结果不支持代理质量收益，也不证明物理变差、动作失败或最终方法否定；小2B/10帧不是235B标准Joint/全视频动态物理真值。

## 技术、完整性与成本

[部署](../reports/w1_vqa_r1_deployment_20261001.json)/[启动](../reports/w1_vqa_r1_launch_20261001.json)：archive/hash一致、Linux25CPU，GPU1在24MiB/noapps时准入，只一次900秒cap任务。实际离线model load2.090181秒，无missing/unexpected/mismatch/error，模型BF16/SDPA/eval，输出全部原题完成；greedy模式忽略checkpoint的temperature/top_p/top_k参数warning属预期，未改变prompt或采样。

[终态审计](../reports/w1_vqa_r1_audit.json)：supervisor2485687/timeout2485695/runner2485697全退出，global锁可用/GPU1 24MiB/noapps；12monitor点无观察到其他compute、peak4972MiB；Torch peak allocated4642345472/reserved4840226816字节。15源视频、10完整模型文件、原question receipt/源码与安装runtime hash重新通过；原始81tokens decode与raw完全一致，summary按原题/raw/覆盖/metadata/token与拒绝重新计算。

监督60.96600103378296秒/0.016935000287162GPUh，累计**3.629295697609584/4GPUh**，余**0.370704302390416GPUh（1334.535秒）**，无在途。加载/hash/失败/评分/flush全部计费，不把runner59.727920秒代替supervisor墙钟。[raw runner](../reports/w1_vqa_r1_runner.json)/[重算summary](../reports/w1_vqa_r1_summary.json)/[supervisor](../reports/w1_vqa_r1_supervisor.json)/[账本](../reports/budget.json)。

## 继续还是转方向

继续最小的评价可信度诊断，不扩大scalar或W2，不据本次弱代理直接转向OMR。CAL8标量7/8机制改善仍在，但重放robot拒绝/MUSIQ3升4降/VQA6平1降尚未给出质量—时间收益。下一matched repeat/black/cyclic错配输入对照覆盖原8/42，不改原方法或已有提示；控制只检查重复稳定和是否响应内容变化，不提供物理准确金标准。固定数据revision根目录只含condition_image/vqa/metadata，此资源检查不等于所有外部ground-truth资源不存在。

拟下一单GPU最多300秒从剩余额度扣除，先协议冻结/实现/CPU/source同步/fresh预算锁与准入。控制输出尚未生成，不能先写judge通过；即使通过也不能替代标准评价、clean配对计时与独立确认。不引入非必要人评、付费、训练或自动扩额。超出原预算/关键方向选择时先具体方案再交用户。
