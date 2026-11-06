# SM89 执行组件接受；BANK24 跨容器生命周期 CPU 卡

2026-10-22。继续用户授权的四卡执行准备，原 BANK24／1624 顺序、科学 scope 和预算批准不变。

## R1.1 完整接受

06:47 时点按原句柄只做一次终态收件，保存原件后离线独立接受，20 项全部通过。原 source `a3cfddd9dafe3eb885e8e650aa1212e6dcd764c9`、manifest、全部 payload、原 1,789 件及单列 29 件元数据、真实输入 fingerprint `6ff3902a8a6272529ad5ad558699b994be1940b7efa1de24adfd37cae0aad90e`、三个生成源、原进程／容器／资源锁退出、env／runtime、只读离线与隐藏 GPU 均一致。原 21 项内存 reserve／settle 控制通过；完整新机 scope CPU、实际 CUDA、Ada 实测价格和 GPU-ready 仍为 false。

- [完整原件](../reports/wc_four_card_BANK24_execution_adapter_CPU_R1_1_terminal_20261022.json)。
- [20 项独立接受](../reports/wc_four_card_BANK24_execution_adapter_CPU_R1_1_independent_acceptance_20261022.json)。

原 R1 控制面预检失败保持。原 06:43 半程若未执行，其原因已被完整终态接受取代，删除过期自动化，不回填半程观察或重复 SSH。

## 新 CPU 卡的必要性

原 host FD 和 PID 不能直接填给 Docker 内的 runner。新实现使用本人短路径文件系统 Unix socket，以 `SCM_RIGHTS` 传递**同一个 flock 的文件描述符**。host 保持原 FD；容器 supervisor 将接收的 FD 真正继承给 runner。Linux socket 长度受限，因此本人临时 IPC 目录只建在 `/tmp/wc-bank24-fd-<job hash>`，0700、容器只读挂载，结束仅清理本人该目录。无需网络代理或共享 daemon 修改。

本 job 显式使用 `--pid=host`，只核对本人的 PID／start ticks。host 用 socket `SO_PEERCRED` 对照实际 Docker PID 和 manifest label，核对相同 PID namespace，不能拿文本 PID 当继承证明。CPU 容器保持全部 GPU 隐藏、network none、readonly root／workspace／Torch 缓存和 2 CPU／16 GiB。

## 完整 CPU 范围

[可执行配方](../manifests/wc_four_card_bank24_container_lifecycle_cpu_r1_20261022.json)，入口 `scripts/wc_four_card_bank24_container_cpu_r1.py`。

1. 复用已接受的 R1.1／前端／原数值依赖，仅按原 SHA 从服务器复制 1,789＋29 件输入，不重下模型或重跑旧数值／前端／资源 CPU。
2. 实际跨 host 与 CPU 容器传递 FD，核对 socket peer＝实际本人 Docker PID、原 inode／device、PID namespace 与独立打开文件的 flock 拒绝。真实子进程再核对 `getppid`、继承 FD 与同一锁。
3. 用同一个生产子进程启动／超时函数执行三类**明确标注的 CPU 生命周期控制**：正常访问 24 项、第三项失败、超时；完整分母分别保留 24／24／24，后两项保留 21／24 个未到达。它们不执行神经轨迹、不生成视频或质量字段。
4. 真实测试目录 `job/TEST_ONLY` 内，用原预算事务方法做三次整卡预留和实际 CPU wall 的加法结算，验证退出释放。`fixture_wall/3600` 只核对费用公式，**实际 GPUh 为 0**；不打开或写入权威账本，不是新可用余额。
5. 原 GPU runner、post 和独立终态接受函数只做精确可逆的主机／路径／新旧 source 身份替换。保留全 36 guided／终态／actions／A_history、四 probe／同 state 前 20、93 RGB／全部适用 LPIPS、Native 与 owner 审计代码。
6. 真正运行发布后的 post 代码的**失败路径**：依赖边界使用明确的 CPU fixture，原始 runner 没有任何神经输出，必须保留全部 24 个 `NOT_REACHED_RETAINED`，0 视频／0 评分；不能填零质量或从子集接受。此项不宣称实际 93 帧或 LPIPS 被本卡重新验过。
7. 实际 GPU 入口继续拒绝缺完整 scope CPU／唯一权威 v2 交接。仅有上述前端或组件接受不能开 GPU。

