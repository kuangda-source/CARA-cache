# E4c 后处理CPU验收与原作业接续（2026-10-11）

**这轮已经推进真实模型实验，并完成其只读后处理的受影响CPU验证。** 新reader真实重读既有完整两flow的88文件／776张量，324次直接比较和48点／24组来源年龄汇总通过；8个缺点、负时间、来源修改、teacher泄漏拒绝及3个FP64标量控制通过。没有重跑采样、native meta、额外GPU或人评。

原独立CPU目录`.sync/wc-e4c-readonly-reader-cpu-r1-20261011`，source40b0143；supervisor4077675/child4077676退出0且消失，实测23.610747秒。原378来源、旧receipt/result SHA、新六文件、完整结果和账本前后SHA不变，已独立捕获在`reports/wc_e4c_readonly_reader_cpu_r1_terminal_20261011_capture.json`与六份native gzip。该CPU结果是reader实现证据，不是新的P质量／寿命结果。

R2只读reader仅将CPU/GPU FP64归约branch-MSE比较统一为既有guided-MSE容差1e-12/1e-15；inverse字节与AST保持。原R1和原在途399源码、Tensor／文件hash／逐元素等价要求不变，所有科学质量判据保留。终态入口绑定这一独立CPU原件，等待原句柄消失、核对原source／原付款结算，随后验证完整scope、44文件／388张量／162直接比较／24点、四视频全部93原尺寸帧及时间戳。部分／失败／未开始和原第一错误均保留，不以subset通过整卡。

GPU现场Unix1791683040.602：原supervisor4075406和child4075494仍存活，指定卡唯一compute app4075494、17616MiB。AV28 OFF父路径36更新和mp4已保存；ON进入首个离线窗口，日志最后完成11更新，磁盘receipt会在整个父路径完成后保存，不能用其0计数断言0真实计算或窗口停止。尚无独立验收的age point或完整OFF/ON等价结果。只跟踪原作业，不修改、重投或启动第二GPU。

当前完整E4c4父／4事件／16五步suffix／24teacher，248pair／496CFG、forecast2.577578296GPUh，仍按直接完整≤8权限执行。前settled40.313761639725、cap77.895246589659／新增48余37.581484949934；在途used=cap是唯一作业保守预留，实际费用待全wall结算。E2完整76／9.8697与E3完整64／12.3775具体批准仍待，不重问、不拆卡或沿用旧授权。

后续科学分析先回答P后C实际误差是否随age1／2／4恶化，以及被原代理排除的动作是否值得小预算区分。全部24点、12对来源对照、时间／beta／alpha／sigma／真实D历史和原代理候选一起报告；P、D各在自身当前latent做teacher，不把跨臂后续状态叫同状态。只有两个已曝光场景/seed0，局部MSE不是终点质量、真实寿命或干净latency；结果不会凭单项阈值否定P或WorldCache方向。目标active，原GPU及CPU终态接续已具体准备。
