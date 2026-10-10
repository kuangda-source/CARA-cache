# P0 实际轨迹执行核心与近似来源管理（2026-10-10）

上一批[232真实结果](232_WC_P0_COMPLETE_REAL_GROUP_RESULTS_20261010.md)说明部分更新能接近同状态完整计算，而当前整组节省有限。本轮补齐由诊断输出到真实返回轨迹的必要接线：P更新实际工作缓存、实际post-RF输出进入后续latent；真实D校准历史和近似来源保持分离。它属于已批准三模块计划内的部署开发，不缩小或替代等待确认的RA＋A完整32路径卡。

## 已实现的执行边界

新增`partial_mlp_deployment.py`复用冻结WC/RF观察编译器和`PartialMLP`，原source/283载荷不改。首版固定C/P/D执行规则只作接口控制，不宣称RA来源感知策略已有：C正常读工作缓存；P执行原深层/头/RF，选定四层实际gather→MLP→scatter并写近似工作来源；D全算并更新D-only标量校准。两probe在选择P前支付，mask仅用实际过去投影layout和固定随机/轮换规则。P实际调用旧DD继续体，但记录语义PP；不得把这个实现细节当真实D。

P来源即使年龄0、全token重算或安全full fallback仍记录`UNKNOWN_NOT_ZERO`及非零风险来源，`RA_zero_risk_reset_allowed=False`。只有实际D可以进入`ResidualCalibrator`；近似工作来源、D-only锚点、MLP逐token来源分开。原native窗口/flow/gate/head/RF保持。周期35计数归0后显式清掉本owner工作/D/投影库存，36新D初始化；条件、噪声、参数身份/版本或latent layout改变时拒绝旧owner，需新请求。第二分支异常回滚投影事务、未提交来源/D历史，并poison整个pair，不能宣称任意WC/solver故障恢复。

## 原范围完整CPU验证已登记

`manifests/wc_p0_deployment_core_cpu_r1_preregistration_20261010.json`绑定68源码，真实固定WC/RF及完整Block/GPT2FeedForward类体；声明CPU小权重、tiny attention/head、Toy latent update。保持28层、选四真实层下标4/10/16/22；小输入128token，block16，50%/75%实际64/96行。这里不运行UniPC、真实Cosmos权重、视频或GPU。

两种flow各保留source D6、在四P点实际D参考、OFF、dense维护控制、随机/轮换两密度、全行P来源控制，以及四条独立部分输出参考；共**26完整36步路径／936pair／1872普通net／962张量实际重读**。独立参考完整算MLP再替换inactive过去投影，只有被测候选必须在两个Linear前gather；它只是CPU正确性参考，部署没有免费teacher或额外头。全行P须与真实D参考输出相等且保持P来源；OFF与dense维护须与源完整相等。两flow分别追加step30 branch1故障，计划完整36、成功29分母保留。全部路径和各P机会实际Linear行数、条件/源、周期和失败poison完整检查，不以成功子集通过。

本地AST与全部68绑定通过，真实服务器CPU尚待。完整RA＋A283绑定经重读未变，仍5.147707517GPUh>4具体确认待；本CPU不拿GPU锁、不初始化CUDA、不写预算，也不生成新的GPU卡。累计34.372880296/77.895246590、窗口余43.522366294、72历史提交保持。CPU只进入独立`.sync/wc-p0-deployment-core-cpu-r1-20261010`，不动旧stage。

## 接续

验收完整CPU原件、所有路径/962张量和失败后，接普通完整采样/恢复及A＋P0的来源接口；RA策略需显式接纳P非零来源模型，不调用原C/D控制器并假装P已经清风险。近似来源数值质量目前未知，真实P0八起点不能自动覆盖多次P自身轨迹。下一GPU设计仍固定全部必要控制和经验整卡费用，≤4自主，>4确认，无非必要人评。

## 原R1失败与独立R2

source1076532原3913226／3913227已退出1并消失，实际5.067818577秒。首SOURCE_BASE warmup因CPU t_embedder将RF的两个逐帧timestep reshape成标量而失败，零完整路径/产物，P0方法尚未进入；原26路径与两故障分母不改。[原件捕获](../reports/wc_p0_deployment_core_cpu_r1_terminal_20261010_capture.json)保持原源码/日志/预算SHA。独立R2只将夹具`t.reshape(1,1,1)`修为`t.reshape(1,-1,1)`再expand，生产P0模块不变；新R2夹具/driver/登记保留相同68源、全部26范围及两flow第二分支故障，真实CPU待。GPU新增0。
