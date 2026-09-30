# L0完整CPU融合准备与CFG实际payload验收

2026-10-01；PARTIAL_L0_CFG_PAYLOAD_VERIFIED_TWO_RECIPE_FUSION_IMPLEMENTED_CPU_ONLY。

## 实际权重与获取终态

[r1终态审计](../reports/l0_adapter_assets_r1_audit_20261001.json)：exit1/1218.1815328598022秒，few-step HTTP流连接中断，不是timeout或人工取消。supervisor2493078/timeout2493079/downloader2493080全部真实/proc缺失，CPU lock free、在跑source/协议hash一致、GPU账本保持3.6512467238638138/4h。只有此任务拥有的临时SSH forward在终态审计后关闭，共享FRPC/系统代理未改。few-step .incomplete保留167772160字节（160MiB），不得将HTTP已读172041088当持久化字节。

CFG release195c8c100e145d5b18068d506f8f2b4498dcaaa4的全部4文件重新按官方LFS SHA256/Git-blob SHA1核验PASS。[独立真实payload CPU检查](../reports/l0_cfg_payload_audit_r1_observation_20261001.json)用固定官方merger的adapter_updates加载600个实际tensor：全finite、300 A-B pair、alpha/r=1、CPU；PIDs2495417/2495418已退出，CUDA未初始化，无GPU成本。此独立短CPU检查没有保存父进程exit code，不补写exit0；完成检查receipt与原proc缺失是验收证据。few-step两JSON也hash PASS，权重仍MISSING/partial，不能称两适配器完整READY。

下一唯一r2沿用同匿名官方endpoint/revision/全部hash/cache与3600秒CPU上限，复用完整CFG及160MiB few-step；仅在旧r1终态/CPU锁释放后提交新身份。不是因观察超时重复启动，不提高GPU额度。

## 两套完整模型CPU融合实现

[程序](../scripts/run_l0_cpu_fusion.py)/[实现](../src/wcomr/lora_cpu_fusion.py)/[冻结协议](../manifests/l0_cpu_fusion_protocol_20261001.json)准备对完整Wan5B执行两臂：CFG-only weight1.0；few-step1.0后CFG0.5。每目标所有delta一起交给固定官方merge，FP32累计、按base原dtype回写，alpha读取实际配置；分片仅减少内存与改变存储，顺序/算法不改。各新输出保存全部825个DiT tensor/原index/config，VAE、UMT5与tokenizer作原已核验资产的显式链接。每臂预计300目标/525未目标，实际数值是否改变另记录，不假定所有非零。

完整输入11base+7adapter文件先逐官方digest核验，真实header/index/普通LoRA/config family/所有key/shape/rank必须一致；拒绝部分权重、已有输出、写到base内部、wrong upstream。所有真实tensor有限值、未目标字节不变、独立逐目标公式（rtol1e-5/atol1e-6用于FP32 addmm舍入差异）、每个保存tensor重新读取/逐字节hash，以及全部原输入结束时再次hash。新模型只在独立路径，不覆盖底座。CUDA_VISIBLE_DEVICES必须为空，不初始化CUDA。Linux执行前至少32GiB MemAvailable/80GiB磁盘，8CPU threads；计划外部timeout3600秒，未启动实际大模型融合。

[本地22检查](../reports/l0_fusion_local_cpu_20261001.json)/[Linux22检查](../reports/l0_fusion_linux_cpu_20261001.json)：8项融合风险/两真实序列化小模型配方、14项header结构；同范围不相加。Linux r1打包漏已有header manifest导致1failed/21passed，r2新staging补齐后22passed，失败保留在receipt，不是科研失败。tiny fixture不是5B实际融合；CFG真实600tensor检查也不等于融合验收。

CPU工具本地torch2.7.1/safetensors0.7.0，Linux现有隔离CPU staging为torch2.7.1+cu128/safetensors0.6.2，实际版本在回执；本地尝试安装官方推荐0.8.0时当前Python3.9包索引无匹配，CPU0.7.0安装成功。project声明safetensors>=0.6.2,<0.9用于复现CPU工具，这是测试之后的打包依赖声明，非改变已验证算法或升级服务器共享环境。尚未建立LongLive推荐Python3.12/torch2.9.1隔离推理环境，不据CPU版本通过称GPU兼容。

## 接续与边界

先完成同资源新身份r2续传/两完整release全部SHA/600×2 finite，再部署固定融合source/协议至新CPU路径，在有界监督下执行真实两臂825权重融合并验收。随后隔离runtime/task/scheduler/条件分支接口检查；仍有模型加载、完整任务与GPU调用次数/显存门。所有代码与回执同步GitHub后才对外报告本步完成。

主线原VQA无一致收益、MUSIQ混合/robot拒绝/CAL8机制only不变。GPU预算新4h决定仍待用户，L1不自动加2h；不把CPU资源推进当质量—时间结果，不引入人评、付费或训练。

## 后续同日r2实际续传

L0 CPU r2/source965a502已实际启动且3PIDs2496080/2496081/2496082均/proc核实live，独立CPU锁持有、3600秒上限、source/协议hash一致、CUDA空/账本不变。复用CFG全部已验收4文件，few-step由160MiB续到188743680字节（180MiB），仍非完整/hash验收/融合。r1原连接失败及160MiB保留不改。

接续同一组新r2 handles，不重复提交；[launch](../reports/l0_adapter_assets_r2_launch_20261001.json)/[live](../reports/l0_adapter_assets_r2_live_observation.json)。
