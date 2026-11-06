# 最终共同测试seed执行桥：标量通过，完整952本地CPU在途

更新：2026-10-16。N05原1078249/1078290/post1078250、source15d77ac/完整66和今天12:05一次验收保持；本轮未查询服务器、模型进度或科学partial。

**最终共同测试需要的seed17/43执行接线已补齐，旧开发入口保持原样。** 新独立模块只放开已有执行器的预登记seed入口，并绑定实际缓存身份，支持现有WC/RA/少步Native、两个冻结候选与同26D强简单对照。五项本地控制通过；完整952条本地CPU校验已单次启动，尚未接受。当前没有新GPU视频、质量或速度结果。

## 1. 为什么需要这一步

原N05有限网格与N06简单规则入口都绑定CAL seed0，最终N07已登记seed17/43。直接绕过检查或修改sample为0会破坏最终测试；本模块保留原文件，只对两处入口seed判断做可逆的一次替换，数值执行器、Native真实更新数、阈值、掩膜、读出、guardrail和旧风险合法域保持。

- 新模块：`src/wcomr/frozen_shared_execution_r1.py`。
- seed0保留原缓存context，便于逐步对照；seed17/43创建各自的缓存context，并记录真实sample.seed。
- 主计时/请求行为仍走已接受执行器；新bridge只在请求边界回收不可达对象，保留算法实际维护。CPU观察器只用于本地验证，不安装到生产入口。
- 支持17个既有配置是执行注册表，不是将最终GPU卡扩大到17方法；N07原8prompt×2seed×10方法＝160正式＋20warm/180模板未选卡、未缩范围。

## 2. 五项已通过的标量控制

|控制|结果|
|---|---|
|完整180排程|160个正式case×method位置齐全，20warm单列；缺seed/少方法/重复方法/新P/非整数seed拒绝|
|源版本与可逆变化|两处各一次seed gate替换，逆向字节和AST与原函数相同|
|缓存身份|seed0原context保持；17/43分离；错误请求名/seed/布尔或浮点seed拒绝|
|既有方法域|全部17配置、Native36/27/19更新、同26D与A5/10/0保持|
|错误恢复|无合法guardrail时不执行；异常后原install引用恢复，无全局补丁泄漏|

原件：`reports/wc_paper_shared_execution_scalar_CPU_controls_20261016.json`。这些是接口和排程控制，不代表最终N07生产CPU已接受。

## 3. 完整本地CPU范围（已登记不缩）

|维度|完整范围|
|---|---|
|设置|WorldCache flow关闭/开启两种，四个原Toy输入|
|配置|全部17个已有有限配置，包括前密C/A|
|seed|0、17、43；0用于旧实现等价，17/43用于实际seed接线|
|audit/lean|816完整路径，408对比较|
|旧seed0控制|136完整路径；全部guided、终态、动作、A历史、来源历史和mock输出对照|
|总计|952路径、32816pairs/65632CFG|
|seed证据|真实固定sampler噪声入口记录传入seed；同seed跨方法初始噪声SHA一致，三seed彼此区分|
|生命周期|每请求释放算法组件，原网络/scheduler/RNG恢复；源与runtime一致|

CPU保留完整UniPC/RF/guarded pipeline体与声明的Toy注意力、权重、head、准备、解码和mock writer。Native使用已声明dense-WC stand-in，不是运行真实Cosmos原生类；输出mock文件不是真实视频。这一步不会挑最终输入、工作点或对手，不接T1/P-ACR，不重开F/B。

## 4. 原始准备中断与独立R2

首次全仓git archive在CPU派发前读取了530667520字节历史数据，进度很慢。已确认没有CPU launch/registration后，仅停止本任务两个Git准备进程；原archive、失败回执保留，952范围不改，也未触碰服务器任务。

独立R2只封存执行源码、测试、脚本、配置与manifest。每文件的Git blob identity与同一HEAD精确比较，再记录SHA256，不打包历史结果；这是打包修复，不是方法或统计范围的缩减。

- 原件：`reports/wc_paper_shared_registry952_source_packaging_R1_failure_20261016.json`。
- 当前source：`89381c1df7603bc9ba3e28913b043ff0dfec3e42`。
- 隔离目录：`.sync/wc-paper-shared-registry952-local-cpu-r2-20261016`。
- CPU原PID：**9614**，准入已一次确认live；当前不提前看partial。
- 完整封存payload：2269文件。
- 启动：2026-10-16T05:35:42.062574+08:00。
- 预计7—12分钟；最早查收：2026-10-16T05:47:42.062574+08:00，unix1792100862.0625741。
- **安排05:49一次查收**，此前不持续监听。

## 5. 查收和后续

```text
.venv/bin/python scripts/capture_wc_shared_registry952_local_cpu_r1.py \
 --launch-ref reports/wc_paper_shared_registry952_local_CPU_R2_launch_20261016.json \
 --output reports/新的完整952本地CPU捕获.json.gz
.venv/bin/python scripts/accept_wc_shared_registry952_local_cpu_r1.py \
 --capture 同捕获.json.gz --output reports/新的独立接受.json
```

须核对原PID/lstart、隔离source/全payload、原exit/result/失败文件、全952 mock原件、408audit/lean与136旧seed0逐步桥接、72个Native计数、全部实际seed/噪声组、掩膜与组件释放；离线从同一回执独立复算，不只接受汇总计数。若原CPU未完，按剩余工作量估时另约一次即结束，不循环轮询。失败保留，修复必须fresh版本/目录，不能改在跑源或少跑方法凑成功。

全部通过后只记“完整本地注册表CPU接受”，最终16真实请求、10冻结方法/阈值、fresh输入身份审计、真实生产CPU、完整成本和GPU仍待N05/N06后封口。常规主线<12且fresh余额/UUID通过直接执行；>=12或余额不足给具体完整卡决定，不拆缩或重置预算。

## 6. 原件

- `manifests/wc_paper_shared_registry952_local_CPU_preregistration_r1_20261016.json`
- `reports/wc_paper_shared_registry952_local_CPU_R2_launch_20261016.json`
- `tests/check_frozen_shared_execution_sampling_cpu_r1.py`
- `scripts/check_wc_frozen_shared_registry952_local_cpu_r1.py`

0新增GPUh、0SSH/账本写。原N05今天12:05、原cap104.971363333、9.5GPUh完整预留和最近可准入5.985269115快照均未重查/改写。F/B关闭，无新训练、OMR或人评。


## 7. 查收工具的独立合成控制

`reports/wc_paper_shared_registry952_analysis_synthetic_CPU_controls_20261016.json`记录完整952合成mock矩阵可接受、八项破坏被拒绝：缺seed位置、缩全路径、错误实际seed、组件未释放、Native CFG计数错误、旧seed0 context串入、结果SHA不符和原CPU仍live。测试不读取9614或其结果，合成通过不等于原完整CPU已通过。

collector另保留尚在写入JSON的parse_error及缺失源的False，避免将观察瞬间的文件状态误当任务完成。当前执行源89381c1的隔离目录不改；本地查收工具的边界修订不改数值代码、952范围或05:49时刻。
