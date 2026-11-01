# P1：完整算法与宿主评分接口接受

完整算法和宿主评分接口的两份原 Linux CPU 已结束并接受。它们补齐 V1 自动生成19D/22D计划、完整FIT选择与原评分交接的实现证据；尚未产生真实 Cosmos 的 V1 校准或视频结果。

| 原验证 | 完整接受内容 | 原终态 |
|---|---|---|
| 算法 R3，source `aca025a7` | 33项控制；flow OFF/ON各146语义/64标签/134实际tiny请求；合计292语义、128标签、268请求、158对真实Alex权重的合成93帧指标 | 04:57:48启动，05:29:37退出0；单核26/4GiB/无GPU |
| 宿主FIT探针，source `7c48488a` | 两个完整两FIT请求；重复客户端和终态reader均零新增；第三请求第二个视频预设编码失败，保留2分母/1已完成对，禁止部分均值进入算法 | 05:27:51至05:29:22，父进程/服务/媒体及3评分容器均已结束 |

R3 的两个flow分别有39/40个不同完整评分cohort，质量别名继续保存全部语义位置。原件恢复未调用生成或评分回调，成功/原件恢复/存储拒绝后的调用者forward绑定、状态和参数均还原。R1 writer失败及R2外层caller恢复失败保留；不重放它们的已完成首flow。

宿主父进程/服务的CPU26/27、RLIMIT_AS4GiB、CPU/墙钟1200秒单独记录。实际四个Docker为2核/8GiB/无额外swap、26/27、无网络/无GPU、只读root/source、唯一可写输出；不以宿主RLIMIT代替容器配置。固定Alex/PIQ评分核未改。预设失败成功触发完整失败回执，原服务非零退出；两个成功回执在新终态观察后字节不变。

- [R3完整接受](../reports/cara_v1_P1_algorithm_Linux_CPU_accepted_r3_20261102.json) · [R3原proof](../reports/cara_v1_P1_algorithm_Linux_CPU_original_proof_r3_20261102.json)
- [宿主实际CPU接受](../reports/cara_v1_P1_host_FIT_CPU_accepted_r1_20261102.json) · [宿主原proof](../reports/cara_v1_P1_host_FIT_CPU_original_proof_r1_20261102.json)
- [检查清理](../reports/cara_v1_P1_algorithm_CPU_acceptance_cleanup_r1_20261102.json)

下一缺口是完整外层执行与释放后接受。新增窄接口把唯一宿主FIT服务放进原guardian的开始/活性/收尾：启动失败不派GPU容器，服务失败停止原GPU，GPU失败也关闭原服务；等待和清理进入原guardian区间。CPU清理未知保留原失败，GPU原释放/实际账单仍可恢复，科学接受另外要求CPU原终态。旧调用者默认不启用此接口。新服务组件5项本地控制通过；原entry及broker回归合计29项通过，另5项真实Linux原进程场景须在新CPU接受，不能以本地skip称通过。

完整P1仍为146语义位置上限，最多142物理生成、84内部指标对和32释放后新指标对。全卡释放/唯一结算后须复用原内部分数，完整汇总与一次冻结。10.9158、含20%余量13.0989GPUh仍是草案，硬限未定；待外层源、资源、存储、评分接受及正式报价就绪后，再一次提交>4GPUh和本卡中央事务许可。没有新增GPU或账本操作，旧冻结及16保护/备用16保持。

补充：新增guardian/FIT CPU的R1在导入阶段因缺少`test_cara_s_endpoint_host_guardian_r1`提前退出1，未进入34项控制；[原失败](../reports/cara_v1_P1_guardian_FIT_Linux_CPU_original_failure_r1_20261102.json)已保存，不重放。独立R2补齐两份测试依赖，并在派发前审计62份可达本地测试helper的注册闭包。该修订只影响CPU源包；上表两个已接受原件保持，GPU仍未启动。
