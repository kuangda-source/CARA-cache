# H1 独立首卡：固定轨迹来源×1/2/4步

2026-10-03。当前状态 `PRODUCTION_CORE_CPU_PASS_PENDING_FULL_ACTUAL_DEPLOYMENT_NO_GPU`。延续[78接口/成本](78_WC_H1_FIXED_TRAJECTORY_CPU_AND_COST.md)；保留r4/H0和H1 CPU r1/r2失败及全部账目。主目标仍是提高调优WorldCache的质量–时间边界，当前局部诊断不等于目标完成。

## 冻结卡与执行依据

卡 `WC-H1-LOCAL-LIFETIME-R1-20261003-A`、run `wc-h1-local-lifetime-r1`，[配置](../configs/wc_h1_lifetime_r1.json)、[执行依据](../manifests/wc_h1_lifetime_r1_execution_20261003.json)、[成本](../reports/wc_h1_lifetime_r1_cost_20261003.json)。当前自主实验goal与既有[累计12GPUh/队列授权](BUDGET_AUTHORIZATION_20261003.md)支持完成常规准备后选择这张独立卡；不是新增人工消息，也不复用已完成104点r4的单次1800秒授权。H0筛查本身不直接启动下一GPU。

最多一次1800秒全cost、1770秒child、kill-after5秒；在78草案上另计50秒startup/import余量，保守规划包络1414.365秒，不缩矩阵以挤进1200。单昂贵任务，共享f1锁；load、首用/JIT、失败、诊断、IO与释放观察全部计费。已用5.05310433089345/12GPUh、34jobs不清零，无新GPU费用；启动时重新读实际账本，余额须容纳1800+15秒结算余量。没有自动第二H1、H2、RV或训练。

## 完整科学范围

一个已曝光第二CAL场景 `common_sense_6487f37f-ef57-49ca-afdc-d898922b5191`、seed0、93帧432×768/guidance7，Cosmos2.5-2B/eager/minimal_a2a，共同eval与原官方WC配置。完整UniPC-Karras网格仍请求35、实际36更新/70CFG horizon；baseline/observed各前21更新/42CFG。step13/21各36组件与进程内restore、全部九项输入/输出/状态/condition gates保留；13恢复后实际继续到21，不是独立可重启整管线接口。

step17/call33、34作为固定来源点，必须仍为有已付probe及两份严格过去同CFG真实full历史的官方full，失败不补选。一个deep组2..27；dense/matched-full/S只在这一状态生成参考，固定6/23/27原dense回退、0.1/0.98/noPV、各1warmup+3repeat。未来age1/2/4对应calls35/36、37/38、41/42，共6来源臂、18来源×age格、30raw文件。全部分母保持，失败不删、不另选K/场景/CFG。

三来源使用相同过去真实dense `(R_p,P_p)`、同一当前真实浅层 `P_s`，只改变新深层参考。私有Gamma+warp窗口 `[R_p,R_s^source] / [P_p,P_s]` 冻结至age4，中间官方刷新不改变held reference。matched-full/S始终approximate，不进入部署缓存或真dense校准器；未来读取相同官方轨迹输入/probe，不复用注意力mask。三种预测及raw先完成，之后才有当前D teacher；teacher重复两次逐位相等，原轨迹恰为full时再与其实际deep逐位相等。只有官方路径参与采样更新。

每个来源保存request/model/condition/CFG/group/step/call、过去true dense counter、快照SHA/版本、固定policy。新增实际cross-attention条件指纹按CFG核对；条件改变在复用与teacher前失败。完整报告每格MSE/reference energy/relative RMSE/方向余弦与有符号S−D、MF−D差。5%是描述性局部保真筛查，dense-held自身漂移同报；不预设单调，不从三个K推出连续安全寿命、最终质量或统计交互。两CFG是相关开发数据，早/中/晚与独立场景及完整闭环均未完成。

## 生产执行与实际CPU控制

[run_wc_h1_lifetime.py](../scripts/run_wc_h1_lifetime.py)调用独立的[同一生产前缀核心](../src/wcomr/h1_prefix.py)；真实入口不提供toy/kernel override。CPU用stand-in Inference/prepare/reset、Toy模块与合成kernel验证该核心，实际官方WC函数和UniPC源码均按固定SHA读取，不能当真实模型前向结果。

[实际CPU回执](../reports/wc_h1_prefix_cpu_r1_20261003.json)：32.689秒、Torch2.7.1+cu128、禁止CUDA lazy init，账本不变。flow OFF/ON两组各两臂21更新/42CFG，全部九门、step13/21各36组件、shared prepared batch/full RNG、buffer增量、18格与30raw通过；原件/重放要求沿78控制。非finite来源与当前CFG条件改变两种失败保持6/18分母，未生成未来truth/补点，所有model/net/scheduler/prepare挂钩恢复。六项reference控制与四组完整固定源码分支矩阵再验证通过；scope/cost/budget分别拒绝10/2/6种篡改。

本轮H1 condition guard的源码已更新，旧78 CPU r3保留其旧版本；当前回执记录新源码哈希。H0脚本与stage未修改。纯CPU core还不代替真实官方prepare/reset与实际模型九门；下一完整部署需补官方prepare CPU控制、真实UniPC在13/21恢复后的下一更新、固定原类meta共享eval、完整资产/包/source/import和sample metadata序列化检查，CUDA必须仍未初始化。

## 唯一启动与独立验收门

先提交/推送source、配置与具体卡；只在新stage验证全部payload，实际CPU及assets/import/native mode gates通过，再fresh UUID/VRAM/compute、全局锁、无inflight和预算。指定旧GPU只是候选，现场不满足则不争抢。输出run identity与scope绑定，旧stage/out/launch存在时只检查，不重复提交。

终态后独立核对source/同条件/九门/状态/来源语义、30文件60张量SHA/finite/shape、CPU float64误差复算与完整6/18分母，再核对实费/监督exit/PIDs/锁/GPU释放。技术门通过与局部寿命证据分别报告；范围不足不追认闭环、视频、H2或论文贡献。结果区待真实回执，不写预测结论。
