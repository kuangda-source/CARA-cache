# P0半程接受，V1同状态标量采集入口准备

原P0第20步于02:14完成一次半程运维检查：7/14完成、0失败，四原进程活跃，原A6000为Exclusive_Process且唯一CUDA PID仍为3110391，当前63°C。原中央预约仍RESERVED_OR_RUNNING，cap226、旧16.5责任和本卡1.95GPUh硬限保持；未结算未结束的费用。见[半程接受](../reports/cara_v1_P0_point20_halfway_accepted_r1_20261102.json)。

依据计数和约50分钟墙钟，保留同一03:03终验；半程自动化p0-20-2已经删除，终验p0-20仍活跃，硬截止03:21:19不变。[调度r2](../reports/cara_v1_P0_point20_acceptance_schedule_r2_20261102.json)保存原计划、半程处理及终验定义。完整科学结果继续等待原终态、释放与唯一结算。

等待期间，已接出[真实缓存标量入口](../src/wcomr/cara_source_lifecycle_scalar_collection_r1.py)，复用原CPU-owned完整状态捕获/恢复操作，在预登记C状态执行一次shadow D、恢复父状态后执行C，随后由普通采样器推进一次UniPC。每条36更新父请求为36原pair加8 shadow pair，缓存、完整求解器、条件、生成器和RNG共同恢复。支持独立C与合法C35；四格实验原C/C、8..33限制保留在其原入口中。

这一新入口的完整Linux控制尚待执行，不能称为生产采集已接受。新独立CPU stage为 `cara-source-lifecycle-V1-scalar-CPU-a6000-r1-20261102`，通过[原通路客户端](../scripts/cara_source_lifecycle_scalar_linux_cpu_r1.py)一次prepare、之后仅capture。既有P0/M1/V1 CPU原件不会重放，当前P0 GPU stage/source保持原样，四卡不接触。

新CPU控制拟验证两个flow各8个父请求及8个独立普通控制，共32完整tiny请求和128条同状态标签；每条父请求必须与同输入普通请求最终latent/mock RGB逐值一致，source、完整状态及RNG恢复有原字节哈希记录。随后连接原固定估值/DP及11项标量组件控制，导出原UniPC当前输入尺度。这些均为tiny权重CPU控制，不读取真实视频或声明方法收益，也不授予P1 GPU权限。

CPU隔离沿用原单核26、无CUDA设备、内存/零swap边界、600秒主工作及60秒退出监督；实时CPU资源核验不通过则不启动。连接未知只恢复新CPU原stage，不重复prepare。完整P1的实际生产组合、范围/报价、一次审批与新中央账本权限仍待；完整top3、公平LPIPS搜索及强对照范围保持。
