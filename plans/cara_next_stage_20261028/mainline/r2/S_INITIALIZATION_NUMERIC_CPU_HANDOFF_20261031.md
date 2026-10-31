# S 初始化数值 CPU 原句柄承接

已完成：R3 于2026-10-31 17:26:37退出/0；完整矩阵和12项独立验收控制通过。终态为 reports/cara_s_initialization_numeric_CPU_R3_operational_r2_20261031.json，接受为 reports/cara_s_initialization_numeric_CPU_accepted_r3_20261031.json，见 research/800_CARA_S_INITIALIZATION_MATCHED_NUMERICAL_CPU_ACCEPTED_20261031.md。以下恢复说明仅供审计，不再查询或重跑已完成CPU。

仅两卡、隐藏 GPU 的微型数值验证；无新 GPU 或账本授权。原 14GPUh GPU 任务仍只按 BUDGET_SUCCESSOR14_POST_LAUNCH_HANDOFF_20261031.md 承接。

R1 因漏带旧固定掩码参数文件退出/1；R2 因两个入口未匹配执行配置而在精确 latent 比较处退出/1。两次失败的源包、容器和回执保留，均未接受完整数值矩阵，不重放原容器。

R3 源为 989e1161f1aa8c81be8434644ceb4e49165f7c13，原容器 cara-S-init-numeric-CPU-a6000-r3-20261031-cpu，原 stage 为 /data20t/gaokuangda/worldcache_workspace/.sync/cara-S-init-numeric-CPU-a6000-r3-20261031。原注册 SHA 为 ee65b3994a17dbeb99a238cfadae00cd44de531321738698df0347ab04299d92。原启动回执 reports/cara_s_initialization_numeric_CPU_launch_r3_20261031.json；实际启动 2026-10-31 17:24:07 Asia/Shanghai，1 核 CPU26、4GiB、无额外 swap、network none、GPU 隐藏、工作上限1200秒和退出上限60秒。

只恢复原句柄：

```sh
python3 scripts/cara_s_initialization_numeric_cpu_r3.py capture --source-revision 989e1161f1aa8c81be8434644ceb4e49165f7c13 --output reports/<fresh_original_capture>.json
```

未知只再 capture；不得再次 prepare、改远程源码或重启容器。完整退出/0后，独立接受脚本为 scripts/accept_cara_s_initialization_numeric_cpu_r1.py，参数 --capture 原终态 --launch 原启动 --output 新回执。源码、资源、两 flow 的实际 installer 配置、3策略×2FIT×3模式×2flow=36条生产路径、12条旧入口比较、18项失败控制都必须接受；两入口完整36步 guided、终态latent/RGB/Torch RNG须精确一致。不会以放宽容差或移除旧入口对照获得通过。

该检查使用声明过的微型权重、attention、prepare、decoder和writer替身，保留 pinned Block/RF/WC/UniPC 与生产路由；不代表真实 Cosmos 权重、真实视频效果或清洁GPU计时。仅本次受影响的3个Uniform初始化策略数值路径受检，799的342策略选择器覆盖是单独证据。

R3 把原 ALLD 配置显式绑定到两入口，只将 flow_enabled 作为 False/True 测试轴，并在每次实际 apply_worldcache 调用检查完整配置。R2 中 flow 标签仅来自上层 fixture，而生产 Requests 会覆盖为 ALLD 的 True；不能把该未接受测试说成覆盖了两种实际 flow。原已冻结生产源码和旧科学结果不修改。
