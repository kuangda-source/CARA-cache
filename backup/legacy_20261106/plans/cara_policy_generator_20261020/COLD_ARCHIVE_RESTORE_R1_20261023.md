# CARA 完整原件的同盘去重归档与恢复

## 保存位置与范围

2026-10-23 完成的归档类型是**同文件系统、只读、SHA寻址对象＋原始路径硬链接**，不是异地备份。没有压缩、重新序列化或删掉任何实验逻辑路径；原 JSON、视频、最终latent、正式1624区间、Native参照、价格、源码/环境/模型和P1输出保持。

- archive root：`/data20t/gaokuangda/worldcache_workspace/.sync/cara-cold-archive-20261023`
- `objects/<SHA256>.pt`：经过完整校验的只读原字节。
- `duplicate-verified.json`：452组 source/canonical 的SHA、大小、inode、uid、mode、mtime。
- `duplicate-commit.jsonl` / `duplicate-committed.json`：实际完成过程和原路径→归档对象映射。
- 本地Git回执：`reports/cara_exact_duplicate_archive_committed_20261023.json`；原恢复核验 `reports/cara_archive_restore_and_P1_protection_verified_20261023.json`。

452个重复文件包括442个warm1624区间/teacher张量和10个重复all36-guided张量，共12,852,656,704 bytes（约11.97GiB）。每个原路径仍存在，SHA和内容相同；归档只合并存储，不合并实验角色、独立运行身份、warm/正式分母或费用。BANK24原始张量仅盘点，未进行归档改动。

复核方式：重新读取记录中的每个 source/canonical/object，确认三个路径指向同一inode、文件长度匹配、无写权限；需要内容审计时重算SHA与原已接受回执匹配。原实验接受器可以继续读取原路径，不必修改历史记录。

## 何时恢复为独立副本

普通只读分析无需恢复。若未来确需写入，应先恢复为独立副本，**不可 chmod 后直接改硬链接内容**，否则会修改该对象的所有别名。应使用新run输出目录处理分析，不改历史原件。

完整恢复需要重新提供约11.97GiB空间并额外保留当前任务准入余量。恢复单个 source 的步骤：

1. 从 `duplicate-committed.json` 精确选择一条 source，确认账号/路径及没有活跃任务正在写该文件；检查可用空间。
2. 把 `archive_object` 复制到同目录一个新的、独立inode的临时文件；不得创建新硬链接当作恢复。
3. 校验临时文件大小与 SHA-256，恢复 `source_original_metadata` 中的mode和mtime_ns；fsync文件。
4. 原子替换 source 路径。确认 source 与archive_object不再同inode，但SHA完全相同。
5. 保存恢复回执。归档对象和canonical不删除，除非后续另有明确维护要求。

本轮已实际在归档目录做一次独立复制恢复探针，确认SHA一致且inode不同，随后只删除该新增探针。所有原始路径和归档对象保留。

## P1 保护

归档前核查所有选中文件均归UID1000、原任务已退出、没有本人进程打开；fresh SHA核验后才替换，原子替换之前先建立归档对象。P1使用的stage内标签/价格JSON与当前输出目录不属于归档集合。归档后原PID1148184/start954343237和容器仍运行，P1全部登记payload SHA保持、registration为31cc191345c36e31ed6dbad4109c859ffa0594da3ce87590beff46f1e774d4f7。

初次大文件哈希触发160秒只读包装超时，原失败保留；随后扩大只读核验时间窗口完成，不重复执行GPU或改变费用。归档脚本只用本人文件权限，无sudo、GPU模式或其他用户进程操作。共享盘空闲变化包含并发写入，不能把净磁盘差全部归因于本任务。
