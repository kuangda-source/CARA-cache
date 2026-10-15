# N05强基线：有限网格接线与完整CPU216在途

主线强基线比较已从待办清单进入实现验证：固定Native三种采样次数、WC/RA各三个阈值，以及两个原冻结工作点。真实UniPC/Karras的CPU展开已接受；新执行入口及完整两flow、四Toy输入的216路径检查已单次派发。

本轮尚无新的模型视频、质量或加速结果，原同26D04:55验收安排保持。

## 1. 固定的完整比较范围

`WC-PAPER-N05-CORE11-CAL4-FULL66-R1-20261016-A`为11配置×四原CAL seed0，44正式＋22完整预热，一次模型加载，2220配对更新／4440CFG。Native35输出为各方法保真参考；四输入、全部网格点和失败分母均保留，不按场景选赢家。

- Native requested steps：35、26、18。
- WC阈值：0.03、0.06、0.12。
- RA阈值：原0.070744235098772的0.5、1、2倍；不重新拟合校准。
- Ours：冻结A_NO_P和TABLE_PHASE_H1，原β1阶段/λ/gamma/读出/费用表保持。

完整核心范围在新输出前登记为`manifests/wc_paper_N05_core66_preregistration_r1_20261016.json`。直接修正近邻仍待Cosmos忠实适配，未被删除或伪装成完成：GP-Refiner当前作者仓库empty；AdaCorrection伴随实现注册Flux/PixArt，未知类返回原transformer，不能将未经适配的调用当作Cosmos比较。先推进已有实现的完整核心问题，近邻缺口继续保留；不是按12GPUh阈值删配置或缩已在跑的卡。

## 2. 已接受的真实采样网格CPU

本地执行了固定SHA的原`FlowUniPCMultistepScheduler`，Karras开启、原构造参数与模型工厂一致，逐更新调用真实solver并检查有限终态。

|requested steps|实际更新|CFG调用|
|---|---:|---:|
|35|36|72|
|26|27|54|
|18|19|38|

原件：`reports/wc_paper_N05_actual_native_scheduler_grid_CPU_20261016.json`。它证明采样网格与数值solver入口，尚不证明少步生成的质量和费用。

原clean executor硬编码35/36，新增`paper_baseline_grid_r1`只对Native的请求域、末步捕获和完整调用检查做四处可逆替换，逆向字节及AST均等于接受版本；官方Native forward选择、guardrail、pipeline、解码、写盘延后和计时边界沿用原实现。WC、RA和两个Ours直接调用原已接受执行器。新记录核对真正安装到net/RA controller的阈值，原共享配置不改；第一/最后block检查Native两分支全算。

三项标量/网格控制通过。原数值模块和运行中的同26D源码未修改，不能将短控制当作完整采样或生产CPU通过。

## 3. 完整本地CPU216

冻结源`762aeb4e010e3b297b23fd8e2f2f91feedd2abc7`；新本地目录`.sync/wc-paper-n05-core216-local-cpu-r1-20261016`，PID **6663**，启动 **2026-10-16 03:04:48.784847**，单次派发后确认原句柄存活。

两flow×四Toy请求×11配置×audit/lean＝176路径，另40条旧默认方法完整控制，共 **216路径、7360pairs／14720CFG**。Native边界仍显式使用旧CPU夹具的dense stand-in；实际生产必须使用经校验的原模型类forward，不把Toy控制冒充真实骨干。

需核对88组audit/lean、40组旧默认完整36 guided/终态/动作/A历史/mock对照、全部216 mock、真实安装阈值、三个Native更新计数、组件释放和初始状态恢复。拒绝或错误按原分母保留，不缩场景/配置或换样。CPU运行使用独立复制的相同SHA运行时，不修改已完成本地72或服务器stage。

预计3—6分钟，最早查收 **03:10:48.784847**，约 **03:12一次查收**，不持续监听：

```text
.venv/bin/python scripts/capture_wc_paper_N05_core216_local_cpu_r1.py \
  --launch-ref reports/wc_paper_N05_core216_local_CPU_launch_20261016.json \
  --output reports/一个新回执.json.gz
.venv/bin/python scripts/accept_wc_paper_N05_core216_local_cpu_r1.py \
  --capture reports/该回执.json.gz --output reports/一个新独立接受.json
```

捕获一次后只离线分析同一回执。未完按剩余量另约一次并结束；技术错误保留，修复用独立新源/目录。不得先看结果文件或因解析错误重复采集。

## 4. 接续与费用

当前仅本地CPU，0SSH、0GPU、0权重、0新teacher、0账本写。完整GPU66尚未生产CPU/实际入口与终态审计封口，未启动；约8.56855GPUh仍是准备forecast，不当作准入或实费。

CPU全部接受后继续实际生产入口、全部66位置的post/费用/启动接线，保留本轮原方法与全部有限网格。原同26D0795a00/1040857/1040918/post1040858依旧**04:55一次验收**，此前不查询它的partial或改任务。N06完整接受后，N05按fresh v2总余额、UUID锁与完整forecast准入；严格<12GPUh已获自主授权，达到12或总余额不足交付具体整卡决定，不拆缩或重置窗口。

N05核心结果不等于直接近邻或最终冻结测试已完成。F/B继续关闭，P/T1增强后排，不新增人评、生成器训练或OMR。
