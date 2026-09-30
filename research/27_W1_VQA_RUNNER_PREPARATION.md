# W1开发VQA runner：实现/CPU检查，未GPU评分

2026-10-01。当前继续WorldCache质量证据补全；scalar CAL8机制信号不等于闭环质量—时间收益。重放7接受1拒绝、MUSIQ3升4降保持，暂不加W2。

## 资源与执行身份

CPU r3/source202e21d因IncompleteRead退出1/1153.880144秒，三PIDs退出/CPU锁释放/hash与预算不变，保留3030384640字节（2890MiB），不是超时/主动取消。[终态审计](../reports/w1_judge_assets_r3_audit.json)/[supervisor](../reports/w1_judge_assets_r3_supervisor.json)/[downloader](../reports/w1_judge_assets_r3_download.json)。新唯一r4/source39993d1已live，Linux4 acquisition/hash通过，三PIDs本次核实，partial3280MiB；同镜像/固定revision/同官方完整hash/cache/cap3600CPU-only，旧失败保留。[启动](../reports/w1_judge_assets_r4_launch_20261001.json)/[观察](../reports/w1_judge_assets_r4_live_observation.json)。观察失败或旧RUNNING文件不得触发重复提交。完整权重仍未验收。

scripts/run_w1_vqa.py、supervise_f1 --w1-vqa、scripts/summarize_w1_vqa.py已实现；尚未部署GPU、未load权重/模型forward/评分。原[输入协议](../manifests/w1_development_vqa_protocol.json)最初状态字串保留为历史冻结标签，以本卡和后续回执区分实现/CPU/实机。另[运行时锁](../manifests/w1_vqa_runtime_protocol.json)绑定真实CPU检查的transformers4.57.1/qwen-vl-utils0.0.14/decord0.6.0/torch2.7.1+cu128，以及实际安装的model class/processor/vision utility哈希；模型官方10文件digest必须全部通过。

## 固定输入与运行边界

- 原8场景、42参考题、7接受候选39题，robot3题视频拒绝保留。不替换样本、插补或安全绕过。
- 每道原题单独固定single-question提示，标签/方法名/ground truth不入prompt；scene SHA256决定参考候选先后。requested2fps，精确10帧索引0/10/20/31/41/51/61/72/82/92，原93帧16fps/显式metadata/decord/patch16/禁止processor二次采样。
- 一次模型加载，离线BF16/SDPA、model.eval/inference_mode、seed0、greedy/max_new_tokens1024，保存raw token IDs/原始答案/parse状态/输入hash与shape/每题耗时。无重问、改提示或substring猜答案；解释或混合标签为invalid。
- 每题持久化partial coverage，未知技术异常/超时停止，不把部分结果写成完整。invalid继续全部原题并给未知上下界；这不是统计置信区间。所有已覆盖scene才能给原7可比scene等权差，原8拒绝分母仍保留。
- 原global GPU lock/UUID VRAM与compute apps准入、单GPU job、所有wall计费。独立模式最多900秒（timeout实际890预留kill/flush），从剩余0.387639303GPUh扣除，包含hash/加载/失败/评分/flush。尚未实测成本，不保证900秒完成。GPU总4h不扩。

## CPU证据与尚未完成

[本地25](../reports/w1_vqa_runner_local_cpu_20261001.json)/[Linux25](../reports/w1_vqa_runner_linux_cpu_20261001.json)相同范围不相加：实际fake-GPU子进程/预算/单模式/超时失败计账，以及原prompt/parser/unknown bounds/原分母、forward异常保留部分答案、终态metadata/raw/token/拒绝被改时拒绝汇总。

[全部真实输入CPU](../reports/w1_vqa_all_inputs_cpu_20261001.json)：15个真实接受视频原文件重新hash，全部10采样帧metadata和每video第一道原题processor输入通过；全部42题文件hash/count核验；CUDA未初始化。不是全题VLM或全帧物理判定。[实际runner拒绝部分资源](../reports/w1_vqa_partial_assets_refusal_cpu_20261001.json)确认15视频/42题/9小文件通过后，在缺完整权重时失败，未import torch/加载/forward；CPU无效UUID隔离，不是实机GPU准入。

下一须终态完整10文件官方Git/LFS hash，离线配置/运行时source匹配，再source commit/hash部署并fresh预算/锁/GPU准入，唯一outputs/w1-vqa-r1。完成后原始receipt/全部PIDs与GPU释放/monitor/source与产物hash/实际成本/原题重算汇总一并审计。

小[Qwen3-VL2B官方模型](https://huggingface.co/Qwen/Qwen3-VL-2B-Instruct)仅开发judge，10采样帧不等于完整动态物理真值；不能冒充论文235B标准Joint/整体质量验收、clean speed或独立确认。资源恢复与CPU通过不作方法正结果，不要求非必要人评/付费/训练。
