# CAL12完整12已单次准入 两次查收已安排

**连续24已完整接受后，CAL12于2026年10月19日15:57:36.932单次派发，原supervisor、runner、CPU post、GPU0锁及2.5GPUh整卡预留已独立核对。16:54只作技术半程，18:06作完整原件验收。当前没有CAL12新增质量或速度结果。**

## 上游和新卡范围

[604连续24完整结果](604_WC_WINDOW24_FULL24_ACCEPTED_CONTINUOUS_CORRECTION_RESULTS_AND_CAL12_NEXT_20261019.md)已经接受全部24位置、16正式1488帧及费用1.810126444846GPUh。原Window24不重查、重派或重跑CPU。原unknown与同句柄元数据恢复链保持。

CAL12自己的生命周期R2 source为2bd41dc8fa19f42353e03a7c78b7264b4b2695c6，stage为.sync/wc-scout-cal12-gpu-lifecycle-cpu-r2-20261018，全部1789源/runtime、20控制和真实入口依赖两命令已验。实际生成仍调用c1c95ce0入口、原1772依赖，不使用当前HEAD替换。原数值248＋10与实际入口CPU直接复用，未重新验证或派发它们。

四旧CAL×G01_LATE_A与VARIATION26_C，两配置各四正式视频，另各两完整预热：8正式＋4预热＝12路径，432guided pairs／864CFG／一次加载／零新Native／零额外teacher。G01补充C21、A22/23；共享计划取消D33、增加D22，保持26D＋10C。原C21不额外计算A或D。

## 真实资源和一次派发

[fresh预检](../reports/wc_scout_CAL12_fresh_preflight_20261019.json)实际15:56:48确认两卡无compute进程、GPU0/1显存320/24MiB、两UUID锁free，CAL12原stage无fence、launch、admission_failure或输出。原v2实结115.83511083569408/cap226、预留0，完整新卡余额充足。

只执行一次原启动器，绑定本卡自己的R2 CPU三件套及上游Window24实际capture/accepted。服务器在派发前重验实际依赖、CPU证明、来源和上游，再由supervisor按v2事务及逐UUID锁完成准入。

| 身份 | 原值 |
|---|---|
| launch-ref | reports/wc_scout_CAL12_full12_GPU_launch_20261019.json |
| launch_id | f3c235ac-1b69-45e5-81cc-4d1cdbd92b08 |
| run | wc-scout-cal4-g01-var26-full12-r1 |
| GPU0 UUID | GPU-de9a5370-cd87-0f1c-a48e-288888777dd3 |
| supervisor | 2729092 / start_ticks569156045 |
| runner | 2729134 / start_ticks569156584 |
| CPU post | 2729096 / start_ticks569156053 |
| 注册SHA | bc3ac7e60d81677722ce5d3960e9e8dd61733d27b2b42e24c067930285b0461a |
| 实际CPU proof SHA | 4249f5362698815ec1dfc871d9b648f0a39e0413dbc557660c222d64071efbb8 |

服务器返回的是已解析符号链接的/media/minchen/4def5c03-8324-4cba-ac0b-9fda7c79dc7b/gkd/worldcache_omr路径，与/home/gaokuangda/data/gkd/worldcache_omr是本次已验同一项目。保留原启动回执中的canonical路径，不修改冻结stage或原source。

[一次admission捕获](../reports/wc_scout_CAL12_full12_original_admission_20261019.json.gz)与[本地独立接受](../reports/wc_scout_CAL12_full12_independent_admission_acceptance_20261019.json)核对三句柄PID/start_ticks存活、SCOUT_GPU_RUNNING、注册身份、原CPU证明、完整12范围、原job/授权/UUID及锁持有、池账总数。只作准入观察，没有打开方法质量或逐步科学partial。启动回执的初始actual_admission_accepted=false保留其初始时点，不覆盖原文件；后续独立接受记录实际准入。

## 查收安排

[实际自动化绑定](../reports/wc_scout_CAL12_full12_two_once_collection_automations_20261019.json)已通过工具创建并从本机配置独立核对。

| 查收 | 最早北京时间 | 实际安排 | 自动化 |
|---|---|---|---|
| 技术半程 | 16:53:54.932 | 16:54 | worldcache-cal12 |
| 完整原件与gate | 18:05:12.932 | 18:06 | worldcache-cal12-bank24 |

半程只核对技术状态，即使已结束也保留原最终验收。终态仅捕获一次原件后离线分析，检查完整12分母、4warm的observer OFF/ON全36guided/终态/actions/A历史/93RGB、原entry/source/CPU/上游身份、可用原张量、同状态前20步及probe/inputhash、所有兼容正式93帧LPIPS、owner释放、实际全wall费用及本UUID锁释放。失败、拒绝、未到达保留，未完按剩余量另约一次后结束，不循环监听。

完整接受后只从四CAL固定μ和中位秩阈值，方向较大z保留D、平局>=；六DEV不重新拟合或翻转方向。G01修正四格交互与共享计划分别解释，不将任一正结果记成原H1已胜强前密。

原Window24终态自动化worldcache-window24-cal12已通过工具删除并核对；不再保留无用途资源巡检。若下一卡资源受阻，再按原规则每两小时检查。

## 费用和下一张卡

CAL12完整预测1.876666667GPUh、上限2.5，沿原严格少于12GPUh直接授权执行。准入后池账实际115.83511083569408/cap226、完整预留2.5、可准入107.66488916430592；本卡实际费用未知。origin79.99637737158223及所有历史保持，预留不当实费。

CAL12全部适用原件／费用和四CAL gate接受后，依[就绪手册](../plans/WC_SCOUT_GPU_READY_CONTINUATION_20261019.md)接BANK24自己的R2 CPU三件套、实际CAL12上游和固定gate，重新fresh UUID/v2完整准入。BANK24六DEV×D21/A21/Native35，18正式＋6预热，完整24／864pairs／一次加载／六Native，预测3.407222222、上限4.5GPUh；不提前派发。

X-R共享银行，不另开GPU。观察器开销计费，不把单次诊断时间或离线单点门控重组当完整在线加速证据；探索不自动并入主稿。N10不重评，F/B关闭，不新增训练、人评、付费VLM或OMR。

## 16:54半程技术检查正常

16:54:38.629按时一次[原任务半程捕获](../reports/wc_scout_CAL12_full12_midpoint_health_20261019.json.gz)确认：完整12分母中11完成、1运行、0未到达。已有12条记录不等于12完成。原supervisor2729092、runner2729134、CPU post2729096的PID/start_ticks均与准入回执一致，原GPU0锁持有，GPU与supervisor错误标签均为空。

[独立技术接受](../reports/wc_scout_CAL12_full12_midpoint_independent_technical_acceptance_20261019.json)另核对原source／注册／实际CPU与授权绑定、完整12计数、原job及v2加法总数。实结115.83511083569408/cap226、整卡预留2.5、可准入107.66488916430592保持；本卡实际费用尚未知。没有读取质量、逐帧、张量或方法时间，不能将COMPLETE技术记录当作科学原件验收。

[半程关闭与最终保留](../reports/wc_scout_CAL12_midpoint_automation_closed_final_retained_20261019.json)确认：本次worldcache-cal12自动化已删除，worldcache-cal12-bank24仍ACTIVE，原18:06时间／not-before／完整验收和BANK24接续保持。没有追加巡检、重新派发、修改原stage或提前开下一卡。
