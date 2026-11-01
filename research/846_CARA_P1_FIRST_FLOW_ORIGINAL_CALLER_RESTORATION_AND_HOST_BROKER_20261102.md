# P1单flow原件、调用者恢复修复与宿主评分接口

P1 R2的首个flow完成了完整算法：146语义位置、140实际tiny请求、64同状态标签、41个完整双FIT查询/82对真实Alex指标，原算法恢复也未新增请求或评分。外层原采样器检查随后发现`net.forward`未还原给调用者，原CPU于04:41:54退出1，第二flow未到达，因此完整CPU入口尚未接受。这些均为合成媒体和tiny模型，不是V1视频结果。

[原完整单flow字节](../reports/cara_v1_P1_algorithm_CPU_R2_first_flow_original_r1_20261102.json) · [原R2失败](../reports/cara_v1_P1_algorithm_Linux_CPU_original_failure_r2_20261102.json)。原R1 writer后缀失败同样保留，不重放原R1/R2。

## 修复与下一原CPU

`apply_worldcache`在P1 loaded入口安装`net.forward`；原完整状态恢复保留的是安装后的WC绑定，不能代替恢复调用者原方法。生产入口现使用原`clean.patched`围住整段安装/收集/恢复，恢复原属性的存在性和原绑定；请求适配/collection构造也纳入finally状态恢复。固定特征、ridge、源标签、DP、选择规则和指标实现均保持。

新CPU增加成功、原件恢复及存储拒绝路径的调用者绑定检查。原R2单flow实耗约18分41秒，新的完整双flow工作上限设3600秒、退出余量60秒，仍单核26/4GiB/no-swap/no-network/no-GPU；完整两flow均须接受，未缩小范围。入口`scripts/cara_source_lifecycle_p1_linux_cpu_r3.py`，独立R3 stage；原R2源47a0048c和原工件保持。

## 宿主评分接口

[实现](../src/wcomr/cara_source_lifecycle_fit_broker_r1.py)与[原CLI](../scripts/cara_source_lifecycle_fit_broker_r1.py)已接通队列、固定CPU容器命令、原PID/容器恢复及完整内部接受。本地九项控制通过：只读来源和唯一可写CPU输出、2核8GiB/no-swap/无GPU/无网络、错误设备/挂载/命令拒绝、原终态一次接受、活跃/UNKNOWN禁止新派、CPU失败保留双FIT分母、越界工件/非19/22纯C策略拒绝、deadline前置准入、运维仅计数及终态读者不能启动任务。

重复读取使用第一次封存的execution witness，最新liveness时间戳不会改写已接受哈希；终态读者不要求已退出的guardian继续存活，也不能创建CPU查询或服务。真实Linux宿主服务、独立容器资源/命令与失败清理仍待接受，不能把本地伪容器检查称为真实隔离证据。

## 剩余推进

继续新R3完整CPU原件验收，同时完成宿主broker的真实Linux CPU、完整终态/释放/唯一结算及补充指标接受、图表/冻结和整卡准入。范围仍146语义/最多142物理，最新10.9158GPUh、20%余量13.0989是草案，硬限与GPU权限均未定。P1仍须完整方案单独批准；四卡原账本例外未授予，未访问中央或新增GPU。
