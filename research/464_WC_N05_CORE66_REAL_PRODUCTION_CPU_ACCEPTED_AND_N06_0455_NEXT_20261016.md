# N05真实生产CPU完整接受，原同26D验收后接续

更新：2026-10-16 03:56，北京时间。

**下一项主线已具备完整生产CPU证据。** N05有限强基线完整66路径的独立R2生产CPU四条命令全部通过、70.921407秒，源与原件已一次捕获并离线独立验收。原R1文件漏传失败在463保留；本轮修复不改变数值算法、对照范围或费用。

## 1. 原件与真实入口

|检查|真实结果|
|---|---|
|source|`15d77ac55de7f5715a76901c47e407663d41c9d3`|
|原CPU|1074441已终态，03:56一次查收，不再重查|
|独立stage|`.sync/wc-paper-n05-core66-production-cpu-r2-20261016`|
|完整payload|1671份全部SHA一致|
|完整CPU命令|3＋7＋4项控制、实际Cosmos入口，共四条exit0|
|实际请求|11配置×四CAL的44种真实InferenceArguments|
|完整科学范围|44正式＋22warm＝66路径、2220pairs/4440CFG、一次加载、零教师|
|实际scheduler|35/26/18 requested对应36/27/19更新；全部timesteps与sigmas等于原CPU展开|
|原生forward|真实`MinimalV1LVGDiT.forward`身份、文件与SHA绑定|
|范围拒绝|10类坏参数/缩分母/训练/新增强/费用门槛变更全部拒绝|
|执行边界|CUDA未初始化、无模型权重、零GPU提交/预算写/共享runtime写；原N06未动|

原件：

- `reports/wc_paper_N05_core66_production_CPU_R2_launch_20261016.json`
- `reports/wc_paper_N05_core66_production_CPU_R2_collection_20261016_0356.json.gz`
- `reports/wc_paper_N05_core66_production_CPU_R2_independent_acceptance_20261016.json`

Native生产forward文件SHA：`2d3ddcf94158c61223bc610f31ede475f7e4e27cc3b604ff3557b73d891e665f`。采样数值核心仍由461接受的完整216条CPU及40组旧默认完整36步桥接支撑，没有改写旧证据。

## 2. 当前唯一GPU接续门槛

原同26D R2仍固定**04:55一次验收**：source0795a00、supervisor1040857/runner1040918/post1040858、原36全分母与24正式、旧28等价、全部适用93帧评分、显存生命周期、费用与GPU0释放全部按原规则验收。没有提前查看其partial，也没有以CPU通过推定它成功。

若完整独立接受，直接执行下一已授权完整N05卡：

```text
.venv/bin/python scripts/launch_wc_paper_N05_core66_r2.py \
  --N06-acceptance reports/原N06新的独立接受.json \
  --CPU-launch reports/wc_paper_N05_core66_production_CPU_R2_launch_20261016.json \
  --output reports/新的N05完整GPU_launch.json
```

必须使用已接受的**R2**目录与新launch，不能用失败R1。启动器绑定原N06真实终态/原账单、新CPU/source、完整66范围；supervisor在逐UUID锁内核对fresh v2余额和设备，只预留完整9.5GPUh，并按实际占卡wall/3600一次结算。原cap104.971363333、origin与新增48窗口均不变。

完整forecast **8.568548038 GPUh**、计费上限 **9.5 GPUh**，符合严格<12自主执行。若准入时总余额不足，交付完整卡与具体缺口，不拆缩控制。原N06若有技术问题先保留并定位，不能绕过失败继续下一GPU。

## 3. 新GPU终态怎样验收

模型驻留、每次缓存和随机状态重置；文本编码/去噪/VAE计入主计时，加载/写盘另列。全部44正式与22完整预热分母保持；新批Native35作匹配参考，所有兼容正式视频评分93帧。旧420的20条默认输出只作数值控制，不拼接新秒数或质量均值。

GPU完成后自动CPU post检查全部原件和来源，保留拒绝/失败/未到达，单个坏容器不抹去其他原件。独立本地分析从93帧分数重算均值、逐场景基线耗时÷候选耗时、完整四场景均值及v2加法记账，不仅接受汇总。

将来使用`capture_wc_paper_N05_core66_r1.py --launch-ref 新GPU_launch --output 新捕获.json.gz`一次收原句柄，再用`analyze_wc_paper_N05_core66_r1.py`只离线分析。三项CPU合成控制已通过：完整66/44重建、拒绝保留而不填零/伪造四场景均值、伪造逐帧均值/账单或缩分母拒绝。见`reports/wc_paper_N05_independent_analysis_CPU_controls_20261016.json`；合成控制不是新视频结果。

长GPU按实际launch估时约7小时后第一次查收，若原GPU/post仍在运行，依据余量重新约一次并结束，不持续监听、不重派。

## 4. 论文主线与后续

接续为：**N06位置/读出归因 → N05公平强基线 → N07最终共同冻结测试 → N08最终重复clean测速**，N09部署费用/N10自动质量复用最终输出配套。N05这轮每格一次正式计时，不能提前替代N08的最终速度稳定性证据。

直接修正近邻Cosmos适配仍是显式缺口；当前完整11配置不称已完成全部N05对手。P/T1保持可选后排，F/B关闭，不引入新训练、人评或OMR。本轮0GPUh，没有新的端点质量或速度结论。


## 5. 接续时的一次准入身份检查

本地新增`capture_wc_paper_N05_admission_once_r1.py --launch-ref 新GPU_launch.json --output 新准入回执.json`。只读新N05的supervisor、原句柄/启动ticks、注册身份、UUID锁与v2加法余额，不读runner或科学partial，不等待循环、不重复派发。绑定已接受R2 stage；该本地collector不改变服务器15d77ac源。

`reports/wc_paper_N05_admission_once_CPU_controls_20261016.json`保留1个合法合成记录与8个拒绝控制：PID复用、child终态、错误设备、缺活动预留、错误整卡费用、锁未持有、错误post归属和账本重算不一致。0SSH/0GPU；它仅检验准入回执边界，不是新实验科学结果。原N06仍04:55按完整原件独立验收。
