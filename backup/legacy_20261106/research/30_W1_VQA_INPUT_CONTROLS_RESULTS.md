# W1开发judge输入控制终态：重复稳定，明显内容变化会改变答案

2026-10-01；source72c9e24；REPEAT_STABLE_AND_RESPONDS_TO_CONTENT_NOT_PHYSICAL_VALIDITY。控制协议在原方法proxy后、任何控制答案前冻结，非盲；全部原8/42题×3条件完成，126strict有效/0invalid，不补质量标签，不改原方法或提示。

| 输入条件 | 有效/原题 | parsed改变/42 | raw改变/42 | YES / NO |
|---|---:|---:|---:|---:|
| matched_repeat | 42/42 | 0 | 0 | 16 / 26 |
| blank | 42/42 | 14 | 14 | 2 / 40 |
| cyclic_mismatch | 42/42 | 14 | 14 | 4 / 38 |

matched-repeat的42个答案与旧WC答案完全一致；blank与cyclic各14/42改变。这个冻结判定只说明本次重复稳定、部分题响应视频内容。它不验证物理推理正确性、235B标准Joint、视频质量或方法接受，也不能把反事实控制算成label accuracy。

| 场景 | repeat改变 | blank改变 | cyclic改变 | 原题数 |
|---|---:|---:|---:|---:|
| av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632 | 0 | 0 | 0 | 4 |
| common_sense_6487f37f-ef57-49ca-afdc-d898922b5191 | 0 | 1 | 0 | 1 |
| human_199 | 0 | 2 | 2 | 4 |
| industry_084 | 0 | 2 | 2 | 3 |
| misc_13398218_3840_2160_60fps | 0 | 4 | 4 | 9 |
| physics_045 | 0 | 1 | 2 | 14 |
| robot_054 | 0 | 3 | 3 | 3 |
| av_51b45829-502e-4143-9c32-c026bd6ab191 | 0 | 1 | 1 | 4 |

第一个AV三条件都是4个NO；common的cyclic没有变化；physics的14题中blank只变1题、cyclic只变2题。不能把总体有响应写成所有场景或细粒度物理判断都有效。原方法VQA6平1misc降（scene等权−3.174603pp）、MUSIQ3升4降/robot拒绝的事实不因控制通过而变成正结果。重复通过支持原两题差异在该重复设置下稳定，仍未确定它们的物理真伪。

## 完整审计与实际成本

[终态审计](../reports/w1_vqa_controls_r1_audit.json)：supervisor2488580/timeout2488585/runner2488587全退出，exit0/无stop reason/global锁可用；GPU1释放24MiB/noapps，16监控点无观察到foreign compute，peak4972MiB。离线BF16/SDPA一次模型load2.054605秒、无missing/unexpected/mismatch/error。原8视频和模型10文件逐个重hash，安装runtime/source锁一致；全部24组采样张量/metadata/shape/来源重算，blank全零/cyclic无固定点/matched旧tensor一致；126tokens CPU decode与raw全部一致，CUDA未初始化。

[本地独立重算](../reports/w1_vqa_controls_r1_local_recompute.json)再次按原8题文件hash/旧baseline/全部raw重建summary，与远端审计/runner完全一致。

本轮supervisor计费79.023694515228秒/0.021951026254230GPUh，不以runner77.692182秒替代；累计**3.6512467238638138/4GPUh**，余**0.3487532761361862GPUh（1255.511794秒，约20.93分钟）**，无在途。

证据：[部署](../reports/w1_vqa_controls_r1_deployment_20261001.json)、[启动](../reports/w1_vqa_controls_r1_launch_20261001.json)、[raw runner](../reports/w1_vqa_controls_r1_runner.json)、[supervisor](../reports/w1_vqa_controls_r1_supervisor.json)、[重算summary](../reports/w1_vqa_controls_r1_summary.json)、[账本](../reports/budget.json)。

## 继续还是转方向

暂停增加scalar/W2复杂度；保留CAL8机制信号和当前代理无收益边界，不据小judge切换方向或作普遍否定。输入对照问题已回答，不继续重复评分或调prompt。下一关键缺口为可部署成本与更强质量证据；当前完整8场景新WC/scalar计时批次不能依据原余额稳妥提交。已形成[下一窗口成本方案](31_W1_NEXT_WINDOW_COST_AND_DECISION.md)，先关键预算/是否值得继续的决策，不要求人评或付费。
