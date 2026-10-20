## 2026-10-21 四卡依赖故障已修复；完整推理仍缺固定Guardrail模型资产

[618实际修复边界](618_WC_FOUR_CARD_ENVIRONMENT_EXTENSION_RELAY_AND_ISOLATED_CPU_REPAIR_20261021.md)：官方四扩展wheel已安装并逐SHA核对，匹配cosmos-cuda、依赖声明和decord元数据修正完成；实际uv依赖检查、Cosmos CPU请求导入/精确版本与四帧合成CPU编码解码通过。29项组件范围独立核对全过，196份实际已装依赖metadata已保存。原R2验证脚本的VIDEO占位符错误保留为失败，由GitHub source e8f80c6c的只读R3实际补验解码；未重装原基础或修改旧stage/env。完整推理导入另在固定Cosmos-Guardrail1 revision d6d4bfa899a71454a700907664f3e88f503950cf的离线缓存缺失处停止，R1/R2/R3完整接受仍false；只接受已修好的依赖组件，不称完整环境/新scope生产CPU/GPU就绪。原env-r2、项目c9a2f95b、11关键runtime、37项decoder payload及原失败结果保持；修复和补验PID/自身容器均退出，0CUDA初始化/模型加载/GPU/账本写。下一步仍需固定模型资产、GPU兼容及新机scope生产CPU/报价/共同v2；原BANK24优先和两卡02:30资源检查、完整1624具体12批准及上游条件保持。已完成的四卡半程/终态自动化均删除，缺模型不重试安装。

## 2026-10-21 00:50完整环境技术半程：扩展安装超时，01:50完整收件保持

[617技术接续](617_WC_FOUR_CARD_TORCH_BASE_ACCEPTED_FULL_ENVIRONMENT_SINGLE_DISPATCH_20261021.md)：实际00:50:50.355仅一次捕获原完整环境任务，原worker SHA和health中的source/manifest与launch一致；原PID已退出，health报告00:39:32.226结束、wall1226.773秒、CPU_ENVIRONMENT_PARTIAL_FAILURES_RETAINED。13命令中11项exit0，CUDA扩展轮安装exit1且日志出现operation timed out，随后Cosmos CPU请求导入exit1/CUDA extra not installed。原生库、Torch和Cosmos基础安装命令为0，完整依赖及新机生产CPU/GPU仍未接受。本次只读技术health/有界错误，未读最终result或提前验收，未修源/重派；0GPU/模型加载/账本写。本次worldcache半程任务已完成删除；worldcache-3的01:50原完整收件和worldcache-bank24的02:30资源检查均读回确认保持。失败原件留存，待原终态完整收件后离线定位新独立修复版本，不重跑旧基础R2或改原stage。

# 四卡环境实际准备：存储已过，代码/CPU环境独立部署

## 10月21日00:15基础接受后，已启动完整环境

[617实际接续](617_WC_FOUR_CARD_TORCH_BASE_ACCEPTED_FULL_ENVIRONMENT_SINGLE_DISPATCH_20261021.md)：原R2全部15项独立检查通过，2358.943秒，Python3.10/Torch2.7.1+cu128实际CPU导入、原进程/容器退出及0GPU均已核对。基础未重跑。完整Cosmos CPU环境于00:19:05单次启动PID290861/start929820876，source c9a2f95b、manifest af9d8495；初次检查六源命令全0和11 runtime源一致，正在补数据盘原生库、无有界错误。已约00:50技术半程、01:50完整验收；不是完整环境/生产CPU/GPU就绪，模型与共同预算/原上游前置保持。

## 23:30资源变化：GPU1空闲，环境前置仍待

[616原件核对](616_WC_TWO_CARD_ROUTE_STILL_UNKNOWN_FOUR_CARD_GPU1_IDLE_20261020.md)：四卡GPU1实际23MiB、0%、无计算进程，其余三卡仍有任务；本项目GPU锁/共同v2和模型hub尚无，未占卡。原两卡入口仍认证前reset。原R2的00:15验收保持，本次不提前读取终态或加载模型；空闲只是硬件可用性，不替代新机环境/模型/兼容/实际CPU与完整准入。

## 23:16一次技术半程完成，R2仍正常安装

按23:15原安排，实际23:16:49.520仅一次捕获reports/wc_four_card_container_Torch_CPU_R2_midpoint_20261020.json。原PID256731/start929253857及worker SHA688b331e一致、进程存活，仍为python-and-pinned-torch阶段，result尚不存在，有界错误标签为空。仅完成技术半程核对，不提前运行终态collector或接受CPU环境；0GPU/权重/账本。原00:15完整查收与原BANK24的00:20资源接续均保留，本次半程自动化完成后删除，不循环查询或重派。

## 23:11源码完整包已实际传到四卡

