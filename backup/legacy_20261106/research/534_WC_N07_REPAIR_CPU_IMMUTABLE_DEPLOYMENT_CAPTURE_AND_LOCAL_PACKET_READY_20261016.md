# N07修复生产CPU：独立部署、一次查收与源码包准备

2026-10-16。接续533，新增R2的CPU部署、ETA后一次查收和离线接受工具。三项新控制、九项原不可变打包控制及三个冷入口通过；当前183份overlay闭合原99数值依赖、修复源码、真实生产入口和执行测试的导入。**尚未部署服务器CPU；Git归档后的完整隔离验证待本次源码提交后执行。**

三个工具严格核验原N07部署/查收/接受脚本的SHA，仅作可逆的合同导入、路径、状态标签与九命令计数绑定，逆字节/AST一致。部署沿用已有不可变安装器：只读原N05完整生产CPU基座，核对原registration，再建立全新stage、冻结新registration和完整payload；原失败N07 stage、共享runtime、GPU任务和账本不写。

原基座是source15d77ac、registration SHA`cb2b95f3ee213a459abcb51f24b1e473c4cc20921991181366617a7baddae322`的已保存完整N05 CPU回执。测试中的合成base标签只检验打包闭合；实际部署仍必须使用并核验该原回执，不能把合成标签当服务器准入。

包内显式加入动态执行的R2 worker/supervisor/post/watcher、CPU bundle、三个CPU工具、520证明对应源码和所有相关fixture。它仍登记八组控制＋实际Cosmos无权重生产入口，共九命令；520采样证明和99数值源码按原件复用，不再跑采样或读取终点科学结果。

CPU启动保存唯一PID/start_ticks、源、stage、registration SHA和最早查收时刻（启动后240秒）。查收只读这个原句柄和完整payload/CPU原件，再离线接受；连接或读取未知不能触发重派。GPU授权不会由CPU工具产生，原完整180、15.055555556GPUh报价、cap113与严格少于12规则保持。

接下来先按已提交Git树归档并安装到本地隔离目录，运行完整八组控制与冷入口，确认工作区没有漏传依赖；通过后再仅启动独立服务器CPU。实际GPU派发/科学终态和N08/N09引用接续仍待，不把本地打包准备当真实生产CPU或修复效果。

本轮0SSH/新GPU/服务器账本写入。原R1及10月17日05:30完整失败查收安排保持，F/B关闭。

原件：[源码包与本地控制准备](../reports/wc_paper_N07_repair180_CPU_staging_local_preparation_20261016.json)。工具：[CPU部署](../scripts/deploy_wc_paper_N07_repair_production_cpu_r2.py)、[一次查收](../scripts/capture_wc_paper_N07_repair_production_cpu_r2.py)、[离线接受](../scripts/accept_wc_paper_N07_repair_production_cpu_r2.py)、[可逆绑定与包闭合](../src/wcomr/frozen_repair_cpu_staging_r2.py)。
