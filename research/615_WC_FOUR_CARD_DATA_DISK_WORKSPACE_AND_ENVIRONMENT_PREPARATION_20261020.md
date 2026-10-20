# 四卡环境实际准备：存储已过，代码/CPU环境独立部署

当前/data20t可用478,780,252,160字节（约445.9GiB），本人新工作区/data20t/gaokuangda/worldcache_workspace已完成64KiB写入/fsync/回读/删除验证。300GiB工作区规划加128GiB余量小于当前空间；原HF树逻辑大小51,651,996,220字节作模型存储保守依据，非已复制结果。数据盘cache/tmp/env/assets目录已建，系统环境没动，0GPU/模型加载/v2写。

四卡GitHub匿名私有仓库读取被拒绝，PyPI可达；官方HF元数据连接失败且未有HF凭据。既有Docker有权限，但缓存候选均不满足本次用户态要求：glibc2.27/2.31，一个ARM64候选不能在该x86机器运行，失败元数据保留。采用独立轻量官方Python3.10容器准备CPU环境，不改共享驱动/daemon；固定Cosmos要求与实际驱动/glibc差异已经明确，准备不等于可运行GPU。

新worker及固定recipe已实现并做本地语法/CLI与11关键runtime SHA核对；真实服务器环境尚待单次worker完成，不能称新scope生产CPU通过。完整执行与GitHub转运协议见plans/WC_FOUR_CARD_ENVIRONMENT_AND_GITHUB_SYNC_20261020.md。原BANK24/已批完整12卡/22:10资源时点保持。
