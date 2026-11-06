# 完成实验重复张量的R2只读合并与恢复

R2控制目录：`/data20t/gaokuangda/worldcache_workspace/.sync/cara-cold-archive-r2-20261024`。这是同盘去重，不是异地备份。

`verified.json`列出9组、38个原始路径的原inode/device/bytes/mtime_ns/mode/uid/nlink和SHA；`commit.jsonl`记录15个原子替换；`committed.json`为成功终态；`objects/<SHA>.pt`与全部实验别名只读硬链接。旧20261023归档对象和路径保留，跨新旧归档的相同对象共享inode。

原实验的逻辑原件和角色均保留，不能将硬链接复用计作新增样本。不得向共享对象写入或先chmod再修改。

恢复某个需要修改的别名：

1. 从`verified.json`查到该路径的原metadata与SHA，确认有足够空间，目标没有活跃写入。
2. 将对象复制到目标同目录的新临时文件（必须新inode，禁止硬链接）。
3. 完整SHA核对后，按记录恢复mode和mtime；fsync文件。
4. 原子替换指定别名并fsync父目录；确认它与共享对象inode不同而SHA相同。
5. 保存恢复回执。其他别名和归档对象保留。

[独立接受](../../reports/cara_completed_tensor_dedup_r2_independent_acceptance_20261024.json)已验证38路径、9组SHA、只读属性，并完成一个完整对象的独立复制恢复探针。
