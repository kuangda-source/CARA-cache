# 只读预算读取修复与 BANK24 完整工具 CPU R2

2026-10-22。继续已授权四卡执行准备；原 BANK24／完整 1624 的范围、顺序、预算和具体 12 GPUh 批准保持。

## 原 R1 已完整收件并明确不接受

11:30 接续实际于 **11:33:11** 用原已授权认证一次恢复本机 SSH master，真实新 PID **28085**，专用 socket 仍为 `/tmp/wc4prep-501/model-r4.sock`。未重启 FRPC 或其他连接，没有测试远端命令、模型下载或 GPU。原转发代理字段保留历史身份，新连接仅用于原 CPU 收件。

随后仅一次收取原 source `a25ae777d075fb937ff61e3e67886e9f682a01ed`／PID632076／start941236421 的终态，实际观察 unix `1792640008.7744792`。原 worker 记录结束时间 unix `1792627374.0202038`、wall **73.078873 秒**；这是 worker 留存时间，不是对08:02时点补作现场观察。

原 CPU 明确失败且不接受完整 scope。17 项失败留存核对通过：14 payload／manifest、1,789＋29 原 SHA、原进程和 fixture 退出、已尝试 post 容器不存在、观察 FD／IPC及资源锁释放、env／runtime保持。一次 Popen／原句柄恢复已经执行，但后处理失败，后续 collector／拒绝控制没有完成，不能以成功子集称完整通过。

实际异常位于原 `BudgetPool.read()`：它进入写方 transaction，以 `a+` 打开 `.sync/gpu-budget-v2.lock`。CPU post 的 workspace 按契约只读，因此触发 `EROFS`。这不是缺模型或依赖证据。原 job／源码／结果／失败日志和两个 UNKNOWN 收件全部保留，原失败不改成成功。

- [本人连接恢复](../reports/wc_four_card_owned_SSH_master_original_CPU_recovery_20261022_1130.json)
- [原 R1 完整终态](../reports/wc_four_card_BANK24_full_execution_tools_CPU_R1_terminal_recovery_20261022_1130.json)
- [原 R1 不接受](../reports/wc_four_card_BANK24_full_execution_tools_CPU_R1_independent_acceptance_20261022.json)
- [17 项失败留存与定位](../reports/wc_four_card_BANK24_full_execution_tools_CPU_R1_complete_failure_and_readonly_budget_diagnosis_20261022.json)

## 独立 R2 修复

只为生成的 CPU post 精确替换预算读取接口。新读取器要求账本与锁已存在且为物理文件，以 `rb` 和共享非阻塞 flock 读取；继续调用原 `BudgetPool.accounting` 校验完整 job 记录和存储汇总。缺文件、锁被 writer 持有、汇总不一致或 symlink 均拒绝。读取器不初始化、创建或改写账本及锁。GPU admission／reserve／settle 的写接口保持原规则；采样、guardrail、读出、gate和质量审计逻辑保持原科学来源。

真实 CPU post 另核对预算与锁的 SHA、inode、大小和 mtime 在执行前后相同。R2 独立收件再次核对 fixture 预算及锁的实际 SHA，避免只凭 worker 声明接受。

**8 项针对性测试与 20 项原执行工具回归通过**。新冻结配方 [完整工具 CPU R2](../manifests/wc_four_card_bank24_full_execution_cpu_r2_20261022.json) 绑定原 R1 失败三件套／源码／14 payload；新部署先只读确认旧 worker 和已尝试容器退出、旧原件未变，再创建独立 R2 job。旧 R1 stage 不修改，不重派。

R2 仍只执行最后一张完整工具 CPU 卡，复用已经接受的模型、资源／前端／SM89组件／跨容器和原1,789＋29依赖。一次提交、结算后 CPU post、四项拒绝及真实 collector 在新 job 下验证；GPU 过程／遥测仅为 `TEST_ONLY` CPU fixture，0神经路径、全24未到达、0评分，费用公式不当实际 GPUh。新 job 为 `wc-fourcard-bank24-full-execution-cpu-r2-20261022`，未来生产 target 也单列 R2，源码发布后才可单次实际 CPU 启动。规划300秒／最长1200秒，实际 launch 后半程及终态各约一次，不虚排尚未启动任务。

## 后续条件

R2 当前仅完成实现和本地控制，尚未实际验收。完整 scope CPU、实际 CUDA、新机实测价格、唯一权威 v2 和 GPU-ready 分别待验。整卡 BANK24 保持6DEV×D21／A21／Native35＝18正式＋6warm／全24／864pairs／1728CFG／1load／6Native；保守规划6.974166667GPUh、完整上限8.75仍非Ada实测。原四CAL固定mu／中位秩、较大z留D、平局>=，DEV不重拟合。

未取得双卡完整权威历史／settlements／全部活动预留和唯一写入权交接前，不开 GPU 或免费 CUDA probe，不用旧116.825快照另建账本。两卡只读监控仍下一15:19，本卡不查询双卡。BANK24全部原件及实费接受后，先既定X-R／同D配额CPU，再完整1624；其4CAL×406／14路径／含warm2030格／13020试验与具体12GPUh批准不重问、不拆缩。cap226／origin79.99637737158223、全部历史及54科研行和status_counts不变。F/B关闭，无训练、人评、付费VLM／OMR。

## 2026-10-22 完整工具CPU只读预算修复R2于11:50实际启动，11:53／11:58查收

