# 独立完整104点补验r4：1800秒条件卡

2026-10-03。用户在当前执行对话直接授权七份实施文件、CPU验证及全部门通过后的单次≤1800秒补验，计入现有累计12GPUh。旧r1/r2/r3及74的拒绝/1200秒成本阻碍保留历史；本卡只替代该补验实施限制，不授予自动下一窗口。

唯一run `wc-mid-full-r4`，card `WC-MID-FULL-COVERAGE-R4-20261003-A`。沿r3共享官方prepared batch与完整RNG转移，扩至call25/26/35/36×layers2..27的104QKV、312个dense/matched-full/sparse只读算子case，两臂各18个完整UniPC更新/36CFG前向，step13/18原总指纹与逐组件签名及observed进程内restore。全部九项一致性门保持；只返回原dense，不回写缓存。sim0.1/cdf0.98/no-PV、1warmup/3repeat及原CAL8开发场景/seed0/模型/采样不变。没有视频生成或质量评估，H0/H1/RV/训练均不自动启动。

[七文件/直接授权](../manifests/wc_mid_full_r4_authorization_20261003.json)、[冻结配置](../configs/wc_mid_full_r4.json)、[独立1800秒成本规划](../reports/wc_mid_full_r4_cost_1800_20261003.json)。规划包络1459.983秒+30秒关停结算余量≤1800秒；监督预留0.5GPUh，child≤1770秒、终止≤5秒，按包括加载/失败/观察/flush的实际墙钟结算。保留已用4.390463858430222h与31jobs，余额7.609536141569778h。fresh GPU UUID/VRAM/compute/全局锁/预算/磁盘门仍须现场通过。

[本地CPU回执](../reports/wc_mid_full_r4_local_cpu_20261003.json)：20通过，1真实UniPC控制因Mac缺diffusers交给实际Cosmos环境，不能算全门通过。实际服务器必须完成全部22项CPU控制、固定官方prepare OFF/ON、第13/18步恢复后下一更新逐位一致、完整source/资产/已有Sparge包及CPU import门；CUDA未初始化、账本不变才可唯一提交。当前尚未GPU。

## 实际CPU与唯一运行启动（非终态）

[实际部署](../reports/wc_mid_full_r4_deployment_20261003.json)：source8c140469b217b96414e606a44ca17539fb3d202b，22项实际CPU/source/资产/import/package控制通过，CUDA未初始化、账本未变。step13/18真实UniPC CPU恢复后的下一更新逐位一致，作为实现门不代替GPU。

[启动](../reports/wc_mid_full_r4_launch_20261003.json)/[现场观察](../reports/wc_mid_full_r4_start_observation_20261003.json)：唯一wc-mid-full-r4已fresh准入；监督2647232/timeout2647303已存活。GPU预留0.5h后账本在途4.890463858430222h，第32job；结束按实际全wall结算，旧31job/费用保留。child起算最大截止北京时间13:25:03；全部104点九门仍待实际收据，不改在跑stage或重提。
