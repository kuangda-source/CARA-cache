# 独立完整104点补验r4：全部技术门通过

2026-10-03。唯一run `wc-mid-full-r4`，card `WC-MID-FULL-COVERAGE-R4-20261003-A`，冻结部署source `8c140469b217b96414e606a44ca17539fb3d202b`。用户在本执行对话直接授权七份文件、CPU验证及全部门通过后的单次≤1800秒/现累计12GPUh补验。该次授权已执行完毕，无自动重启或下一窗口。旧r1/r2失败及费用、r3短前缀身份保留；74的写入拒绝和1200秒规划成本阻碍是历史，原估算不是实际超时断言。

## 完整覆盖与无扰动结果

[实际runner](../reports/wc_mid_full_r4_runner_20261003.json)、[汇总](../reports/wc_mid_full_r4_summary_20261003.json)、[独立审计](../reports/wc_mid_full_r4_audit_20261003.json)。call25/26/35/36×layers2..27的104QKV/312 dense、matched-full、sparse case全部完成，仍为同一个已消耗CAL8开发场景，104个算子输入不等于104独立场景。原模型/seed0/93帧/432×768/guidance7/UniPC-Karras35请求、36实际solver网格、WC70-call horizon不变；sim0.1/cdf0.98/no-PV、1warmup/3repeat，始终返回原dense，shadow不回写缓存。

两臂各18个完整UniPC更新/36CFG前向，18full/18skip；输入总哈希、输出、trace、块数、原完整状态指纹、采样、命名输入、condition和逐字段签名九项门全部严格相等。共用官方prepared batch、request以及完整RNG前后转移签名一致。step13/call26、step18/call36每处36组件全部相同（14 net/WC、16 solver及output和五类RNG/显式generator组件）。两处observed进程内restore均通过；第13步restore后GPU实际继续至第18步且仍与baseline匹配。该证据不覆盖独立进程重启、条件/闭包重构或不同动作的反事实整管线分叉，也没有第18步后的GPU续推。

独立CPU审计重新读取104份QKV，总39749652384 bytes（约39.75 GB）：文件SHA/长度、q/k/v集合、BF16 [1,31104,16,128]、finite及312个张量raw-byte SHA全部通过，case与其自身call/layer的snapshot正确关联。312case均finite、三次hot计时及中位数一致；冻结payload、全部九门和两处组件完整性/恢复、费用及释放独立验收。没有另开GPU重算误差；数值摘要来自已录算子输出/误差，审计重算了计时中位数与筛查汇总。约39.75GB bulk保留服务器，不入Git。

## 算子筛查

| 指标 | 结果 |
|---|---:|
| dense/sparse中位算子耗时比 | 1.218931× |
| sparse相对真实dense RMSE≤5% | 92/104 |
| dense/sparse速度比≥1.1 | 76/104 |
| 同时通过两筛查 | 64/104 |
| matched-full相对dense最大RMSE | 1.3327% |
| sparse相对dense最大RMSE | 9.2873% |

每call双筛查通过数：25为14/26，26为15/26，35为17/26，36为18/26。层6、23、27在四输入上均超过5%误差；该统一稀疏配置不能用于全部深层。matched-full全104点通过本局部误差筛查，仍是量化/同后端近似，不是真dense anchor。1.219×是单次self-attention算子的复测中位比，未部署候选生成视频，不能称视频质量保持或端到端加速。r2的62/104只是旧失败控制下的局部诊断；本r4独立64/104不能倒改r2为PASS。共享prepared-input与全RNG是组合修复，本轮通过不证明r2 GPU失败只有一个原因。

完整中间刷新/全26深层技术覆盖缺口已补齐。下一可准备现有H0互补性具体卡，按不安全层及实测成本作保守选择，之后H1来源×寿命；无统一全层配置或缓存后续收益结论。H0/H1没有实施或运行授权由此自动产生；W1/W2复杂化暂停，RV仍DESIGN_ONLY，尚无标签/Head/LoRA/训练。

## 实施、CPU、费用与释放

[直接授权和七文件清单](../manifests/wc_mid_full_r4_authorization_20261003.json)、[冻结配置](../configs/wc_mid_full_r4.json)、[独立1800秒成本规划](../reports/wc_mid_full_r4_cost_1800_20261003.json)。本地20CPU通过；Mac缺diffusers的实际UniPC检查改由必过的真实Cosmos环境执行。[实际部署](../reports/wc_mid_full_r4_deployment_20261003.json)22项CPU全通过（含官方prepare OFF/ON、第13/18步恢复后下一UniPC更新逐位一致）、源码/资产/已有Sparge包和CPU import门通过，CUDA未初始化、账本未变。成本规划1459.983秒+30秒余量≤1800秒；fresh UUID/VRAM/compute/锁/预算/磁盘门通过后[只启动一次](../reports/wc_mid_full_r4_launch_20261003.json)。最初launch回执state null是监督器写状态前的启动瞬间，[后续现场回执](../reports/wc_mid_full_r4_start_observation_20261003.json)确认child。

[监督结算](../reports/wc_mid_full_r4_supervisor_20261003.json)：exit0，无stop reason，全过程GPU墙钟1153.547615806秒（0.320429893279GPUh）≤1800秒，涵盖导入/模型加载、两臂诊断、退出/释放；baseline前缀206.944554秒、observed含shadow787.550977秒，两者不是候选端到端对照。0.5GPUh预付在途值已用实际费用替换，不重置历史。权威[账本](../reports/budget.json)累计4.710893751709566/12GPUh、32jobs，余7.289106248290434GPUh，无inflight；账本status是监督器结算阶段字符串，最终验收见独立audit，未为改字符串重写服务器账本。

原supervisor2647232/timeout2647303/runner2647305均不在/proc，全局f1.lock可获取；指定A6000回到24MiB/no compute，540次monitor无其他PID，源/费用/释放审计通过。CPU审计CUDA未初始化，无新增GPU任务或费用。原r1 172.900538秒、r2 1064.140757秒、r3 486.319348秒全部保留。只在Git保存源码、配置、文档和小回执；权重/视频/大QKV未同步。
