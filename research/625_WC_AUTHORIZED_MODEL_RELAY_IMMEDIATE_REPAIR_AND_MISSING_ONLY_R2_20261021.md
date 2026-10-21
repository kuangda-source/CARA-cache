# 625 — 固定模型中转立即修复与独立缺失续传R2

用户在技术半程发现失败后直接要求“现在就开始修复”，因此现在收齐原失败记录并准备新版本，不再等待原21:11时点才开始修复。原R1 worker、manifest、失败result、86件回执与外盘partial保持；不是重启原任务。

原R1在下载Reason1首个4,968,243,304字节分片时退出，最后完整断点385,875,968字节。固定源码说明三次有界分块尝试耗尽，但原catch未保留底层异常；不能从RuntimeError倒推出具体HTTP错误或服务器故障。对同一固定文件/断点的新一次1MiB诊断已返回206、精确Content-Range/长度且实际收到完整1MiB；当前权限和该请求链路可用，不能据此复原先前故障原因。

新独立R2使用4MiB分块、每块最多8次尝试、90秒socket timeout和2秒起始/30秒封顶指数退避，每次刷新同一冻结对象的请求nonce。严格校验状态、Range、长度和完整对象hash；失败块回滚到已提交断点，保留现存数据。错误只记录分类、HTTP状态、字节范围和时长，不写token、签名URL或原始异常文本。跨域重定向仍移除Authorization。

原96文件/21,358,871,258字节与原固定revision、原HF兼容路径/VAE内容别名不变；先在服务器重新核对完整现存件，只允许登记的10个缺失文件发起下载，不重下已验86件。外盘新job复制并核对原partial作续传种子，原失败job不覆盖。模型临时文件只落 `/Volumes/data`；凭据只在Mac受限文件内，模型每件远端完整hash通过后删除新中转副本。资源任务仍为0CUDA/模型加载/GPU/账本，不代表新机生产CPU或实验就绪。

11项本地实现控制通过：后缀续传、短读回滚、错误Range/长度拒绝、HTTP分类与脱敏、401有界停止、小完整文件200兼容、坏种子完整hash拒绝、超时保留断点、跨域凭据剥离、现存blob及别名核对。原R1完整失败已在用户立即修复授权下本地收件并离线不接受；旧collector的无条件public辅助模型flag另保留raw并离线纠正，不借其他scope标记接受。

本次先发布精确R2源码和配方，再单次实际启动；只有实际launch和一次准入后才记录PID、source和新的半程/ETA安排。8小时仍是初始资源规划，原24小时资源wall上限不变，均非GPU价格。原两卡四小时只读、公开SigLIP任务及BANK24→完整1624/具体12批准/共同预算历史保持。实际续传与排程以下方新回执为准。

- [11项本地控制](../reports/wc_four_card_model_relay_resume_R2_local_controls_20261021.json)
- [同一断点有界请求诊断](../reports/wc_four_card_authorized_relay_R2_bounded_range_diagnostic_20261021.json)
- [原失败即时收件](../reports/wc_four_card_authorized_external_models_R1_human_immediate_repair_failure_capture_20261021.json)
- [原失败独立不接受及scope纠正](../reports/wc_four_card_authorized_external_models_R1_human_immediate_repair_independent_nonacceptance_20261021.json)
- [独立R2配方](../manifests/wc_four_card_frozen_model_relay_resume_r2_20261021.json)
- [独立R2实现](../scripts/relay_wc_four_card_frozen_models_resume_r2.py)
