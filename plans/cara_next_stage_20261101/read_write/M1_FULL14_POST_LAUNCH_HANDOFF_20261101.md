# M1完整14：原已启动运行承接

唯一run `cara-read-write-M1-full14-r1-20261101`，launch `7949388215944eb98c7f64f21e8e1dd1`，source `b930df4b04a0924d8bea0af32c0f7aaf8c33a5c8`。只恢复原stage/容器/PID-start ticks，不再GPU dispatch、source prepare、storage launch、换卡或修改运行中源/配置。用户已允许本卡原四卡中央账本读取/预约/实耗结算；不允许四卡实验或账本迁移。

## 原身份、时间与范围

- stage `/data20t/gaokuangda/worldcache_workspace/.sync/cara-read-write-M1-GPU-a6000-full14-r1-20261101`。
- 两卡原A6000 `GPU-cebf7119-cf03-23b9-e192-cd196332b704`；container `cara-read-write-M1-GPU-a6000-full14-r1-20261101-gpu`。
- 原launch SHA `0be9dc301d6762e08a538e27de48c8b86182f175a77405ada41eff39f1109b46`；注册SHA `2def9cdcb04c20b96977c6f82ad728cebf42e67907048a650238d2ba9f9bbd5e`。
- guardian PID2919359/ticks682506757；container CLI2919446/682506947；supervisor2919504/682506989；runner2919548/682507135。完整boot/namespace/command SHA见原接受回执。
- 原guardian实际开始 **2026-11-01 18:49:24.756352 Asia/Shanghai**；硬1.95GPUh，原硬截止 **20:46:24.756352**；**20:36:24.756352**开始停止释放余量。硬截止不能后移。
- 完整14请求/504 solver更新/512paired/1024CFG；两旧FIT、seed0、第8更新；八四格科学输出、四独立等价控制、两新Native。全部93帧。
- 2CPU/40GiB同额memory-swap上限，独立16GiB输出/48MiB跨盘journal，90°C，cap226及旧16.5责任。原single-runner CUDA/EXCLUSIVE_PROCESS已核对。

起点：[actual start](../../../reports/cara_read_write_actual_start_accepted_r1_20261101.json)、[原status](../../../reports/cara_read_write_original_start_status_r1_20261101.json)、[原中央预约](../../../reports/cara_read_write_central_reservation_r1_20261101.json)。实际开始后安排同一半程19:38、同一终验20:28；实际automation ID为半程`m1`、终验`m1-2`，原定义SHA见`reports/cara_read_write_acceptance_schedule_r1_20261101.json`，不创建重复监控。

## 只恢复、完整收尾

1. `scripts/cara_read_write_control_r1.py status --output 新唯一回执`只读原句柄、14分母运维计数、GPU温度/显存/独占、资源和原账本。禁止部分T_DD、科学分数/曲线或择优挑角。连接UNKNOWN继续恢复原句柄，不能重派。
2. 仍活跃时保存一次运维观察。半程可仅据完整/剩余路径计数和实际墙钟前移**同一个**终验；不改原GPU截止、不新建重复检查。终验仍活跃则调整同一终验继续接受。
3. 原GPU结束后，先用status返回的原lifecycle终态，`settle --input 该原status回执 --output 新回执`完成唯一guardian全段实际费用。失败也结算。事务UNKNOWN先`central-recover`，不得重复收费；不得把supervisor区间另收费。
4. 仅原完整14正常终态、进程/锁释放、Default恢复且实际费用已结算后，保存`reports/cara_read_write_final_original_r1_20261101.json`和`reports/cara_read_write_final_settlement_r1_20261101.json`原字节。不要重新生成GPU原件。
5. 使用`scripts/cara_read_write_accept_transport_r1.py artifacts`只派一次有界CPU读者，接受完整14、00对独立Uniform/11对独立D8的四组完整latent/93RGB等价。活跃只`capture`。接口异常可修外部CPU接线并保留原失败，不能改原GPU源、生成原件或重复已接受评分。
6. 四等价门与完整工件通过后，`score`唯一八对新Native参考Fidelity-v2；CPU活跃仅`capture`，禁止重评分A32/B36/E1或自动重派此评分。完整八对接受前不作科学结论。
7. 保存完整接受的八对原件后，用`scripts/analyze_cara_read_write_complete_r1.py --accepted 完整接受JSON --output 新分析JSON`分析逐输入、等权均值及全93帧read/write/interaction。其三个签名/分母CPU控制已通过；分析源码单独版本化，GPU源b930df4b保持。
8. 更新canonical、原件SHA、图表与研究记录，精确提交推送；保留旧A32/B36/S/Q/搜索/E1冻结、WC/RA FIT UNMATCHED、旧CAL及最终16/备用16保护。成功全链接受或真实失败完成释放/结算后删除半程和终验；不自动下一GPU卡。

CPU评分环境仍复用原离线Alex/PIQ原权重，不下载。M1只识别同父读/写/交互在一个固定位置的效果，不直接建立部署速度、泛化或整个主方法有效性；M2配方与read-only消融另行完整预注册。

连接使用原Tailscale私有ProxyJump配置和gaokuangda/docker受控角色。纯SSH默认group可能不能inspect Docker；不得据此把原容器说成不存在。保留原两层ControlMaster=no/ControlPath=none，不改Windows/Clash/路由或服务。

## 19:38半程已处理

[半程原状态](../../../reports/cara_read_write_halfway_original_status_r1_20261101.json)于19:38:48回读7/14完整、1运行、6未到达、0技术失败；原四PID/start ticks均存活、原runner独占、67°C。独立[中央只读](../../../reports/cara_read_write_halfway_central_status_r1_20261101.json)确认原1.95预约保持，cap226、used194.03986128165678、reserved18.45、旧16.5不变。未看部分科学分数/时延，未结算活跃运行。

[半程接受](../../../reports/cara_read_write_halfway_accepted_r1_20261101.json)后已删除m1；[检查R2](../../../reports/cara_read_write_acceptance_schedule_r2_20261101.json)保留同一m1-2于20:28，原定义SHA不变。按计数/墙钟无需前移，未新建检查、未延长硬截止。若遇已排队的旧半程消息，复用此原件，不重复半程动作。

M2仅独立CPU准备：[固定源码缓存导数与实现安排](M2_ADJOINT_IMPLEMENTATION_AND_HARD_ACTION_PLAN_R1.md)。其新源和CPU stage不改变本M1的b930df4b源/容器/配置；后续卡不继承本卡账本许可。