reports/wc_four_card_GitHub_source_bundle_and_runtime_transfer_20261020.json：23:11:41.661完成58873323完整GitHub历史包和原runtime源码包上传，远端逐包SHA均与本机已验包一致；不含凭据或模型。最新原生库代码已经GitHub发布，后续小改动按增量包同步。此为源码转运接受，不是环境/生产CPU/GPU接受。原R2及23:15/00:15查收保持，原BANK24仍00:20。

## 23:04原生库缺口已实际定位，安装准备保留待验

reports/wc_four_card_CPU_container_system_library_probe_20261020.json核对原Python镜像：libstdc++可加载，libGL/glib/libgomp缺失。最新完整环境worker因此增加数据盘原生库步骤：官方签名APT包只下载并用dpkg-deb解到system-libs-r1，通过LD_LIBRARY_PATH/PATH加载；不安装宿主机包，不运行安装脚本，拒绝替换固定容器libc/loader，记录每个deb SHA并在新Python进程核验。此步骤尚未实际执行，不能说原生库已装好；原R2 Torch任务未改。

GitHub完整镜像已实际完成，已发布58873323的完整bundle为387902233字节、SHA6094d21d9df1ec7a830e40b9d5204a62800a55812190ddb0bec2c79fce18af48；runtime源码归档1306627字节、SHA950e227cc4a070fc92eec0bdff33e4956a805c7437efc20e98125d852c376bb9，11关键SHA保持。本机按需存储一次读取超时发生在任何上传前，下载并复制归档到本地.cache后SHA一致。当前仅源码转运在途，CPU/GPU未重派。后续小变更用带base先决条件的增量bundle，完整worker逐包验SHA再fetch/checkout准确GitHub版本，避免重复发送完整历史。

当前/data20t可用478,780,252,160字节（约445.9GiB），本人新工作区/data20t/gaokuangda/worldcache_workspace已完成64KiB写入/fsync/回读/删除验证。300GiB工作区规划加128GiB余量小于当前空间；原HF树逻辑大小51,651,996,220字节作模型存储保守依据，非已复制结果。数据盘cache/tmp/env/assets目录已建，系统环境没动，0GPU/模型加载/v2写。

四卡GitHub匿名私有仓库读取被拒绝，PyPI可达；官方HF元数据连接失败且未有HF凭据。既有Docker有权限，但缓存候选均不满足本次用户态要求：glibc2.27/2.31，一个ARM64候选不能在该x86机器运行，失败元数据保留。采用独立轻量官方Python3.10容器准备CPU环境，不改共享驱动/daemon；固定Cosmos要求与实际驱动/glibc差异已经明确，准备不等于可运行GPU。

新worker及固定recipe已实现并做本地语法/CLI与11关键runtime SHA核对；真实服务器环境尚待单次worker完成，不能称新scope生产CPU通过。完整执行与GitHub转运协议见plans/WC_FOUR_CARD_ENVIRONMENT_AND_GITHUB_SYNC_20261020.md。原BANK24/已批完整12卡/22:10资源时点保持。

## 容器已拉取，首轮Torch依赖错误保留并修复新R2

22:36:07原CPU prerequisite单次启动，22:38:19终态失败，131.499秒。官方Python3.10.19/bookworm镜像实际拉取成功；Torch阶段typing_extensions wheel名称元数据被旧pip拒绝，回退源码后CUDA单一索引缺flit_core。原失败worker/日志/回执保留；不是科研负结果，0GPU/模型加载/账本。R2改用独立envs/wc-cosmos-py310-cu128-r2、固定pip25.2、精确cu128二进制轮及PyPI依赖源；主环境安装同步修正相同依赖源边界。真实CPU导入尚未通过，不能称环境或生产CPU接受。失败证据见reports/wc_four_card_container_Torch_CPU_R1_technical_failure_capture_20261020.json及failure_independent_boundary。

原双卡22:10资源槽实际22:19:50一次SSH仍认证前失败，GPU/v2/原句柄未读到；下一最早10月21日00:19:50，原worldcache-bank24已重约00:20。四卡准备不替代原BANK24和完整1624具体12批准的上游/实际CPU前置。

## R2实际启动与两次查收

22:44:35.218按已发布dc8c57d0单次启动R2，PID256731/start929253857，worker SHA688b331e。22:45:07初次检查原进程、源码、镜像和独立数据盘env路径一致，phase=python-and-pinned-torch，无错误，result尚无。原失败R1保持，0GPU/模型/账本。R2实际半程最早23:14:35，worldcache已安排23:15；终态最早10月21日00:14:35，worldcache-2已安排00:15并明确接完整环境/源码转运；两项已回读，原BANK24仍00:20。

完整环境worker强制绑定R2实际成功result字节SHA和独立接受。基础Torch通过不替代Cosmos请求导入、扩展/版本freeze、模型资产、新scope真实生产CPU或GPU驱动兼容。GitHub直接镜像仍在下载，未称四卡已clone最新完整仓库。原runtime源码归档已完成并核对11关键SHA，不含凭据、模型或非生产媒体。
