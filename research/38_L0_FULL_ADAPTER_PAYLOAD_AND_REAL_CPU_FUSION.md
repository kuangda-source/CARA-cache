# L0全部adapter资源与真实CPU融合

L0 range-r4/source7c0f2ec唯一实际续传成功，exit0/31.271029秒，最后12658832字节一次range完成/0retry。全部7文件官方digest与实际1200张量CPU有限性、300×2目标/rank/alpha及825基座header匹配通过；原3PIDs2502124/2502125/2502126退出/CPU锁释放/source与协议一致/账本不变，审计后仅owned临时转发关闭。真实融合尚未提交，实际模型/GPU parity仍未通过；新4GPUh仍待用户重要预算决定。

[唯一启动](../reports/l0_adapter_assets_r4_launch_20261001.json)/[完整终态核验](../reports/l0_adapter_assets_r4_audit_20261001.json)。r4首次传输预检EOF失败且没有job；新owned transport预检成功后才提交r4。完整few-step SHA验证包含之前保留prefix，未将局部下载当验收。

下一真实CPU融合采用已有固定协议：CFG1.0；few-step1.0后CFG0.5。新job/model目录，固定source/官方mergerSHA，8线程、3600秒cap、至少32GiB RAM/80GiB磁盘。每臂825tensor/300目标/525untargeted，全输入前后hash、有限性、独立矩阵算术与序列化重读核验，不能用exit0替代完整产物验收。无CUDA/GPU预算成本。

[公共T2V CPU接口](36_L0_NATIVE_CONDITIONAL_CPU_PREPARATION.md)保留guide1 BF16抵消与直接cond的数值差异；实际全pipeline/模型与任务仍待下一门。

## 真实CPU运行

真实Wan5B两臂CPU fusion-r1/sourcec69e492已唯一启动。supervisor2502473/timeout2502474/runner2502475实际/proc live，独立fusion锁持有、CUDA空/source固定与账本未变。准入时MemAvailable59360669696字节（55.3GiB）、磁盘720206147584字节（670.7GiB）；3600秒CPU cap，当前完整输入hash阶段/未创建模型目录，尚未完成merge或产物验收。

[唯一launch](../reports/l0_cpu_fusion_r1_launch_20261001.json)/[当前观察](../reports/l0_cpu_fusion_r1_live_observation.json)。固定.stage `.sync/l0-assets-range-cpu-r1-20261001`/deployment-real-fusion-r1.json不可在跑时更改；job `outputs/l0-cpu-fusion-r1`，model `l0-fused-models-r1`。观察失败先核同PIDs/输出，不重复launch。exit0后仍要全2×825/各3shard digest、serialized tensor/未目标/输入前后hash/finite与矩阵公式、PID退出/锁/source/账本终态核验。

最新实际进度：fusion-r1/sourcec69e492同3PIDs实际live，CFG-only一臂已全部825张量/3分片完成融合、独立公式、有限性、未目标字节不变与序列化重读验收；完整两臂及末尾原输入hash尚未完成。CPU锁持有/source一致/账本未变，维持3600秒cap，不重复启动。
