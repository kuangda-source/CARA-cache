# guided-W1 同状态采集核心与下一真实批次（2026-10-10）

新[采集核心](../src/wcomr/cfg_guided_w1_collection.py)与[源码编译接口](../src/wcomr/cfg_guided_w1_forward.py)已实现。当前选定原D6路由的两个合法CC状态12／30，在线原缓存输出保持；β=1、原标量W1与当前probe起算的完整深层teacher只在同一实际状态评分。两分支直接经过原RF全文条件帧处理，形成FP32 BCTHW速度与guided目标。teacher与候选不写生成缓存，不观察校准锚点，额外深算、head、hash、读写成本独立记账。

源码转换在三个明确位置观察prewarp、当前hidden／上下文和实际原head输出，检查移除观察与恢复predicate后的AST完全等于原函数。候选使用原flow语句、当前embedding／adaln和原head；原Gamma／warp／head调用不改。给定head的RF转换只替换net调用，保留原条件时间和GT速度处理，逐值核对原输出。校准只观察实际D；按单调逻辑step建立历史，避免第35步cnt70清空后把第36步当历史第1步。实际部署的native-policy控制器允许第35步CC并按模70检查，第36步新周期保护DD，12／30历史分别应为[6,7]／[19,25]。

[CPU预登记](../manifests/wc_mf_a_collection_core_cpu_r1_preregistration_20261010.json)与[必要控制](../tests/check_cfg_guided_w1_collection_cpu.py)为flow OFF／ON各完整采集OFF／ON，共四条完整36步／144对／288正常net；校准两起点、原输出／终点／动作／counter／RNG／buffer值相同，实际八分支张量／起点保存并重读。另保留最后登记起点写出失败：计划36对／两起点，29对／一起点成功后第30对失败，poison后不继续。实际server CPU尚待，本地仅AST／compile。小型Toy blocks／非线性head和显式受控latent更新不是UniPC、Cosmos CAL、视频质量或速度。

[独立CPU部署](../scripts/deploy_wc_mf_a_collection_core_cpu_r1.py)和[原件捕获](../scripts/capture_wc_mf_a_collection_core_cpu_r1.py)使用现有server Python，禁止CUDA／下载，不获取GPU锁，不写费用。CPU期间原R2可继续及结算；不能把账本变化归为CPU使用GPU。

真实下一批保留四个CAL场景AV28／Human／misc／AV51、原seed0／guidance7／35请求，按[首窗口](../plans/WORLD_CACHE_MULTI_FIDELITY_FIRST_WINDOW_20261009.md)各两起点。完整ON/OFF对照为8条父路径／288solver／576正常net／8个全93视频槽，8个ON起点／16次score-only深层／416个额外deep-block调用、48个额外candidate/teacher head，64个真实post-RF分支速度保存。该GPU范围尚未冻结或提交，先接完整实际UniPC／管线控制与真实资产绑定、整卡成本和fresh准入；不从PaidProbe或旧标量误差补造速度。全局α∈{0,.5,1}，场景等权、并列取更小α，接BASE-R闭环全视频，不要求A先单独稳定获胜才能组合B／C。

[R2原实时进度](../reports/wc_ra_comparison_r2_last_native_live_progress_20261010.json)六方法路径各完整36步，RA目前两场景完整分支均28；Common Native已接受，Human Native仍在执行，原GPU／raw／评分四句柄活。这是计算进度，尚无八路径终态／全93新结果。原R1正负保留，不对子集验收或重投R2。

预算启动前实费32.03426413020637／77.89524658965853，48窗口余45.86098245945216GPUh、70提交／一个R2在途；预留不是实费，原作业退出后按全wall结算。完整单次≤4自主／>4确认，无非必要人评，goal active。旧16路6.704卡仍未批准。

CPU R1 source89a07b6／62源在导入时缺失calibration.py，6.766557秒退出1，尚未执行测试路径；[完整失败原件](../reports/wc_mf_a_collection_core_cpu_r1_terminal_20261010_capture.json)与原stage保留。这是隔离载荷遗漏，非方法负结果。新[CPU R2登记](../manifests/wc_mf_a_collection_core_cpu_r2_preregistration_20261010.json)只补完整本地import依赖闭包，不改算法、四全路径／两个起点及写出失败；新[独立R2部署](../scripts/deploy_wc_mf_a_collection_core_cpu_r2.py)和[原件捕获](../scripts/capture_wc_mf_a_collection_core_cpu_r2.py)不覆盖R1原件。

CPU R2 source7c4f3e6／64源2.467762秒导入源码全局绑定失败：夹具漏提取原compute_saliency_map，尚未运行测试路径；[失败原件](../reports/wc_mf_a_collection_core_cpu_r2_terminal_20261010_capture.json)保留。新[R3登记](../manifests/wc_mf_a_collection_core_cpu_r3_preregistration_20261010.json)补原函数namespace，并绑定已有真实D6使用的native-policy成对控制器，避免把早期原型step35保护DD冒充部署路由；真实固定DD为1–7／13／19／25／31／36，两个起点不变。旧源码、stage与失败不改；没有GPU或方法负结果。

CPU R3 sourcef6f4d1b／64源2.716150秒在第一对调用前拒绝：直接夹具给apply_worldcache的是35，而实际管线两CFG分支传70；[原件](../reports/wc_mf_a_collection_core_cpu_r3_terminal_20261010_capture.json)保留。新[R4登记](../manifests/wc_mf_a_collection_core_cpu_r4_preregistration_20261010.json)只将直接夹具设置为实际70-call horizon，36实际对与全部控制保持，不改模型或实际管线。真实GPU R2八路径已完整原件验收，评分仍运行，不重新生成。

CPU R4 source2b6e51a／64源实际5.056530秒退出0、原3884428／3884429消失；[完整原件](../reports/wc_mf_a_collection_core_cpu_r4_terminal_20261010_capture.json)独立绑定通过。四完整36步、flow两种设置逐输出／终点／动作RNGbuffer相同，40实际分支／五文件重读与最后起点写出失败恢复通过。继续完整实际UniPC采样接线，详见[219](219_WC_RA_R2_FIDELITY_AND_GUIDED_W1_FULL_PIPELINE_NEXT_20261010.md)。旧各阶段待状态为历史，不重投。