[635实际原件与接续](635_WC_READONLY_BUDGET_READER_FIX_AND_FULL_BANK24_TOOLS_CPU_R2_20261022.md)：原R1完整失败／17项留存审计保持。修复后的source6d9cd494已GitHub发布，R2于11:50:27.049436单次启动PID644729/start942609041，独立job和target均为R2；14payload／原1789＋29及全部已验资源复用，不改旧R1 job。11:50:39一次admission确认原worker活、source／manifest／生成源／2CPU16GiB和旧R1失败绑定一致，已进入一次提交及结清后真实CPU post阶段；仅技术准入，尚未完整scope CPU接受。只读预算修复沿原accounting、已有锁rb／共享flock，8新控制＋20原工具回归通过，实际post预算／锁不改写及collector完整链仍待终态独立验收。已读回bank24-full-tools-r2-cpu-halfway于11:53一次半程、bank24-full-tools-r2-cpu-terminal于11:58终态，按实际launch最早11:52:27／11:57:27，不回填观察；旧R1终态自动化已完成删除。本人SSH master当前28085，四卡连接已恢复；GPU／CUDA／新价／唯一v2仍待，0新科研GPU／权威账本写。两卡15:19四小时只读、原完整24／BANK24→既定CPU诊断→完整1624／具体12批准、cap226历史与54科研行状态保持。

- [Actual CPU R2 launch](../reports/wc_four_card_BANK24_full_execution_tools_CPU_R2_launch_20261022.json)
- [One admission](../reports/wc_four_card_BANK24_full_execution_tools_CPU_R2_admission_20261022.json)
- [Technical admission boundary](../reports/wc_four_card_BANK24_full_execution_tools_CPU_R2_admission_technical_boundary_20261022.json)
- [Two once-only checks and prior automation deletion](../reports/wc_four_card_BANK24_full_execution_tools_CPU_R2_actual_two_once_checks_20261022.json)

## 2026-10-22 12:00完整工具CPU R2技术完成，独立终态待验

[635技术原件与接续](635_WC_READONLY_BUDGET_READER_FIX_AND_FULL_BANK24_TOOLS_CPU_R2_20261022.md)：11:53半程槽延后送达，实际仅于12:00:09.855954收取原R2技术状态；source6d9cd494／PID644729/start942609041／14payload与manifest一致。原worker已退出，health记录11:51:02.710220结束、wall35.577秒，报告一次提交及原句柄恢复、只读预算post、四项拒绝和真实CPU collector完成；预算与锁前后SHA／inode／mtime／大小相同，CPU容器peer／隐藏GPU与完整24未到达／0评分边界保持。这些仍为技术记录，未读取最终result／日志、终态独立哈希或运行accept，完整新机scope CPU尚未接受；11:58独立终态任务保留原句柄，按实际送达收件，不回填观察。半程bank24-full-tools-r2-cpu-halfway已完成删除，未改终态或两卡15:19四小时只读定义；0新派发／模型下载／Cosmos权重／CUDA／科研GPU／权威账本写。实际CUDA、Ada实测价格、唯一权威v2和GPU-ready仍待，原完整24／BANK24→既定CPU诊断→完整1624／具体12批准、cap226历史及54科研行状态保持。

- [One technical halfway capture](../reports/wc_four_card_BANK24_full_execution_tools_CPU_R2_midpoint_20261022.json)
- [Offline technical boundary: 36 checks](../reports/wc_four_card_BANK24_full_execution_tools_CPU_R2_midpoint_technical_boundary_20261022.json)
- [Halfway deletion and unchanged independent checks](../reports/wc_four_card_BANK24_full_execution_tools_CPU_R2_midpoint_automation_completion_20261022.json)

## 2026-10-22 12:05 BANK24四卡完整执行工具CPU已独立接受

[635完整原件与接续](635_WC_READONLY_BUDGET_READER_FIX_AND_FULL_BANK24_TOOLS_CPU_R2_20261022.md)：11:58终态槽延后，实际仅于12:05:54.420407收取原R2/source6d9cd494/PID644729/start942609041，保存原件后离线34项接受全过。原14payload／1789＋29／五生成源和registration、一次提交恢复、结清后真实CPU post／四拒绝／collector、预算与锁前后物理metadata及终态独立SHA、原worker／fixture进程／两CPU容器／FD／IPC／资源锁退出、env-runtime均接受；原R1只读预算失败和UNKNOWN原件保持。当前BANK24完整新机执行scope CPU通过，GPU边界仍为TEST_ONLY CPU fixture，全24未到达／0评分／实际GPU费0，不产生神经实验结果。96／公开14／LPIPS和已验依赖复用，无新下载或重装。实际CUDA、Ada实测价格、fresh资源及唯一权威v2写入交接仍待，GPU-ready为false；6.974166667／上限8.75只是完整保守规划。R2两次检查均完成删除，无新长CPU或GPU任务；两卡下一15:19四小时只读定义保持。后续先完成完整权威历史／活动预留／旧机不新派fence与唯一写入交接，再按真实CPU三件套及原CAL12／gate进行单次准入；完整1624还需自己的新机CPU／重价并等待BANK24完整原件和实费接受，其具体12批准不重问。原全24／四CAL gate／DEV不拟合、BANK24→既定CPU诊断→完整1624、cap226历史与54科研行状态保持。

- [Original R2 terminal](../reports/wc_four_card_BANK24_full_execution_tools_CPU_R2_terminal_20261022.json)
- [Independent CPU acceptance: all34](../reports/wc_four_card_BANK24_full_execution_tools_CPU_R2_independent_acceptance_20261022.json)
- [Complete acceptance audit](../reports/wc_four_card_BANK24_full_execution_tools_CPU_R2_complete_acceptance_audit_20261022.json)
- [Completed checks and conditional next steps](../reports/wc_four_card_BANK24_full_execution_tools_CPU_R2_completed_handoff_20261022.json)
