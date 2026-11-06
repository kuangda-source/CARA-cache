# 五模型CPU验证链准备：完整批次、固定源部署与独立验收

2026-10-16。**原N10五个神经模型的CPU验证链已经补齐，15项批次/部署/验收控制通过。** 指定ViCLIP资源仍待13:17按预计时间接收；本轮未部署或执行真实模型，没有GPU任务或新质量分数。

## 完整范围与真实执行准备

CPU bundle固定DINO、AMT-S、RAFT-things、ViCLIP、MUSIQ-SPAQ五角色，逐一启动独立CPU进程；某个角色失败、结果损坏或缺失仍继续保留其余角色和完整五分母，不借成功子集声称环境全部通过。其目标是源/权重/运行接口验证，不是缩小原160视频/960指标位置的评价范围。

部署入口只在原指定资源已终态且独立完整大小/SHA相符后才工作。它核对固定216份VBench代码的SHA256/Git blob、真实BPE、四份原权重身份与指定ViCLIP；Git绑定本地worker/完整bundle/工具和原imaging代码，再在fresh stage复制原缓存DINO的12份源码，原缓存和生成stage不写。

重模型CPU启动前检查登记GPU任务；若主线GPU在运行则返回明确deferred，不创建stage或进程，不停止其他作业。实际CPU子进程显式空CUDA可见集、两线程/低优先级，使用原参数和合成输入；名字匹配已有`evaluate_wc_`资源检测，避免与N08 clean计时静默重叠。该边界观察不宣称整个时间区间独占。

## 终态与验收

实际部署后预计约5—15分钟，最早启动后15分钟一次收。collector保留原PID/start/source/注册、全payload SHA、全部五模型原件与原bundle；原任务仍在运行时只返回完成文件数以便重估，不循环监听。CPU终态后只离线从各模型原JSON/哈希重建五个结果，不能只信成功汇总。

验收核对真实checkpoint/state_dict载入、CPU/FP32/eval、原模型类/源SHA、实际输入输出形状、有限性、梯度禁用、无CUDA/网络，以及五模型原分母。ViCLIP视觉/文本768维、原8帧与32-token/49408词表接口，RAFT20次、AMT一次插值等均按504原入口。缺失/失败/被修改原件保持失败；模型CPU通过也不代替真实视频质量评价。

## 本轮控制实际覆盖

- 完整批次5项：全部五顺序、单角色失败/缺失/异常仍保留五次尝试、缩域拒绝、坏资源/源/权重状态拒绝、坏shape/精度/有限性/梯度拒绝。
- 原件独立验收5项：从分离原文件重建、成功汇总不能掩盖坏原件、缺失原角色保留五分母、live/缺bundle不算接受、坏源/过早查收/缩分母拒绝。
- 部署5项：临时目录真实复制源码与注册，Popen明确mock且只一次；登记GPU活动时不创建stage或进程；坏归档拒绝；旧stage不覆盖；未接收资源时在Git/SSH之前拒绝。

这些为合成元数据、临时目录与模拟进程控制，未加载Torch模型或权重。实际模型CPU stage及结果仍为0；不把15项控制当NN运行证据。原99数值采样实现、N07 CPU证明和最终方法/输入不变。

## 下一步与原权限

13:17仅接503的原下载source3c7767f/PID1113019；如完整资源接受，提交原件后可在fresh资源/登记GPU条件满足时运行本完整CPU验证链，若N07已获批准则优先主线，不让后台CPU抢正式计时。若下载失败，保留原result/part并定位具体资源问题，不替换模型或缩评分维度。

N07完整180卡15.055555556GPUh与同一累计cap113的具体询问仍待直接人类回复，未新增GPU/预算写或重复提问。主线N07→N08→N09/10，P/T1后排，F/B关闭，无训练、OMR或人评。

## 原件

- [15项本地控制回执](../reports/wc_paper_N10_full_five_model_CPU_chain_preparation_20261016.json)。
- [完整CPU bundle](../scripts/evaluate_wc_N10_models_cpu_bundle_r1.py)。
- [Git绑定CPU部署](../scripts/launch_wc_N10_models_cpu_r1.py)。
- [按ETA一次查收](../scripts/capture_wc_N10_models_cpu_r1.py)及[原件独立验收](../scripts/accept_wc_N10_models_cpu_r1.py)。
