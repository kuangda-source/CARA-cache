# CARA同卡进程身份、价格信任与后续顺序

## 当前实际观察

原1624最新于2026-10-23 **04:01:26.333449 Asia/Shanghai**恢复原句柄检查：13/14条路径完成、最后`formal_3_COLLECT`运行、0未到达、0失败。原supervisor、runner及容器仍存活，日志未发现错误。此前03:43:00检查为11/14完成。唯一launch仍为`37ab7e89-952b-4ddb-acde-5b20a0fc1295`；本轮没有GPU提交、终态接受、价格科学分析或改动远端stage。

- [原任务技术回执](../reports/wc_policy_assets_full1624_fourcard_GPU_authorized_followup_20261023_0343.json)
- [恢复后的最新原句柄回执](../reports/wc_policy_assets_full1624_fourcard_GPU_recovered_20261023_0403.json)
- [账户与独占能力回执](../reports/wc_four_card_GPU_exclusive_capability_and_competing_account_20261023.json)，实测03:43:59.432799。
- [此前半程与预算](647_CARA_FULL1624_HALFWAY_AND_SHARED_GPU_PRICE_CAVEAT_20261023.md)；原全程检查仍为08:26。

GPU3（UUID `GPU-d4868f0a-29df-9077-82db-77f7bf0f9934`）上的新增进程属于**服务器账号`guanwenfei`，UID1005**，PID848535，父PID848529，显存13408 MiB（13.09375 GiB）。进程启动时间约10月22日23:25:44；启动时间不能证明它首次使用GPU的时刻。账号映射不证明实际操作者身份。我们的runner为PID811944、UID1000，start_ticks946345336。没有查看他人代码/数据，没有通知对方，也没有终止任何进程。

## 对此次验收的影响

同卡并行主要使动作时间和端到端速度缺少独占条件，实际GPU占用时长也可能增加。完整数值标签、视频原件和控制相等仍按原验收器核对：通过则保留，不因竞争一概作废；未过则保留失败。当前仍在跑，尚未完成最终接受或结算。

价格审计入口已新增：`scripts/audit_wc_policy_asset_prices_r1.py`，仅消费原终态完整接受的原件；明确区分112个三轮重复格与1512个单轮正式格，检查波动、顺序和max-source聚合。已知竞争的原价格不会因低CV自动被认证。原`generator_input_ready`也不能单独放行PG-P1。

当前账号无免密修改计算模式权限、所有卡为Default且均在使用。随后用已授权四卡登录凭据完成只读sudo命令权限检查，确认可以修改指定UUID计算模式，[权限回执](../reports/wc_four_card_exclusive_sudo_authority_readonly_20261023.json)。新增只读独占检查工具`scripts/check_wc_four_card_exclusive_r1.py`；新GPU实验要求真正的设备独占/管理员调度，并在启动前后验证原runner身份。**当前没有启用硬件独占**；须等空闲后实际验证支持并设置，不能用项目文件锁冒充跨用户隔离。

只读准入工具首次遇到SSH 255，保留UNKNOWN回执；本机原master PID42963与socket均已消失。沿已有四卡私有凭据恢复master PID56689，并配置ServerAliveInterval=30、ServerAliveCountMax=3、ControlPersist=50400，未重派GPU。实际模式查询恢复后再次确认原runner和外部PID同卡。初版检查暴露两机墙钟偏差，freshness改为同步查询完整monotonic往返上界；不修改原服务器观测时间。网络恢复回执文件名中的0404是标签，实际恢复时间以`observed_unix=1792699173.2237399`为准。

## 已准备的接续

[后续完整方案](../plans/cara_policy_generator_20261020/PRICE_HISTORY_NATIVE_CONTINUATION_R1_20261023.md)：先原1624完整接受，再动作价格审计及独占测量补救，然后PG-P1/P2。增加冻结策略后的有限历史窗口诊断和少步Native等时间对照，新增范围计入新整卡报价，原运行中12 GPUh卡不改变。

本地7项测试覆盖完整分母、warm排除、缺失/非法计时、重复轮次漂移、Default/MPS/占用/陈旧快照拒绝、runner PID/start/UID精确绑定，以及原终态哈希和竞争回执的launch绑定。它们验证审计和准入逻辑，不代表真实价格或硬件独占已接受。
