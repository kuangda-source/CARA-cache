# P1已批准：原资源准入与唯一启动交接

用户2026-11-02明确回复“批准单次 19 GPUh 及本卡账本事务”。仅这张完整卡获批，无需再次询问GPU预算或本卡原账本事务；[独立授权](V1_P1_SINGLE_CARD_AUTHORIZATION_R1.json)、[完整审批卡](V1_P1_SINGLE_CARD_REVIEW_R1.md)、[本次准入等待](../../../reports/cara_v1_P1_approved_admission_wait_r1_20261102.json)为原件。旧P0/其他卡许可不复用。

## 固定身份

- run：cara-source-lifecycle-V1-P1-full146-r1-20261102
- launch：a2b1dcf993774897902a5f0cc0858220
- source：dd2a73060f4097ceb91dd66c8a5f98a33fe65092
- GPU source registration：bded3f7a6cdbfe12f0993720e910a489230ae43b7975a48a7745259a5f96069b
- stage：/data20t/gaokuangda/worldcache_workspace/.sync/cara-source-lifecycle-V1-P1-GPU-a6000-full146-r1-20261102
- two_card唯一A6000：GPU-cebf7119-cf03-23b9-e192-cd196332b704

完整146语义位置／最多142物理请求／5176模型pair／64同状态标签，自动19D/22D、嵌套来源消融与同实际费用LPIPS搜索。预计18.0273375924GPUh、硬19，90°C、600秒停止释放余量、GPU40GiB/内部CPU8GiB且不swap、宿主最低52GiB；全部原科学合同/最终16与备用16/原冻结保持。

## 已完成与当前阻塞

唯一GPU源、CPU/报价/独立64GiB与48MiB日志均已接受。新授权原字节已实际绑定，见authority_bound原件；禁止再prepare源包、存储或CPU。原admit已扫描全部生产资产并写出stage/fresh-admission.json，但最终内存门拒绝。诊断：MemAvailable49.7760GiB<52，CPU24–27亲和性满足、原GPU空闲45°C，无GPU意图/派发/启动。没有发现可释放的大型旧实验进程；不停止其他任务、不降门槛。

本卡四卡原中央operator已准备完成，115文件，缓存/tmp/source-lifecycle-P1-central-operator-a2b1dcf993774897902a5f0cc0858220。central-prepare已完成，禁止再创建。原账本读取通过：cap226、used197.02183603468436、旧责任16.5、available12.478163965315645，P1不存在、envelope空、0账本写入。若届时账本不变，需按已批准规则最少一次24GPUh增量至250才能预约19；每次实际增量通知，当前尚未增额。

## 准入与一次启动

所有操作从本机调用scripts/cara_source_lifecycle_p1_control_r1.py，输出使用新的唯一reports路径，保留所有拒绝/失败。原Tailscale私有配置与stdin凭据已接通，禁止改网络/路由或泄露凭据。

1. status --output 新回执。若已有GPU意图、派发、启动、guardian、容器或UNKNOWN，只恢复这个原句柄；禁止重派、换源、换卡或另建run。
2. 原运行不存在时，用refresh --output 新回执（原admit已保存资产身份）。它重核原源码/资产stat/存储/设备/内存/权重/独占与完整范围。若52GiB不足，保存一次运维回执，等待同一个准入检查下次执行；不进行中央预约。原输出和journal须空。
3. 完整refresh成功后，central-status检查已准备的原operator和唯一账本。必要时再refresh，确保reserve --input 原refresh回执时其资源和原句柄观察均在60秒内。reserve仅能给原run唯一预约，并在原账本事务内记录最少24GPUh增量。网络未知先central-recover，恢复同一事务，禁止重复增额/预约。
4. dispatch --input 原reserve回执。若中央快照超过60秒，用central-status取同一原envelope的新快照再dispatch；不创建新预约。dispatch也重新检查现场资源；既有意图只status恢复。硬19、源和完整范围不改。
5. status恢复真实GPU-launch/guardian/CLI/supervisor/runner的PID-start ticks、容器ID、唯一CUDA上下文与实际guardian开始。GPU实际开始前不称已启动。
6. 根据实际开始设置一个半程（约+9小时1分）和一个全程（约+18小时7分）的线程heartbeat，实际hard cutoff+19小时，停止释放余量600秒不变。只静默检查原句柄、146分母进度计数、温度、资源、独占和账本；无变化不通知。半程可按计数/墙钟前移同一个终验，不创建重复检查。保存实际启动回执、两个检查ID及GPU post-launch handoff后，删除本准入检查。

若等待资源仍不可行动，只保留同一15分钟准入检查，不创建新的重复检查或GPU实例。用户授权持续有效。

最新入口恢复状态和是否已询问用户，以docs/project_status.json的P1_latest_prelaunch_operational_ref/P1_network_restore_question_pending为准。原status入口UNKNOWN时不得假设未运行或仍为旧内存值；只恢复原状态，不refresh/预约/派发。已有连接恢复问题待回复时不重复提问，仍保留同一检查；原19GPUh批准保持。

## 原终态、释放与唯一费用

成功失败都先status取原完整terminal lifecycle与launch SHA，检查原guardian容器终态、CLI/runner退出、锁释放与Default恢复。settle --input 原terminal status回执，唯一结算原guardian全段实耗。网络UNKNOWN先恢复原中央事务；不得再次收费。四卡只做本卡原中央事务，不跑实验、不迁账本。失败保留全分母和实际费用，不冻结、不评分、不自动下一卡；收尾后删除剩余检查。

## 完整成功后的CPU接受与导出

完整GPU成功释放且唯一结算后，在原stage固定source调用wcomr.cara_source_lifecycle_p1_artifacts_r1.released_artifacts(capture,expected_launch_sha256,settlement)。它先验证release，再完整读取146/最多142物理、64标签、所有等价/RGB与原封存FIT。不得在此前查看部分科学分数。

用原internal-score-environment.json的torch_home/piq_site/weights_sha256调用wcomr.cara_source_lifecycle_p1_scores_r1.bind_post_scorer，随后原wcomr.cara_source_lifecycle_p1_score_dispatch_r1.dispatch(stage,packet,config,registration_sha256)仅派一次至多32新对。post-score-control/intent.json存在则只recover(stage)，不得重派。原bootstrap和固定CPU资源/截止/原PID-start ticks必须验证。完整52接受时已封存内部FIT原样复用，不重评旧指标或重选任何原FIT赢家。

之后原wcomr.cara_source_lifecycle_p1_report_r1.complete(stage)完整汇总输入等权结果/双时钟/93帧/实际校准费用，一次冻结原FIT计划；原分析seal消除只读观测时间变化，已有结果只接受相同原字节。使用原scripts/cara_source_lifecycle_p1_result_bundle_r1.py export --stage 原stage导出完整report/analysis/freeze原字节和SHA；取回原导出包后在本机按独立SHA render，不在服务器安装绘图库、不再评分。固定13角色52位置及FIT/曝光CHECK/四旧CAL分别解释，工程筛选不是论文成立线。更新canonical、研究记录及原件引用，精确提交推送；完整接受后删除终验和多余检查。
