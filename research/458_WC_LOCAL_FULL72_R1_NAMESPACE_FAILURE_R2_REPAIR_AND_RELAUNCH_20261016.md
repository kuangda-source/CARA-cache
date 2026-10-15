# 本地CPU72：R1模块装载失败定位与R2完整重跑

已定位第23步/T1执行接口完整CPU检查的首个技术问题：本地AST装载的WC/RF模块缺少源码文件元信息和一个原WC辅助函数绑定，因而被现有来源/全局校验拒绝。独立R2补齐了实际装载信息和绑定，编译控制已通过；H1/T1参数、分配执行器和完整72路径设计均保持。

**本轮没有新的方法质量结果。原失败可复核，R2完整采样仍待验收；同26D原任务与04:55安排保持。**

## 1. 原R1按时一次查收

在最早准许时刻02:26:36.917之后，只查了原PID5392一次：句柄已结束，source814b5d0的四项payload一致，exit1，耗时8.592644秒；无完整结果、mock输出0。原72计划分母保留，完整路径接受0/72。错误发生在第一个owner构建的来源校验、进入首个采样pair之前：

```text
AttributeError: module 'cpu_full_pinned_wc' has no attribute '__file__'
```

原完整回执：`reports/wc_w3_phase_runtime_local_full72_CPU_collection_20261016_0227.json.gz`；原退出、failure.json与独立终态接受均保存。没有改原目录、原失败或重新启动5392。

这次失败验证了入口仍在拒绝来源不完整的局部模块；它没有提供H1、阶段规则或T1的科学反例。原分配器、冻结参数和先前456局部结果不变。

## 2. 修复内容与编译控制

R2只修改本地CPU夹具的两处装载点：

- 给实际从绑定WC源码编译出的模块补`__file__`，并先断言WC函数`co_filename`确实来自同一源码；同时从同一原文件装载`compute_saliency_map`。
- 给从绑定RF源码编译的原类模块补`__file__`。

第一次compile-only检查进一步发现缺少`compute_saliency_map`，原全局校验继续报`Unresolved actual production global`。该检查失败也记录在R2推导回执中。随后补的是原函数，没有替换成恒等函数或绕过校验。

两处替换可逆回原R1源码，原字节与AST一致；WC/RF函数、原来源/全局守卫和算法本体不改。编译控制核对了完整WC配对/读出转换和真实RF velocity构造的源/全局绑定，并确认缺元信息、外来源仍被拒绝；0forward、0权重、0GPU。回执：

- `reports/wc_w3_local_full72_R2_metadata_derivation_20261016.json`
- `reports/wc_w3_local_R2_origins_compile_control_20261016.json`
- `reports/wc_w3_local_R2_origins_and_velocity_compile_control_20261016.json`

验收器的mock writer形状另按原inference源码校正为`[3,93,16,16]`：原`video[0]`在写盘前移除batch维，guardrail返回后为C/T/H/W。这是独立reader的布局纠正，没有改变运行中的CPU或视频管线；证据在`reports/wc_w3_local_CPU_mock_shape_reader_alignment_20261016.json`。

## 3. 新R2完整任务

新源 **c3742059b136310ed73efacb6c838a3efbe5ccab**；分配执行器仍是814b5d0中已过六项标量控制的同一份代码，H1与T1指纹不变。新目录`.sync/wc-phase-runtime-local-r2-20261016`只复制了同SHA的9份绑定源码，原R1目录保留。

原完整设计不缩：两flow×四Toy请求×H1原集/H1-CAD/仅第23步/T1-CAD×audit/lean＝64路径，另8条旧H1完整控制，共72路径、2592pairs/5184CFG。每个配置重置所有请求状态；预期32组audit/lean、8组旧H1全36guided/终态/动作/A历史/mock输出等价，以及所有owner释放。第23步与T1允许改变实际后续轨迹，不以等于原H1作为它们的验收要求。

本地PID **5826**于 **2026-10-16 02:32:10.360859** 单次派发并确认存活。预计5—10分钟；最早查收 **02:42:10.360859**，约 **02:44一次查收**，不持续监听。

```text
.venv/bin/python scripts/capture_wc_w3_phase_runtime_local_cpu_r1.py \
  --launch-ref reports/wc_w3_phase_runtime_local_full72_CPU_R2_launch_20261016.json \
  --output reports/新的R2完整捕获.json.gz
.venv/bin/python scripts/accept_wc_w3_phase_runtime_local_cpu_r1.py \
  --capture reports/该R2捕获.json.gz --output reports/新的独立接受.json
```

查收必须覆盖所有72位置、32mock配对与8旧H1控制、真D来源保持及实际第23步D→A覆盖。若没有覆盖某个新动作，只接受已有范围并明确缺口；失败/缺失不填成成功。若仍在运行，只重新估时约一次并结束。捕获后分析错误仅离线处理同一回执，不重复采集。

## 4. 接续与必要边界

这是本地Toy完整接口准备，仍使用显式Toy权重、attention、prepare、decode、mock writer；补元信息不等于真实生产环境导入。尚无服务器生产CPU、真实新策略视频、LPIPS或延迟结论。完整检查通过后，才继续准备实际生产入口和具体视频卡。

本轮0SSH/0新teacher/0拟合/0GPU/0账本写。原同26D0795a00、1040857/1040918/post1040858、GPU0及04:55一次验收不改，也未读其科学partial。先验收当前两项，再结合结果决定原H1/第23步/T1的完整视频范围、报价与fresh准入；F/B关闭，不引入人评、生成器训练或OMR。
