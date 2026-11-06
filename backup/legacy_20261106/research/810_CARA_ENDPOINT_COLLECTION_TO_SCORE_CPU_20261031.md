# 810 — 端点采集至实际评分整链CPU接受

端点采集、完整视频工件检查、释放后评分派发和原句柄接受已在两卡完成一次整链CPU验证。两种flow各覆盖完整32条和去重25条，共114条实际微型采集路径、32条独立历史微型参考路径、40对实际Alex/PIQ评分，每对完整93帧；四种组合均接受完整24逻辑位置，并各保留12份旧夹具指标。原R4容器退出0、无OOM，工作473.780秒；9项本地边界检查和13项独立终态检查通过。没有新增GPU实验、读取原GPU部分科学结果或访问中央账本。

## 原终态与验证范围

源码`724f1c4479d2cc714576178ca15496aa2b714adf`，原stage为`/data20t/gaokuangda/worldcache_workspace/.sync/cara-S-endpoint-pipeline-CPU-a6000-r4-20261031`，注册SHA为`a61a1311c33982efbc4378b7ec8fc291dafe07ef7da6e7985c5c380c50873b21`。实际21:44:21开始，21:52:17退出；外层真实Docker限定CPU26、1核、4GiB、无额外swap、network none、只读根文件系统、无GPU设备，工作1200秒加退出余量60秒。启动回执成功，后续只捕获同一个原容器。

这次让真实采集产物贯穿检查和评分：固定上游采样器与36步路由使用声明的微型CPU模型，保存实际张量和93帧视频，再由释放后工件读者核对原文件、参数、源哈希、完整帧数、时间戳及九项RGB控制。每种flow的32条范围产生12个新评分对，25条范围产生8个去重新对；两者仍各有24个逻辑位置。评分实际调用固定Alex LPIPS和PIQ0.8.0，四个独立Linux评分进程均完成并退出。相同意图再次调用只恢复原结果，不生成新进程、不改变评分输出文件。

GPU生命周期、费用/释放包和内部Docker观察仍是明确标注的CPU夹具；临时账本只位于该CPU stage的测试目录。外层容器、微型采样、视频编码/解码、实际评分、子进程身份和退出检查是真实执行。历史指标数值沿用旧评分对象作为复用夹具，相关视频身份绑定到新生成的微型参考；没有重评原A32/B36视频，也没有加载实际Cosmos模型权重。40对合成评分不能作为新科学结果。

## 保留的失败与修复

R1、R2、R3均保留独立原stage和退出1终态，没有重启或覆盖。三处测试接合问题依次为：Native FIT参考应取A_ANCHOR；采样器必须独占创建原输出目录；固定上游写入接口接收CTHW float32而不是THWC uint8。最后一项依据与远端注册SHA相同的上游源码核对。修复仅作用于CPU夹具，补入历史16位置、目录独占及视频布局/量化回归检查。

独立接受器核对原源码/runtime、资源限制、四种组合完整分母、全93帧、九项RGB控制、旧12行保留、四个不同评分PID/start ticks及其退出、实际评分内核哈希与manifest绑定。拒绝运行中、少flow/少范围、少帧、少控制、旧行变化、评分仍活跃、错误内核和将CPU准备冒充整张GPU卡接受。

## 后续边界

已接受的是采集到评分的CPU连接。新端点GPU runner、guardian与一次派发的整卡接合，以及24位置汇总/图表仍待完成，`whole32_CPU_accepted=false`保持。实际预算mask继续等待原112路径/51查询完整接受和唯一冻结；之后需要所选策略受影响验证、完整最终报价及新卡/原中央交易授权。

原14GPUh卡、23:16半程、次日06:01终验和06:45:04硬截止保持，本轮没有重新观测其GPU状态。A32/B36/原S冻结、科学表行、cap226和旧16.5责任均不变。

[CPU接受](../reports/cara_s_endpoint_pipeline_CPU_accepted_r1_20261031.json) · [完整原终态](../reports/cara_s_endpoint_pipeline_CPU_capture_r8_20261031.json) · [22项本地及接受检查](../reports/cara_s_endpoint_pipeline_acceptance_checks_r1_20261031.json) · [保留失败](../reports/cara_s_endpoint_pipeline_setup_failures_r1_20261031.json) · [原句柄交接](../plans/cara_next_stage_20261028/mainline/r2/S_ENDPOINT_PIPELINE_CPU_HANDOFF_20261031.md)
