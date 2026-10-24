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

## 用户选择与实际完成

用户随后明确选择“只删NuPlan数据及压缩包、ConvMAE训练检查点；保留代码、配置和小日志”。已按上述固定逐文件清单执行，未整目录删除。实际收件时间2026-10-24T13:04:25.005840+08:00：61,974份目标文件已删除，原分配空间1,458,187,579,392字节（1358.043GiB）；579份保留文件删除前后完整SHA256一致。包括ConvMAE基础权重的checkpoint目录、全部代码、配置和小日志保留。两次删除前进程/映射核对无引用；逐文件dev/inode/UID/size/mtime/ctime重新验证，任何变化即停止。目录结构保留，未递归删除上级目录，未触碰CARA原件、任务或GPU。

/data20t普通用户可用从0恢复到1,458,187,579,392字节（1358.043GiB）。这是实际statvfs快照，可能随其他任务变化；本次实际可用空间增量与目标文件分配空间一致；不把估算代替实测。原104失败和11.9GPUh预约仍保留，未结算、未评分、未重跑；恢复方案仍需独立执行决定。

[删除前身份与保留SHA](../reports/cara_two_targets_predelete_identity_and_retained_SHA_20261024.json) · [实际清理与保留SHA复验](../reports/cara_two_targets_authorized_bulk_cleanup_complete_20261024.json)。远端小审计原件：`/tmp/cara-user-authorized-bulk-cleanup-20261024-1305.json`。
