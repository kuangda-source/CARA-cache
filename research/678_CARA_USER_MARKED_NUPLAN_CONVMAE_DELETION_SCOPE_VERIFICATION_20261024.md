# 用户标记的NuPlan和ConvMAE删除范围核对

用户标记截图中的Epona/NuPlan约1.03TiB及ConvMAE约304GiB，并要求先核对。此次仅只读元数据；未删除、移动、改变进程或重跑104。完整遍历62,553个文件，核对当前所有可见进程的cwd/exe/root、FD和maps；未发现对两目录的正在使用引用，无权限缺口，无嵌套挂载、文件硬链接或文件软链接。当前无进程引用不保证未来任务无静态路径依赖，也不代表检查点已有备份。

| 精确路径 | 文件属主 | 文件分配空间 | 内容 |
|---|---|---:|---|
| `/data20t/zhaiheng/Epona/NuPlan-Download-CLI` | wangshuai / UID1010 | 1.031TiB | NuPlan压缩包、一个解压lidar目录、少量下载代码及Git记录 |
| `/data20t/maofangyuan/code/ConvMAE` | maofangyuan / UID1006 | 303.724GiB | 191个pth文件，主体为MCMAE_SEG/log和DET/output训练检查点，另含代码、配置和日志 |

这里是两个目录集合，不是两个单文件。NuPlan目录在zhaiheng路径下，但属主是wangshuai，不能按上级目录名确定所有者。ConvMAE主体是训练产物，不能把它们称为可重建缓存或声称已有备份。

推荐具体范围：删除NuPlan目录内nuplan-*.zip和解压的nuplan-v1.1_mini_lidar_1数据；删除ConvMAE内MCMAE_SEG/log及DET/output中的pth/pt/ckpt检查点，保留代码、配置、小日志和checkpoint中的基础权重。该范围可释放约1358.043GiB（1.326TiB）；整目录删除仅多释放约1.41GiB，却同时删除上述记录。已向用户询问只清大数据/训练检查点还是完整删除两个目录；在范围答复前不执行删除。删除前须再次核对原inode、大小、时间和进程引用，只对明确文件清单执行，不递归扩大到上级Epona或code目录。

核对时/data20t普通用户可用仍为0；恢复空间后仍须单独完成104失败账单、持久控制文件和ENOSPC生命周期修复，不能自动重跑。原104及CARA所有实验原件均不在两个目标目录内。

原件：[目录/进程核对](../reports/cara_two_user_marked_deletion_targets_readonly_20261024.json)、[逐文件清单摘要及完整本地清单SHA](../reports/cara_two_user_marked_targets_file_manifest_20261024.json)。前一项磁盘归因与104恢复方案保留在[677](677_CARA_DISK_GROWTH_ATTRIBUTION_SAFE_MIGRATION_AND_104_RECOVERY_20261024.md)。
