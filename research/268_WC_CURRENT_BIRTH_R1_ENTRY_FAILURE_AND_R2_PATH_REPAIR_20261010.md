# 当前P完整CPU R1入口失败与R2路径修复

2026-10-10。原工作P完整256 CPUexit0后，新785f847／314载荷任务按顺序启动；监督3999876、子4000240均退出，R1 exit1、实际CPU0.450656424秒。入口读取`Path('scripts/check_wc_working_epoch_sampling_cpu_r1.py')`依赖当前工作目录，服务器从其他目录启动，触发FileNotFoundError。尚未进入测试fixture或任何采样路径，实际完成0／计划256保留；无Torch/CUDA执行或GPU费用。

失败回执、test.log、driver／注册／payload已独立绑定，`independent_source_complete_results_and_actual_artifact_hashes_verified`在这个失败捕获中只证明失败元数据与源码，不证明完整CPU通过。旧stage不修改、不重启，失败不作P算法或方向负结果。

新R2仅将driver源码路径改为`Path(__file__).resolve().parents[1] / 'scripts/check_wc_working_epoch_sampling_cpu_r1.py'`。R1／R2入口逐字只差此一处；当前P控制器、物理owner、fixture和目标规则不改。外层、派生层与最终生成driver先编译并保留逆向AST检查；路径从任意启动目录定位冻结stage，完整服务器CPU待实际执行。

R2完整256×36／9216更新、4736成功张量、1024恢复、原32＋12工作周期＋12目标变异、四文件截断及四完整写出故障范围保持；四请求／八方法／两个flow／两个工作周期不缩。新独立stage、source、注册和监督一次执行；前置加入已独立验收的原4736张量／4032决策证据及已封存R1失败。GPU0、不写账本、不改变原判据或容差，无新增人工评审。

阶段A四场景终点保真改善和实测参数P动作0→240脚本结果保留；下一R2完整验收、实际参数组合入口、生产CPU和具体视频卡仍按计划推进。累计GPU37.676066656/77.895246590、新48剩余40.219179934保持，严格>4GPUh整卡才确认。
