# N09真实生产CPU通过；外部GPU占用使完整40卡暂未准入

2026-10-18。**完整1787源码、十命令及真实Cosmos生产CPU已接受。GPU资源检查在任何生成子进程启动或预算预留前拒绝了本次派发，因此本轮没有新视频、组件测量或GPU费用。** 这是资源等待，不是方法结果，也不是CPU验证失效。

## CPU成果与修复

原R1实际服务器九组74控制通过，真实入口遇到跨平台派生标准差／差异列表核对问题，原失败完整保留（[566](566_WC_N09_CPU_R1_PLATFORM_METADATA_FAILURE_AND_SCOPED_REPAIR_20261018.md)）。修复仅在N09下游沿用既有单ULP标准差桥接并重建诊断列表；原N08严格验收器和桥接、算法及原始数据不改。

修复R2 source `8c353ba107060bd0d315d726e0d40d56c5325d39`，stage `.sync/wc-paper-n09-production-cpu-r2-20261018`。CPU1629454/start554993366原进程已结束，全部1787文件SHA、194 overlay和10条命令通过；实际CPU耗时 **198.8012秒**，无CUDA／模型权重加载／GPU／账本写。

- [实际CPU查收](../reports/wc_paper_N09_actual40_production_CPU_R2_collection_20261018_0042.json.gz)
- [独立CPU接受](../reports/wc_paper_N09_actual40_production_CPU_R2_independent_acceptance_20261018.json)
- [完整40的既有小于12GPUh权限绑定](../manifests/wc_paper_N09_actual40_under12_GPU_authorization_20261018.json)

完整范围及费用不变：两个旧CAL×五冻结角色；10完整预热＋30正式／40路径、1440pairs／2880CFG、一次加载，20条正式profile，原audit／profile audit／profile lean三模式对照；预计 **4.245833333 GPUh**、计费上限 **5 GPUh**。GPU实际费用、组件和显存结果仍空；N08三轮重复测速保持独立。

## 实际未准入状态

原派发于00:45:35.096505返回supervisor1636878/start555043861、post1636879/start555043874，launch_id `c9401be4-f5b8-4dce-89d8-2fed621a6b0b`。这只是派发回执，未当作GPU准入成功。

[一次原句柄准入查收](../reports/wc_paper_N09_actual40_original_admission_collection_20261018.json.gz)随后确认：原两个进程均已消失；supervisor明确记录 `N09_FULL40_ADMISSION_FAILED_NO_GPU_CHILD`、`GPU_child_started=false`。原N09输出supervisor文件不存在，v2中没有N09 job或预留，自身UUID锁释放。独立[无子进程／无费用接受](../reports/wc_paper_N09_actual40_no_GPU_child_admission_independent_20261018.json)保留该状态，不把0条生成改写成40条实验失败或成功。

GPU0当时约48063MiB，GPU1约47696MiB，分别有其他账号的1615193／1615194进程。只读[占用来源观察](../reports/wc_paper_N09_other_GPU_owners_readonly_observation_20261018.json)核对两者仍活跃、同一父进程、00:16:35启动；无目录访问权限的部分照实记录。没有停止、重启、改优先级或释放这些进程，也没有推断完成时间。瞬时GPU利用率为0不表示显存可用。

原本安排的02:56半程／05:31终态两个自动化，因本次没有GPU任务而均已删除；[取消回执](../reports/wc_paper_N09_actual40_checks_cancelled_after_no_admission_20261018.json)保留原计划与0次执行，不伪造已做半程。未来真正准入后须从新启动时间安排，不能沿用这次过期时点。原stage／authority／派发fence不清除，不能直接重复调用原派发。

## 当前费用与下一步

这次新GPU费用 **0**；fresh v2显示实结 **110.869061155 / 226 GPUh**，预留0，可用 **115.130938845 GPUh**，origin79.996377372和全部历史账保持。卡小于12的授权、完整对照和资源准入门槛均未放宽。

1. 等空闲资源后恢复完整N09；使用新独立派发身份和来源／CPU绑定，fresh UUID／显存／进程／v2余额准入，不清除旧失败或仅凭GPU利用率重试。
2. 当前可以继续本地CPU准备，并接续N10完整五模型的固定资源与CPU验证；N09实际GPU测量开始前应结束重CPU／模型评分，不相互干扰。资源准备或CPU通过不当质量分数。
3. 下一轮方法已登记[连续修正区间完整24设计](../plans/WC_DROP1_CORRECTION_WINDOW_FULL24_20261018.md)：同一第21步删除D，比较25D-A1与25D-A3，保留26D-C和25D-C。仅静态计划通过，生产执行器、88数值CPU、真实生产及完整报价尚待；不将计划当作新结果。

原N12四场景同25D保真作用及单AV28局部MSE改善保持；F/B关闭、P和历史网络后置，无训练、人评或OMR。当前没有本项目正在执行的GPU实验，但服务器GPU正由其他账号占用。已向用户询问可能的释放时间，CPU工作不依赖答复。
