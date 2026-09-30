# L0续传修复、完整融合监督与任务接口门

2026-10-01；L0_PARTIAL_RANGE39_CPU_AND_INTERFACE_AUDIT_NOT_FULL_FUSION_OR_GPU_READY。

## 第二次HTTP流中断与恢复范围

L0 r2因第二次HTTP流中断exit1/583.253381秒终态；3PIDs2496080/2496081/2496082已退出/CPU锁释放、原source/协议核验和GPU账本不变，owned r2转发在完整审计后关闭。few-step保留555745280字节（530MiB），CFG4文件继续官方hash PASS。新16MiB range/retry/rollback/fullSHA获取程序和完整融合监督已实现，本地/Linux39同范围CPU通过；还未r3提交/完整5B融合。

[r2终态审计](../reports/l0_adapter_assets_r2_audit_20261001.json)/[终态观察](../reports/l0_adapter_assets_r2_live_observation.json)。r1到r2使用同官方release/cache，真实持续进度，不是观察超时重复任务；本次不是3600秒cap耗尽。接续不重复旧身份，不改变两适配器/原11base/GPU预算，也不以完整CFG替代联合配方。

[新range协议](../manifests/l0_adapter_range_acquisition_20261001.json)/[CPU下载工具](../scripts/download_l0_adapter_ranges.py)/[传输](../src/wcomr/ranged_download.py)保留同匿名官方HF/revision/hash/cache/3600秒。每请求16MiB、socket30秒、每chunk最多3次；要求精确HTTP206、Content-Range与Content-Length，再连续写入；失败请求回滚到该请求前，保留较早chunk。整文件完整官方Git-blob/LFS SHA通过后才将.incomplete发布为blob/snapshot。530MiB既有prefix仍不受信任，只有最终全文件digest能验收；不记录CDN签名URL/headers/tokens。全7文件终态检查，不跳过两JSON/CFG4文件。

原CPU acquisition parent新增明确--range-download门，只在新range protocol/官方endpoint/3600秒配合时用新工具；历史r2已终态审计才改代码，不修改仍在跑的source。r3提交前需source同步/GitHub hash确认/LinuxCPU、唯一新identity与owned loopback preflight（精确Range/prefix边界核验）；未知启动先查同handle，不重复启动。

## 有界完整模型融合监督

[监督](../scripts/supervise_l0_cpu_fusion.py)为真实两配方[原fusion runner](../scripts/run_l0_cpu_fusion.py)提供新job/model output身份、deployment锁中所有source SHA、独立l0-fusion flock及继承FD、timeout3590/parent3600、SIGTERM/KILL仅自身子进程组、退出码/日志/失败partial、Linux子进程ru_maxrss与前后source和GPU账本核验。CPU cap可以降低，不能超过冻结3600；CUDA_VISIBLE_DEVICES为空/离线，不触碰GPU账本。exit0只表示等待完整模型artifact审计，不是自动通过质量或GPU。

[监督+融合本地27](../reports/l0_fusion_supervised_local_cpu_20261001.json)/[Linux27](../reports/l0_fusion_supervised_linux_cpu_20261001.json)为先前22加5项真实子进程生命周期检查。之后[全范围本地39](../reports/l0_range_and_fusion_local_cpu_20261001.json)/[Linux39](../reports/l0_range_and_fusion_linux_cpu_20261001.json)同范围通过，不相加计数：range6、CPU获取supervisor4、完整性2、fusion-supervisor5、fusion8、header14。range用本机HTTP模拟忽略Range/短响应/整SHA错/已有blob/断点/Git-blob等；不是互联网权重完成或5B融合。实际Linux部署/大模型CPU仍需要fresh资源与全文件/hash gate。

## 固定源码与真实CPU scheduler检查

[新接口源码锁](../manifests/l0_interface_source_lock_20261001.json)：官方Wan commit42bf4cf的textimage2video.py与UniPC、官方LongLive commitfb16a879的utils/config.py与UniPC均按Gitblob取回。Wan与LongLive UniPC文件逐字节相同，SHA0dec8c7ed17f6f2049275c6848113314da6ccec1c8db5bdc89df43c05c6038d9；服务器历史Wan的这一个TI2V文件也与官方完全相同，不宣称整个旧runtime无改动。

[Linux实际CPU检查](../reports/l0_interface_linux_cpu_20261001.json)在现有CPU工具torch2.7.1+cu128/diffusers0.35.2加载两份真实scheduler，分别4/50steps、shift5、训练1000、动态shift false；完整timesteps/sigmas和对合成flow的每步结果逐字节一致/finite，最后sigma0。4步时间点首999/末624，50步首999/末92，全部数组在回执中；不得用未移位的1000/750/500/250替代。未加载DiT/textencoder/VAE，无GPU初始化或科学生成。

固定LongLive sample函数真实AST提取，在CPU spy model下测试：4step guidance1有4cond/0negative；50step guidance1有50/0；50step guidance5有50/50。这是控制分支代码证据，不是实机DiT前向次数/显存或质量。

## GPU前明确的管线门

固定官方WanTI2V.t2v的source380/382行以及i2v的580/584行均直接执行cond/uncond；guidance1不会跳过negative。因此不能只给stock generate.py guide1就称CFG-free。应在新版本的公共native管线中显式处理guidance1只条件分支，并验证native guide5参照/任务条件/固定noise不变，再实测调用次数；或经完整参照验收后选择共享pipeline。当前没有实施或宣称任何GPU管线parity。

两边UniPC相同只通过scheduler门；不是完整任务等价。LongLive通用wrapper.forward只支持完整序列T2V，拒绝clean_x/其他非空condition参数；不能直接套到图像条件或动作控制世界模型。默认CFG121帧/few-step125帧，必须明确共同规格，不能靠默认值配对。Wan5B的spatial stride16/temporal4/latent48、1280×704与24fps是源码默认；不把这些默认当显存准入。LongLive原--checkpoint期望adapter；CPU合并全权重应作为新model-dir，不能重复注入adapter。两边原noise构造位置不同，seed同名不证明相同噪声；未来配对需固定实际noise hash/共同入口，原生和适配臂保留同任务条件。

官方推荐Python3.12/torch2.9.1环境仍未验收，当前CPU版本通过不是推理兼容证明。L0剩余：r3全7文件/600×2 finite → bounded真实两臂825融合/全部序列化与未目标权重 → 隔离runtime/model/task接口与共同输入门。L1/GPU新4h尚待用户重大预算决定，不自动训练/付费/人评，主线质量—时间无一致收益的结论保持。
