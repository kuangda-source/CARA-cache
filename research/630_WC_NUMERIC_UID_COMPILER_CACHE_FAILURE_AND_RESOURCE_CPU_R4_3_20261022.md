# 数字UID与编译缓存定位；剩余资源CPU R4.3

## R4.2原失败已完整保存

05:24沿原launch一次完整收件，随后仅离线accept明确不接受完整资源CPU。原source8925d168、worker／manifest／全部payload一致；supervisor／本人容器退出、资源锁释放；env元数据／11runtime／原resolver复用证明保持，NVRTC库和loader独立SHA与worker记录匹配。17项完整失败留存核对通过。

- [完整终态原件](../reports/wc_four_card_offline_resources_CPU_R4_2_terminal_20261022.json)
- [独立不接受](../reports/wc_four_card_offline_resources_CPU_R4_2_independent_acceptance_20261022.json)
- [完整失败审计](../reports/wc_four_card_offline_resources_CPU_R4_2_complete_failure_audit_20261022.json)

本次已越过Transformer Engine common原生库加载，进入pytorch/jit导入。新失败为PyTorch Inductor初始化默认缓存时调用`getpass.getuser()`，容器数字UID1000没有passwd条目、也未提供用户名变量，触发`KeyError: getpwuid(): uid not found: 1000`。原NVRTC错误不在本次栈中；这只说明该导入阶段取得进展，尚不接受完整入口或CUDA兼容。

[PyTorch v2.7.1缓存实现](https://raw.githubusercontent.com/pytorch/pytorch/v2.7.1/torch/_inductor/runtime/cache_dir_utils.py)优先使用TORCHINDUCTOR_CACHE_DIR，默认目录才查用户名；[Python 3.10 getuser约定](https://docs.python.org/3.10/library/getpass.html#getpass.getuser)优先读取LOGNAME／USER等变量。新修复沿原实现设置进程配置，不关闭编译、不伪造库加载成功。

## 独立R4.3只补进程身份与自身缓存

[新固定配方](../manifests/wc_four_card_offline_resources_cpu_r4_3_20261022.json)注册独立job `wc-fourcard-offline-resources-cpu-r4-3-20261022`。保持原数字UID／GID，只给容器进程设置USER／LOGNAME，并明确五个缓存路径：TORCHINDUCTOR_CACHE_DIR、TRITON_CACHE_DIR、TORCH_EXTENSIONS_DIR、CUDA_CACHE_PATH、XDG_CACHE_HOME，全在新job下。实际执行前核对真实getpass解析、目录所有权与写入探针，不改系统passwd／宿主机配置／env-r3／依赖／runtime。

继续复用原R4.1成功110解析／tokenizer命令的完整result／manifest／worker／probe／log SHA；另绑定最新R4.2失败原件与退出。只新执行原受限入口导入与未到达的预训练LPIPS CPU探针。原探针body与原算法实现不改，不设置关闭Torch编译或绕过Transformer Engine的变量。现有AlexNet／线性权重与NVRTC库必须原SHA复用，禁止下载。

2CPU16GiB、隐藏GPU、网络none、readonly root／workspace／Torch缓存，仅新job和自身缓存可写。Cosmos权重／CUDA初始化／真实评分／科研GPU／账本仍为0；LPIPS允许加载两个固定CPU权重并执行合成检查。

21项本地控制通过，新增复现无passwd数字UID错误、无需改passwd的真实getpass解析、五个缓存目录写入／所有权、缺失Inductor路径和目录越界拒绝。这些不是远端CPU通过。代码先GitHub发布后一次fresh预检、单次真实派发；规划8分钟，半程4分钟／最终10分钟，整体上限20分钟。实际launch与两个检查另记，当前尚未派发。

终态必须两新命令全0／两个精确marker与原发布probe源码、原resolver复用、最新失败原件不改、真实进程身份及五个自有缓存、NVRTC／两LPIPS独立完整SHA、env／runtime保持及原进程／容器／锁退出分别接受。资源CPU通过不等于实际CUDA／新机科研scope生产CPU／整卡报价或GPU-ready。

原双卡四小时只读06:16不动，本任务不查双卡或写v2；cap226／origin79.99637737158223／全部历史／54科研行与状态保持。原BANK24→既定CPU诊断→完整1624、四CAL gate与源闭包、完整1624具体12批准和新机CPU／重价／上游／唯一预算交接前置保持。F/B关闭，无训练／人评／付费VLM／OMR。

## R4.3实际启动与两个原时点

GitHub source `f6af9f383de79ddd9702b73b5a8db97d3d9c63bf`发布后，05:30:23.955120单次启动supervisor PID621186/start940328731；worker SHA `96368f6bd21732178e0ad1f2faab12c58051c10be6a85de90b59b69c6470e201`，manifest SHA `2e5520648babbc24a1fd7e4ec9d76bbc0044f2ad8b6d5399ffbdfaa63f104c45`，新job按上述R4.3名称。

一次admission确认原source／全payload／manifest、原进程与本人容器活、只读root／空GPU设备；实际进程getpass解析gaokuangda、numeric UID1000、五个缓存目录所有权／写入检查通过，未改passwd。旧R4.2失败原件与原成功resolver／LPIPS资源保持，正在入口导入，尚无新命令终态通过。fresh预检数据盘344,413,700,096字节／主存68,408,176,640字节只供本资源准入。

- [实际launch](../reports/wc_four_card_offline_resources_CPU_R4_3_launch_20261022.json)／[一次admission](../reports/wc_four_card_offline_resources_CPU_R4_3_admission_20261022.json)
- `r4-3-cpu`：05:35一次技术半程，最早unix1792618463.9551198／05:34:23.955120。
- `r4-3-cpu-2`：05:41一次完整收件，最早unix1792618823.9551198／05:40:23.955120；保存后仅离线accept。

两个原定义已读回；旧R4.2终态`r4-2-cpu-2`完成删除，两卡06:16定义保持。R4.3仍为资源CPU在途，完整CPU／CUDA兼容／科研scope生产CPU／报价／预算门分别接受，0科研GPU／账本写。

## 2026-10-22 05:38半程：R4.3两项CPU命令已退出0，05:41独立终态验收保持

[midpoint](../reports/wc_four_card_offline_resources_CPU_R4_3_midpoint_20261022.json)：05:35槽实际05:38:27.910528仅一次原R4.3技术收件，原PID/start/source、全payload与manifest一致；supervisor及本人容器已退出。health报告05:33:16.862结束、wall171.870秒，原受限入口导入与预训练LPIPS CPU两命令均0／精确marker通过，原110解析0证明、进程身份／五个自有缓存、env／runtime保持。半程只记录技术完成，未读取最终result／日志／终态独立哈希或accept；完整离线资源CPU仍待05:41一次原件验收，不充CUDA兼容／新机科研scope生产CPU／报价／GPU-ready。未新增下载／安装／Cosmos权重／CUDA初始化／真实评分／科研GPU／账本写。半程r4-3-cpu已完成删除；r4-3-cpu-2原05:41及两卡四小时06:16保持。原96／公开14、BANK24→完整1624／具体12批准／cap226历史及54科研行状态保持。

[Technical boundary](../reports/wc_four_card_offline_resources_CPU_R4_3_midpoint_technical_completion_boundary_20261022.json) / [Original final handoff](../reports/wc_four_card_offline_resources_CPU_R4_3_midpoint_completed_original_final_handoff_20261022.json). All 20 technical checks passed; independent full resource CPU acceptance remains pending.
