# 784 — 发布源包与中央单次事务连接

源准备、完整资料准入、批准绑定、原中央预约绑定及唯一预约/结算入口已补齐。代码发布源为 `e56648d19be6b75825579642aac60c376d1acf50`，已核验GitHub main；宿主传输客户端另在 `29586354` 发布。两端各301个覆盖文件通过现有Git归档工具逐字节核对，未提交新GPU或运行CPU验证容器。

## 源包与双端准备

复用 `immutable_stage_payload_r1` 的源码读取、Python依赖解析、Git blob归档及传输工件检查。新准备器补齐普通脚本/测试模块的依赖与明确的校准manifest、profile、limits、设计文件和真实历史账本夹具；没有迁移或修改原工具。

每端使用自己的已接受原CPU registration：四卡为原校准R2的 `ad82aead…`，两卡为原Q5的 `c2728dc7…`。这些CPU registration提供 `parent_git_revision`，新计划显式保留这个字段名作为基底标记；不把它冒充原CPU实际执行源码。完整基底字节以原registration SHA及其payload SHA核对，新覆盖字节另绑定发布提交。

准备仅复制到固定的新独立stage，核验原runtime与所有源字节；已有相同完整stage只读恢复，partial、改变内容、错误host或symlink拒绝覆盖。原基底、runtime及旧运行不改。准备状态不写GPU批准；后续只有外部明确的单次批准、完整双端CPU证明及报价，才能绑定原生产权限。GPU曾有意图则不能重新准备、准入或绑定。

## 中央事务

新中央入口仅从登记为four_card的operator stage调用，沿用226GPUh唯一账本、原责任保留核算和每宿主一个实际作业规则。新预约必须是固定完整51查询/112路径/14GPUh，双端原句柄检查和选中宿主准入均新鲜；未知、已有原意图、缺批准/证明、资源不足或陈旧快照都拒绝。

预约先持久化精确before/after回执，再原子替换中央账本。中断后只恢复这笔原事务；已更新则复用同一回执，不能切换launch或host。结算先走原财务终态读者，包含原四类进程、容器、完整guardian单调实测账单与来源检查；成功、失败和真实超限都只记录原成本一次。重复成本冲突、进程UNKNOWN和CPU夹具进入生产模式均拒绝。临时账本测试保留原4.5+12GPUh责任及无关作业，不接触实际中央账本。

## 验证及实际连接

[本地R2回执](../reports/cara_budget_preparation_central_local_CPU_r2_20261030.json)：58项、0跳过、0失败，9项源准备、11项中央事务、15项单次入口、7项运行器身份、16项生命周期。实际执行临时文件复制、源字节核对、真实历史账本副本的原子事务与中断恢复；实际宿主准入元数据和进程提交仍为替身。不是双端整卡CPU接受或真实GPU结算。R1回执保留，R2补齐显式设计文件的包覆盖。

本轮只读登录曾同时成功：四卡 `user-Super-Server` 可用内存约64.3GiB，两卡 `minchen-X11DAi-N` 约53.6GiB，两端原registration SHA均与已接受回执一致。随后通过同一任务私有userspace ProxyJump检查固定新stage/原容器时，两端再次在SSH banner阶段超时，观察结果未知。实际只调用了observe，未调用远端prepare；没有新stage创建、CPU作业、GPU提交或中央预约。本轮未修改SSH/Tailscale/Clash或服务设置。

源包：[四卡](../reports/cara_budget_published_source_package_r1_20261030.json)、[两卡](../reports/cara_budget_published_source_two_package_r1_20261030.json)。归档及基底registration保存在本地`.sync`的独立目录，机器回执记录其SHA；原包不会覆盖。

## 下一步

恢复同一两端原句柄观察后，安装原发布源包，完成实际Linux及双端整卡CPU；并补64GiB非稀疏专用存储、独立48MiB日志及含生产端末次全量回读的完整实测报价。上述齐备后请求单次14GPUh实际启动批准，实际开始后再安排半程与终验。当前仅14GPUh设计方向获选，GPU启动仍未获批。

原62个B36源和A32冻结再次核验未改，cap226及旧16.5保持。S/Q原任务仍由原对话独立验收，主线不重复处理其运行。

[本轮总回执](../reports/cara_budget_source_central_preparation_r1_20261030.json)