本地 16 项有界控制已通过，涵盖整卡报价缺项／NaN／拆范围拒绝、完整分母与失败保留、本人超时进程组停止、可逆生成源、实际 authority 缺口／历史截断拒绝、短 socket 路径和原 stage 恢复。Mac 不能代替 Linux 跨容器核对，必须 GitHub 发布后在四卡实际运行。

## 保守整卡规划报价

完整 BANK24 保留六 DEV × D21／A21／Native35＝18 正式＋6 warm、24 路径、864 pairs／1,728 CFG／1 load／6 Native。原七项整卡时间项各乘 2，再加容器启动退出 180 秒和计费 SM89 setup 失败余量 300 秒，整体再乘 1.2，规划 **6.974166667 GPUh**，完整上限 **8.75 GPUh < 12**。这只是保守规划，非新 Ada 实测或速度结果，实际新机时间项仍全部 null，原八项待测价格不覆盖。失败或超时也计入整个 GPU 容器 wall；没有免费 GPU 兼容性 probe。

此次仅 CPU，0 GPU／0 预留。规划报价将和完整实际 CPU、权威账本、fresh UUID／磁盘／主存共同进入后续完整卡准入，不能因严格小于 12 就绕过其余门。上限保护不保证实际算法／硬件一定成功。

## 单次部署与查收

新 job：`/data20t/gaokuangda/worldcache_workspace/bootstrap/wc-fourcard-bank24-container-lifecycle-cpu-r1-20261022`。规划 300 秒，最长 900 秒。已有 stage 仅恢复原句柄，不重复派发。实际启动后一次 admission；以实际 start+120 秒和 start+420 秒向上取整分钟，分别约一次技术半程和终态。原件保存后离线 `accept`。未知不当未启动，失败保留原件，以新版本只修真实问题。

SETUP 只在同一次 CPU 部署中读取 Docker runtime 名称，记录是否注册 NVIDIA runtime；它不读取 GPU 状态或初始化 CUDA，也不修改 daemon／驱动。如果缺 runtime，GPU 门继续关闭。

## 接续与边界

本卡通过只能称跨容器生命周期 CPU 接受，`full_new_host_scope_production_CPU_accepted=false`：仍需将真实 GPU 一次派发 CLI、post watcher 和科学终态 collector 的容器绑定全部接通并另做完整 scope CPU。当前生成的原 post／accept 科学审计代码保持，可直接复用；不要再次导入资源或重跑已验组件来冒充这项缺口。

实际 GPU 入口必须取得双卡权威 v2 全历史／settlements／全部活动预留，旧机不再新派的 fence，以及唯一写入权交接。当前没有该证据，不能用旧 `116.825` 快照初始化四卡账本；新入口读取真实交接并验证历史不截断。cap226／origin79.99637737158223 保持。两卡每四小时只读自动化独立，本任务不额外查询双卡。

完整 BANK24 原件／实费接受后，仍接既定 X-R／同 D 配额 CPU 诊断，再接原 config SHA `75338efd0d7c2d145c73bb3d5514c37fcec46851995785724eeca8f650419f9a` 的完整 1624 卡；具体整卡 12 GPUh 已批，不重问、不拆缩。F/B 关闭，无训练、人评、付费 VLM／OMR。54 科研行和状态不变，不把本卡写作科研结果。

## 实际单次启动与查收安排

新 source `687ef2b88a3786b535db8377c8f0605e9430199e` 已 GitHub 发布。实际于 **2026-10-22 07:17:01.510432**／unix `1792624621.510432` 单次启动，supervisor PID `629593`／start `940968487`，worker SHA `c1336cd2b3a34dc1048c6d96e6af8ffb2f350abcb4d1762a2bc70e62c7b21385`，manifest SHA `bfcdf06c73f45c3800811ff1d6e6384c036b3826ad087e3abdfe48b9da22bfb2`。实际从服务器复用全部 1,789＋29 件源文件，无基础包／模型重传。

