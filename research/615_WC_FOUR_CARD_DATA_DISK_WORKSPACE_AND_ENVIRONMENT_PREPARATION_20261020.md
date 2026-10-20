# 四卡环境实际准备：存储已过，代码/CPU环境独立部署

当前/data20t可用478,780,252,160字节（约445.9GiB），本人新工作区/data20t/gaokuangda/worldcache_workspace已完成64KiB写入/fsync/回读/删除验证。300GiB工作区规划加128GiB余量小于当前空间；原HF树逻辑大小51,651,996,220字节作模型存储保守依据，非已复制结果。数据盘cache/tmp/env/assets目录已建，系统环境没动，0GPU/模型加载/v2写。

四卡GitHub匿名私有仓库读取被拒绝，PyPI可达；官方HF元数据连接失败且未有HF凭据。既有Docker有权限，但缓存候选均不满足本次用户态要求：glibc2.27/2.31，一个ARM64候选不能在该x86机器运行，失败元数据保留。采用独立轻量官方Python3.10容器准备CPU环境，不改共享驱动/daemon；固定Cosmos要求与实际驱动/glibc差异已经明确，准备不等于可运行GPU。

新worker及固定recipe已实现并做本地语法/CLI与11关键runtime SHA核对；真实服务器环境尚待单次worker完成，不能称新scope生产CPU通过。完整执行与GitHub转运协议见plans/WC_FOUR_CARD_ENVIRONMENT_AND_GITHUB_SYNC_20261020.md。原BANK24/已批完整12卡/22:10资源时点保持。

## 容器已拉取，首轮Torch依赖错误保留并修复新R2

22:36:07原CPU prerequisite单次启动，22:38:19终态失败，131.499秒。官方Python3.10.19/bookworm镜像实际拉取成功；Torch阶段typing_extensions wheel名称元数据被旧pip拒绝，回退源码后CUDA单一索引缺flit_core。原失败worker/日志/回执保留；不是科研负结果，0GPU/模型加载/账本。R2改用独立envs/wc-cosmos-py310-cu128-r2、固定pip25.2、精确cu128二进制轮及PyPI依赖源；主环境安装同步修正相同依赖源边界。真实CPU导入尚未通过，不能称环境或生产CPU接受。失败证据见reports/wc_four_card_container_Torch_CPU_R1_technical_failure_capture_20261020.json及failure_independent_boundary。

原双卡22:10资源槽实际22:19:50一次SSH仍认证前失败，GPU/v2/原句柄未读到；下一最早10月21日00:19:50，原worldcache-bank24已重约00:20。四卡准备不替代原BANK24和完整1624具体12批准的上游/实际CPU前置。

## R2实际启动与两次查收

22:44:35.218按已发布dc8c57d0单次启动R2，PID256731/start929253857，worker SHA688b331e。22:45:07初次检查原进程、源码、镜像和独立数据盘env路径一致，phase=python-and-pinned-torch，无错误，result尚无。原失败R1保持，0GPU/模型/账本。R2实际半程最早23:14:35，worldcache已安排23:15；终态最早10月21日00:14:35，worldcache-2已安排00:15并明确接完整环境/源码转运；两项已回读，原BANK24仍00:20。

完整环境worker强制绑定R2实际成功result字节SHA和独立接受。基础Torch通过不替代Cosmos请求导入、扩展/版本freeze、模型资产、新scope真实生产CPU或GPU驱动兼容。GitHub直接镜像仍在下载，未称四卡已clone最新完整仓库。原runtime源码归档已完成并核对11关键SHA，不含凭据、模型或非生产媒体。
