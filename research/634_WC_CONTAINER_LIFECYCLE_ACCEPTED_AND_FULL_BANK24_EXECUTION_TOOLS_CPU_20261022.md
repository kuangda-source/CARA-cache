# 跨容器生命周期已接受；BANK24 完整部署工具 CPU 卡

2026-10-22。继续已授权的四卡资源与执行准备，保留原 BANK24→既定 X-R／同 D 配额 CPU 诊断→完整 1624 的顺序。

## 原 R1 独立终态

原 07:25 终态槽实际 **07:31:03.886818**／unix `1792625463.8868175` 仅一次收取原 source `687ef2b88a3786b535db8377c8f0605e9430199e` 的完整终态，随后仅离线接受。**26 项全部通过**：12 payload／manifest、原 1,789＋单列 29 件 SHA、5 生成源及可逆 post／accept、真实 host／Docker PID 与 namespace／FD、正常／失败／超时全 24、明确 CPU fixture 的 wall 加法、两锁与原进程／容器／IPC 退出、原 post 失败路径全 24 未到达／0 评分、原 env／runtime 保持。

- [一次完整原件](../reports/wc_four_card_BANK24_container_lifecycle_CPU_R1_terminal_20261022.json)。
- [26 项独立接受](../reports/wc_four_card_BANK24_container_lifecycle_CPU_R1_independent_acceptance_20261022.json)。

只接受跨容器生命周期 CPU；完整新机 scope CPU、CUDA、Ada 实测价格、唯一 v2 和 GPU-ready 此时仍未通过。原所有科学／资源证明和历史失败保持，未增加 GPU 费用。

## 本次补齐的执行工具

生产入口 [wc_four_card_bank24_execution_r1.py](../scripts/wc_four_card_bank24_execution_r1.py) 提供 `launch-gpu`、只读 `recover`、一次 `capture` 和离线 `accept`。它绑定自己的完整 CPU 三件套、原 CAL12 接受与四 CAL gate、完整规划报价，以及外部独立接受的权威 v2 交接。生产代码不创建或重置账本，不接受 CPU fixture 作为 GPU 卡。

1. 持久 intent 先于一次 Popen；有 launch／fence 只恢复原句柄。明确资源忙且没有 fence 时保留原准备与完整来源，后续新槽才用新 launch ID 首次提交。控制锁覆盖授权写入与派发，避免两次调用互相覆盖授权。
2. GPU 外层仍持有原逐 UUID flock，经真实 socket peer／SCM_RIGHTS 交给容器内父进程，再实际继承给 runner。内层启动即写真实子进程 PID／start，外层确认本人 GPU 容器及内层／runner 都退出才按整个 wall 结清。
3. 后处理 watcher 只在原 GPU 父子进程和容器退出、整卡结算与原锁释放后启动。运行中、未知容器、未结算或锁仍被持有均拒绝；不能凭 host PID 文本判断容器退出。
4. 原 post 运行在 2 CPU／16 GiB、network none／readonly root／隐藏 GPU 的 CPU 容器；原 workspace 与模型／Torch 缓存只读，只写本 job／自身 cache。新 post／collector 容器也以实际 Docker peer PID／namespace 和独立观察 FD 绑定，观察 FD 不是 GPU UUID 锁。
5. 科学终态 collector 先在 host 做一次 GPU／compute 遥测与原句柄／账本观察，原任务还活时只保留技术状态；全部退出后才在上述 CPU 容器独立重读原件 SHA。保存后再离线调用精确适配的原科学接受函数，保留全 24／全部失败拒绝／36 guided／终态／actions／A_history／同 state 前 20／probe／inputhash／适用 93 RGB 和 LPIPS／六个新 Native／owner／费用与 UUID 释放。
6. 原 runner GPU 分支曾读取旧前端 CPU 文件。本次只将该部署证明读取精确可逆替换为真实新机完整 CPU 独立接受及新 registration SHA，不生成假的旧 registration 或把旧 CPU 改名为新 CPU；采样、H1／gamma、修正与 guardrail 逻辑不改。

## 新独立 CPU 卡

[冻结配方](../manifests/wc_four_card_bank24_full_execution_cpu_r1_20261022.json)，入口 [wc_four_card_bank24_execution_cpu_r1.py](../scripts/wc_four_card_bank24_execution_cpu_r1.py)。新 job 为 `wc-fourcard-bank24-full-execution-cpu-r1-20261022`；规划 300 秒，最长 1,200 秒。实际 launch 后 +120／+420 秒向上取整分钟，分别安排一次技术半程和一次独立终态。

本卡复用已接受的资源／数值／前端／组件／FD 证明与原 1,789＋29 件，只执行新增的实际 CLI schema、一次提交和原句柄恢复、结算后真实 post 容器、真实终态 collector 容器与其拒绝控制。GPU 进程及遥测边界使用明确标注、仅在 `job/TEST_ONLY` 的 CPU fixture：0 神经路径、完整 24 未到达、0 评分，CPU wall／3600 只检验加法公式，实际 GPUh＝0。保存的原 CPU 观察时间不修改；离线接受函数的 ETA 边界另用明确标注的纯函数 fixture，不当现场观察。

host 控制器仅做本人 Docker／文件／PID 协调，限制自身为两个 CPU affinity 和 16 GiB 地址空间；真正的 post／collector 都在 GPU 隐藏、离线只读的容器。没有修改共享驱动、daemon、passwd 或原环境，也没有重复模型下载／26 GB 全量哈希／旧数值与前端生产 CPU。

本地 **20 项新控制**已通过；同次相关 **60 项本地回归**包含这 20 项，其余只是回归，不计为新的生产 CPU 进度。新实际 CPU 尚待发布／单次部署，不能以本地测试称完成。新卡通过后才可能接受 `full_new_host_scope_production_CPU_accepted=true`，实际 CUDA／价格／唯一 v2／GPU-ready 仍分别待验。

## 报价与下一门

完整六 DEV × D21／A21／Native35＝18 正式＋6 warm／24、864 pairs／1,728 CFG／1 load／六新 Native 保持。完整保守规划 **6.974166667 GPUh／上限 8.75 < 12** 沿原七项×2，加容器启动退出 180 秒／计费 SM89 setup 失败余量 300 秒，再整体×1.2；它是规划，实际 Ada 时间项仍全部 null、无预留，不当实测速度。

实际 GPU／CUDA 兼容仍必须先拿到双卡完整权威 v2 历史／settlements／全部活动预留、旧机不再新派的 fence 和唯一写入权交接，再做 fresh UUID／磁盘／主存与完整余额准入。当前不复制旧 `116.825` 快照，也不免费试 GPU。缺交接继续独立 CPU 准备，不制造无用巡检。

完整 1624 原 config SHA `75338efd0d7c2d145c73bb3d5514c37fcec46851995785724eeca8f650419f9a`、4 CAL×406／14 完整路径／含 warm 2,030 格／13,020 试验和具体整卡 12 GPUh 批准保持，不重问、不拆缩；新机自己的 CPU／整卡重价／BANK24 原件与实费／权威预算门不绕过。cap226／origin79.99637737158223、全部预算历史、54 科研行与 status_counts 不变。F/B 关闭，无训练、人评、付费 VLM／OMR，不自动并主稿。两卡每四小时只读独立，本卡不追加双卡查询。