07:17:36.219252 的一次 admission 已保存，20 项身份与技术边界核对通过。原进程和本人容器已退出，health 报告 CPU **25.091993 秒**通过：真实 host/Docker peer PID 和 FD／inode／namespace 核对通过，三个真实子进程场景分别访问 24／3／0 项，完整保留 24／24／24，后两者保留 21／24 未到达；原 post 失败路径退出 0、完整 24 未到达、0 评分且未填质量。尚未做终态独立源 SHA／锁释放验收，因此 `container_lifecycle_CPU_accepted=false`，完整新机 scope／GPU-ready 仍 false。

同次 SETUP 实际读到 Docker runtime 名称含 `nvidia`，仅接受已注册这一资源事实，不充 CUDA／模型兼容。部署前磁盘 344,004,132,864 字节、MemAvailable 68,055,384,064 字节，仅为本 CPU 准入，不当后续 GPU fresh 准入。

- [实际 launch](../reports/wc_four_card_BANK24_container_lifecycle_CPU_R1_launch_20261022.json)。
- [一次 admission](../reports/wc_four_card_BANK24_container_lifecycle_CPU_R1_admission_20261022.json) 与 [20 项技术边界](../reports/wc_four_card_BANK24_container_lifecycle_CPU_R1_admission_technical_boundary_20261022.json)。
- [两次检查实际读回](../reports/wc_four_card_BANK24_container_lifecycle_CPU_R1_actual_two_once_checks_20261022.json)：`bank24-fd-cpu` **07:20** 技术半程（最早 07:19:01.510432），`bank24-fd-cpu-2` **07:25** 独立终态（最早 07:24:01.510432）。即使早完成也不提前接受或重派。

原 `bank24-sm89-cpu-r1-1-2` 的完整组件接受原因已完成，新真实检查安排并读回后已删除。原半程过期删除，不回填观察；两卡四小时只读自动化保持。

按本机存储约束，在原 1,789＋29 全件已独立 SHA 接受且服务器复用后，清理本任务本机重复的代码输入／生成副本 **46,023,934 字节**，两个 SHA 源归档、Git 和所有原件保留；不触碰任何模型／凭据／原失败外盘 prefix。见 [清理回执](../reports/wc_four_card_BANK24_container_lifecycle_CPU_R1_local_redundant_code_copy_cleanup_20261022.json)。

## 07:20半程槽延后，实际07:26一次技术收件

实际 **2026-10-22 07:26:53.919197**／unix `1792625213.919197`，只执行一次原 R1 句柄的 `capture --kind halfway`。原 source、12 件 payload、manifest、host PID／start 和 Docker peer／FD 记录一致；20 项技术边界核对通过，health 仍报告原 CPU 25.091993 秒 PASS，原 supervisor 和本人容器退出。三个场景全 24 分母、21／24 未到达保留、原 post 失败路径全 24 未到达／0 评分和 env／runtime 保持。

本次未读取最终 result、日志、终态独立哈希或运行 `accept`，因此跨容器 CPU 的独立接受仍待原 `bank24-fd-cpu-2` 终态收件；其 **07:25** 原计划／最早时点与句柄保持，不在半程任务中代收或回填观察。本次半程原因完成，已删除 `bank24-fd-cpu`。

- [一次半程原件](../reports/wc_four_card_BANK24_container_lifecycle_CPU_R1_midpoint_20261022.json)。
- [20 项技术边界](../reports/wc_four_card_BANK24_container_lifecycle_CPU_R1_midpoint_technical_boundary_20261022.json)。
- [半程删除与原终态保持回执](../reports/wc_four_card_BANK24_container_lifecycle_CPU_R1_midpoint_completed_final_handoff_20261022.json)。

完整新机 scope CPU／实际 CUDA／Ada 实测价格／唯一权威 v2 交接和 GPU-ready 仍未通过；本次无新派发、下载、模型加载、CUDA、科研 GPU 或权威账本写。两卡每四小时只读、原 BANK24→既定 CPU 诊断→完整 1624／具体 12 批准、cap226 历史及 54 科研行状态保持。

