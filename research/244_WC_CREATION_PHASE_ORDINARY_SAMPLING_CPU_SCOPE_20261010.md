# 固定创建阶段先验：普通完整采样 CPU 接线卡

2026-10-10，执行前登记。依据[阶段策略216步结果](243_WC_CREATION_PHASE_CPU_RESULTS_AND_CALIBRATION_DOMAIN_20261010.md)，把已登记的阶段控制器接入原普通采样。原全局版本及249绑定不改。本卡只验证阶段控制器与执行、来源、A、恢复的接线，不验证新真实视频。

完整范围保持原动态CPU卡：四个Toy命名请求、两种flow、八方法 `SOURCE_RA / DYNAMIC_NO_P / CPD / REF_CPD / A_CPD_OFF / A_CPD_W1_ONE_PHASE / A_CPD_BETA1_ONE_PHASE / DENSE_CONTROL`，64条成功和64条完整末写出故障，共128条36步、4608 solver更新、9216常规net调用；2368个成功张量重读、八条独立完整GEMM参照、八条原RA参照、八条A OFF参照、288步RA比较、512次物理与额外状态恢复、16变异拒绝、两次截断拒绝、两次末写出故障全部保留。

普通执行仅两项全局绑定替换：原动态owner构造使用 `CreationPhaseCPDController`，原完整batch使用该新owner。原函数字节码、执行器、部分GEMM、A读出、状态恢复与原模块全局保持；新模块分别记录绑定证明。fixture复用原完整检查，使用显式synthetic早／晚floor=0.005／0.02、step25边界及原同一synthetic drift与费用，不把真实经验映射混成CPU质量验证。成功路径所有P实际出生floor必须符合阶段，所有C保持上次来源floor，只有D归零，并要求实际早／晚P都出现。实际费用、rho／gain及工作P校准查表不属于本次改动。

在独立目录 `.sync/wc-source-aware-phase-sampling-cpu-r1-20261010` 运行。前置原动态128 CPU独立验收及原件哈希、源runtime、注册载荷与已提交源码一致。使用现有SCP，显式禁止CUDA，不获取GPU锁、不写预算；只启动一个完整CPU任务。终态须独立核对PID消失、完整结果、所有产物哈希与实际张量重读，不能把运行中状态算通过。所有失败原件保留，不按成功子集重定义范围。

这项正常接线为后续真实动作成本及完整方法视频做准备；不增加全层／历史搜索或人评。原RA＋A完整5.147707517 GPUh卡仍等具体确认、不拆卡；完整单次≤4 GPUh自主规则与新增48窗口保持。
