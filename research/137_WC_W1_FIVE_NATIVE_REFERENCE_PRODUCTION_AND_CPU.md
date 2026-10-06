# 137｜W1 五参考完整执行、结算与全帧评分准备

2026-10-06；生产源冻结阶段：本机 CPU 通过，实际服务器 CPU 下一步。没有新 GPU 或科研结果。

按[确认窗口 v4.0](../plans/WORLD_CACHE_CONFIRMATION_WINDOW_20261006.md)，完整卡 `WC-W1-NATIVE-REFERENCE-CAL8-R1-20261006-A` 只补五个原索引0/3/4/5/7的 Native35，不重跑旧 WC/W1、不替换被拒 robot，原8/7/1分母保持；已有两匹配参考复用。3600秒总上限、3570 child、kill5，CPU前置准入规划30秒另从纸面机动余量扣，预付只3600秒；费用代理1743.586/2626.577秒不能作为硬界。加载、失败、输出与释放进入实际费用，CPU全93帧解码/LPIPS在释放后。本卡仍未获独立GPU范围批准。

生产入口沿用已实际CPU通过的五参考核心，显式关闭cache、绑定官方类forward、沿用原setup/request/seed/grid/28层eval/backend/guardrails及解码策略；仅改worldcache关闭和输出目录。共享f1锁、实际UUID/显存/进程两次检查、完整预算准入与预付、隔离自己的进程组、超时或冲突只终止自己的子进程、按原账本实际wall结算。技术异常保留原记录及完整五分母。

终态审计核对原PID退出、源/配置/CPU证明、全wall费用和可用旧/新视频SHA、93帧/PTS。未来别人使用GPU不阻止CPU评分。全接受时最多7匹配场景、14个Native相对loss；新参考被拒/中断则明确缺失，不补样、不计零。报告场景等权均值、中位数、改善/持平/退化与逐帧分布；逐帧不是独立样本，不要求七场景全胜。LPIPS为保真，旧MUSIQ/VQA混合结果仍保留，不声称物理/语义或独立CONF、部署速度。

[本机检查](../reports/wc_w1_native_reference_production_local_cpu_r1_20261006.json)通过21个损坏输入拒绝、全接受/含拒绝/中断的分母及正负持平评分。真实CPU子进程验证正常结束、启动失败、模拟外国GPU进程观测时仅停止自己的CPU子进程；三种临时账本均按实际wall结算、原子进程回收。合成metric和GPU观测不是真实视频/GPU证据。

[冻结配置](../configs/wc_w1_native_reference_production_r1_draft_20261006.json)及[CPU清单](../manifests/wc_w1_native_reference_production_cpu_r1_20261006.json)总159文件，原R2核心148文件不改，新增11文件包含本配置。下一实际CPU源/资产、生产合同、真实Native类及实际五请求/setup、四入口help；不重跑未改的完整五核心Toy。GPU执行仍等待W3-B的9600秒具体范围答复；W1完整卡CPU通过后再提交可审阅范围，不能把24GPUh预算视作任意新卡批准。