## 2026-10-22 跨容器CPU26项独立接受，接完整部署工具CPU

[634实际接受与新卡](634_WC_CONTAINER_LIFECYCLE_ACCEPTED_AND_FULL_BANK24_EXECUTION_TOOLS_CPU_20261022.md)：原07:25槽实际07:31:03.886818仅一次完整收件，source687ef2b8的26项独立接受全过，原1789＋29／五生成源、真实FD与Docker PID、全24失败保留／0评分、两锁／IPC与原进程退出、env／runtime保持。继续补齐一次GPU派发／原句柄恢复、结算后CPU post和host-PID绑定终态collector；20项新本地控制及相关回归通过，新scope CPU配方已冻结，须GitHub发布后单次实际运行，不以本地通过替代生产验证。原GPU分支改读真实新机完整CPU证明，不伪造旧注册；完整24与科学逻辑不改。保守规划6.974166667／上限8.75<12仍非Ada实测，完整scope CPU／CUDA／实际价格／唯一v2和GPU-ready仍待，0科研GPU／权威账本写。两卡四小时只读、BANK24→既定CPU诊断→完整1624／已批12、cap226历史及54科研行状态保持。

## 2026-10-22 完整BANK24执行工具CPU08:01单次启动，08:06／08:09查收

[634实际原件与接续](634_WC_CONTAINER_LIFECYCLE_ACCEPTED_AND_FULL_BANK24_EXECUTION_TOOLS_CPU_20261022.md)：原跨容器CPU已26项独立接受。新sourcea25ae777的完整部署工具CPU于08:01:40.854244单次启动PID632076/start941236421，复用原1789＋29／模型和全部已验依赖；一次admission20项身份／技术边界核对通过，实际CLI帮助0／缺参拒绝2、原env和2CPU16GiB限制保持，08:01:50观察原worker活、进入一次派发与结算后真实CPU post阶段，未终态接受。已读回唯一新ID bank24-full-tools-r1-cpu-halfway于08:06技术半程（最早08:03:40.854244）、bank24-full-tools-r1-cpu-terminal于08:09独立终态（最早08:08:40.854244）；创建延后只向后排，不回填观察。原bank24-fd-cpu-2原因完成已删除，避免历史ID碰撞的短别名也已替换删除。完整scope CPU／实际CUDA／Ada实测价格／唯一v2和GPU-ready仍待，0新科研GPU／权威账本写；保守全24规划6.974166667／上限8.75<12非实测。两卡四小时只读、原BANK24→既定CPU诊断→完整1624／已批12、cap226历史及54科研行状态保持。

## 2026-10-22 11:07终态收件认证受阻，11:30恢复本人连接后续收

[634本次原件与恢复安排](634_WC_CONTAINER_LIFECYCLE_ACCEPTED_AND_FULL_BANK24_EXECUTION_TOOLS_CPU_20261022.md)：原08:09终态槽延后送达，实际11:07:53.556405仅一次原句柄收件，SSH退出255／Permission denied (publickey,password)，未取得当前远端PID／阶段／源码或终态；该时间为本地原件保存时间，不当远端观察。随后只读本机核对确认原SSH master PID85709与专用control socket均不存在；原收件器复用丢失连接后转为BatchMode认证被拒绝，不能据此判原CPU失败或退出。未追加SSH、重派、读取原CPU result／日志、运行accept、查询GPU或写账本。保留原UNKNOWN并将同一终态自动化改为11:30一次恢复接续：先恢复本机已授权私有SSH连接，再用新唯一文件收取原sourcea25ae777／PID632076/start941236421结果，不改旧job／科学闭包／FRPC或他人任务，不回填08:09观察。11:30是连接恢复收件时点，非worker ETA；完整scope CPU／CUDA／Ada实测价格／唯一v2和GPU-ready仍待。已验资源及完整24范围、两卡每4小时只读、BANK24→既定CPU诊断→完整1624／具体12批准、cap226历史及54科研行状态保持。
