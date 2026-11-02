# P1新增入口CPU R2原句柄承接

仅恢复本原CPU，不prepare、重启或重派，不访问GPU或四卡。先读本地完整接受/失败关闭；如已有终态接受，不再连接服务器刷新状态。

- 原启动：`reports/cara_v1_P1_entry_delta_CPU_launch_r2_20261102.json`。
- 固定源：`4d4a00bec85af8b2382ff0b53c1a324ed25e85b1`。
- stage：`/data20t/gaokuangda/worldcache_workspace/.sync/cara-source-lifecycle-P1-entry-delta-CPU-host-r2-20261102`。
- registration：`562f1b2f07845cc04a75c21d35fe4197ad889a56ea28e3d56eb229c02c53e2ea`。
- 原宿主PID `3252271`，start ticks `687454702`，boot `13495735-f30b-47a2-af0a-2496f5206a0b`，namespace `4026531836`。
- 实际开始：2026-11-02 08:34:03.764620 Asia/Shanghai；CPU26/27、AS4GiB、CPU/wall1200秒、退出60秒，无GPU。
- [原开始检查安排](../../../reports/cara_v1_P1_entry_delta_CPU_acceptance_schedule_r2_20261102.json)：半程`p1-cpu`08:45，终验`p1-cpu-2`08:56。状态不变/不可行动保持安静，完整关闭后删除两项。

只用原capture：

```sh
python3 scripts/cara_source_lifecycle_p1_entry_delta_cpu_r1.py capture --source-revision 4d4a00bec85af8b2382ff0b53c1a324ed25e85b1 --output reports/新的唯一回执.json
```

完整原宿主退出后，用`scripts/accept_cara_source_lifecycle_p1_entry_delta_cpu_r1.py`，传原启动、完整capture、新接受与原字节输出。原23项为合成元数据：分析5、临时中央结算5、模拟RPC5、容器/worker入口8；本机原3图表控制仅按原Git源码复用。没有新指标、真实Cosmos视频或GPU Docker。先前R1缺Matplotlib在stage创建前拒绝，原只读确认stage不存在；传输意图和本地更早的回执类型拒绝全部保留，不恢复该失败准备。

当前本地图表已另做布局修订和3项实际渲染/视觉QA，参见`reports/cara_v1_P1_local_figure_CPU_r2_20261102.json`与`reports/cara_v1_P1_local_figure_visual_QA_r2_20261102.json`。这份新图表源没有写入正在运行的R2 stage，不能说原Linux测过该新布局。捕获和接受必须绑定上面的原Git源；新图表由其独立CPU回执覆盖。

完整接受后保持P1整卡GPU/账本未批准，继续35处原组件源码复用审计、正式配置/报价、生产绘图交付、私有64GiB存储与源包准备；全部具体可审阅后，才请求完整>4GPUh及本卡原账本事务。旧科学冻结/费用/保护最终16与备用16保持。

## 原件已关闭

[完整接受](../../../reports/cara_v1_P1_entry_delta_CPU_accepted_r2_20261102.json)：23项通过，08:34:13.997727正常退出，原句柄消失、源与runtime完整。原件不再capture/prepare；两项检查已删除，[关闭回执](../../../reports/cara_v1_P1_entry_delta_CPU_complete_cleanup_r2_20261102.json)。
