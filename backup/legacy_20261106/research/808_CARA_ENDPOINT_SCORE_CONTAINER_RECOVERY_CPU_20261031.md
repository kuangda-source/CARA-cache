# 808 — 端点评分原容器恢复与完整接受CPU验证

新端点评分的只读原容器恢复组件通过两卡27项CPU控制，随后12项独立终态接受检查通过。真实Linux子进程验证原CLI、原评分进程退出与host view，Docker状态和评分数值保持显式合成夹具。R2启动回执曾超时，随后只读恢复同一个容器的退出/0终态，未重派。本轮没有指标计算、原实验输出读取、GPU派发或中央账本访问。

## 原运行与修正

R2源码为`66f78b1302e4b36892f7da57103547070a7eb361`，stage为`/data20t/gaokuangda/worldcache_workspace/.sync/cara-S-endpoint-capture-CPU-a6000-r2-20261031`，容器为stage名加`-cpu`，注册SHA为`44431b7bb85881656d98fb3ef91e2fdabc9a140c575b156838da65a5e52996fe`。实际容器20:42:14启动、20:42:21退出/0，Pid=0、无OOM；worker实测6.327234983秒。外层CPU26、1核、4GiB、无额外swap、network none、只读根文件系统和无GPU设备由原capture核验。工作上限180秒、退出余量30秒。

R1源码`5a08b5defdbf9a9a1eaa896893ba5c5656e04ec5`的25项控制已经正常结束，原记录保留。其后检查真实Docker回执发现九位小数时间戳与Python3.9/3.10解析不兼容；旧夹具只含六位小数，未覆盖该输入。R2增加RFC3339Nano的UTC解析、真实九位格式及缺时区拒绝两项控制。R2是该受影响路径的新CPU验证，不重启R1，也没有重算807的真实合成指标。

R2的Mac启动命令因SSH回执超时返回-9，不能据此认定服务器未启动。后续原capture返回同一stage、注册源码和唯一launch记录及完整终态。接受器保留未知启动记录，要求恢复的launch不早于原prepare、stage/source/完整payload/runtime一致，再接受完整证明；没有补造一次成功启动传输，也没有再次prepare。

## 恢复边界

只读恢复器绑定完整工件包、原GPU释放launch、规范评分manifest、注册源码与runtime。检查原容器ID/name/image/manifest label、明确CPU资源与GPU隐藏、无自动删除/重启、host PID视图、精确只读project/stage及唯一可写评分输出、原入口/命令/用户/PYTHONPATH。

容器缺失、Docker观察失败或boot/namespace未知均保持UNKNOWN；活跃容器或原CLI不读评分，失败容器不读部分评分。仅在原容器退出/0、无OOM、原CLI退出后读取原评分intent，继续确认原worker PID/start ticks/host view已退出；随后才打开完整结果，核对进程身份与容器时间区间并调用807的完整24接受器。此读者不会派发、消耗一次执行意图、补写缺失launch、重评或结算。

22项元数据控制覆盖完整十二对及别名八对、活跃/未知/失败、原句柄仍活跃、容器替换、manifest/source改变、GPU设备、资源与重启设置、额外挂载/可写源码、命令变化、时间区间及CPU夹具隔离。5项实际Linux控制覆盖原CLI活跃、CLI结束但worker活跃、全部原进程结束后接受、重复只读接受不改原文件、错误boot保持UNKNOWN；第三个独立哨兵进程在检查中保持存活，测试收尾只停止自己绑定的子进程。

外层验证容器是真实Docker运行；内部目标评分容器的inspect是合成数据，评分行也是合成数值。本轮不证明实际生产评分容器已派发，也不形成新科学结果。生产端点仍固定2核/8GiB/4小时，完整24逻辑位置、12份原指标不变、12或8唯一新对。

## 剩余工作

本轮完成原容器恢复与完整接受门。一次性生产CPU容器派发、缺失启动回执下的派发意图恢复、实时CPU/环境准入仍须接入；新GPU runner/一次派发、整卡CPU及24位置汇总/图表也未完成。实际预算mask仍等待原112路径/51查询完整验收与一次冻结，之后绑定受影响验证、最终源和完整报价，再取得新卡授权。

原14GPUh实验及23:16半程、次日06:01终验、06:45:04硬截止保持。本轮未重新观测它的GPU状态或读取部分科学分数。A32/B36/原S冻结、科学表行、cap226与旧16.5责任不变。

[R2原接受](../reports/cara_s_endpoint_capture_CPU_accepted_r2_20261031.json) · [R2原终态](../reports/cara_s_endpoint_capture_CPU_capture_r2_20261031.json) · [保留的未知启动回执](../reports/cara_s_endpoint_capture_CPU_launch_r2_20261031.json) · [独立接受检查](../reports/cara_s_endpoint_capture_acceptance_checks_r1_20261031.json) · [恢复器](../src/wcomr/cara_s_endpoint_score_capture_r1.py)
