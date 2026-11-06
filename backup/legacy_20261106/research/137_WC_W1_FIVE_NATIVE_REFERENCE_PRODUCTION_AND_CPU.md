# 137｜W1 五参考完整执行、结算与全帧评分准备

当前：**完整五参考卡的实际服务器 CPU 准备通过，尚无新 GPU 运行或新科研结果。**

源 `064e6c0` 的 R2 独立 stage `.sync/wc-w1-native-reference-production-cpu-r2-20261006` 共159文件，七步 exit0、23.507秒：实际源/资产12.158秒、合同与监督结算0.369秒、真实Native/实际五请求和setup导入10.604秒、四生产入口help通过。[实际CPU回执](../reports/wc_w1_native_reference_production_actual_cpu_r2_20261006.json)原件SHA `ec7f5ca66d708df44598621d3dbc919792961b5b7d3bbd0f37631db175b1623d`；真实生成模型/权重张量/CUDA未执行。

[独立原件审计](../reports/wc_w1_native_reference_production_cpu_audit_r2_20261006.json)从服务器标准库核对766项原生SHA，原15个CPU句柄全部退出，21合同拒绝与3监督CPU集成场景重读原log；R1失败159文件、核心148、旧B136及最早R1核心146均保持。原GPU账本仍12.99974633233337/24h、47jobs、无inflight，W1/B新授权和真实输出不存在。预算SHA未变，新GPU费0。

[R1 CPU失败](../reports/wc_w1_native_reference_production_actual_cpu_r1_20261006.json)原件保留，13.279秒/exit1：先通过源/资产13.010秒，再在监督临时夹具的磁盘门退出；[只读诊断](../reports/wc_w1_native_reference_production_cpu_r1_diagnosis_20261006.json)发现 `/tmp` 余2558431232字节，不足4GiB，而真实数据盘余557978615808字节。R2只将CPU临时目录移至独立stage所在数据盘并增强失败报错，生产生成/监督/审计/评分/核心源码不改，未放宽磁盘准入。它属于CPU夹具文件系统条件不匹配，不是W1方法或真实GPU失败；旧控制未重复执行。

[最新具体配置](../configs/wc_w1_native_reference_production_r2_draft_20261006.json)与[冻结清单](../manifests/wc_w1_native_reference_production_cpu_r2_20261006.json)已可审阅。拟执行完整五参考、3600秒总/3570 child/kill5，上限1GPUh计入现有累计24；CPU准入规划另30秒从纸面机动池扣，机动余量由4785.913调整为4755.913秒（1.321087h），不增加GPU预付或累计上限。CPU能力准备完成，不由CPU通过、预算余额或自动续接推定新卡批准。W3-B 9600秒具体范围答复仍待，不重复提报。

已核对原始恢复请求及随后两个自动续接，共三个连续goal轮次；W3-B同一具体范围确认一直未到达。两卡必要源码/实际CPU/原件准备现已完成，[范围阻塞审计](../manifests/wc_confirmation_scope_blocked_audit_20261006.json)记录新的三轮计数，不沿用旧blocked计数。此时缺的是直接范围答复，不是预算耗尽、资源不足或方向被否定；目标未完成，准备结束后申请blocked并停止重复CPU/新增实验准备。确认任一具体卡后按该卡继续，另一卡不自动获准。

以下保留源冻结时的准备记录。


2026-10-06；生产源冻结阶段：本机 CPU 通过，实际服务器 CPU 下一步。没有新 GPU 或科研结果。

按[确认窗口 v4.0](../plans/WORLD_CACHE_CONFIRMATION_WINDOW_20261006.md)，完整卡 `WC-W1-NATIVE-REFERENCE-CAL8-R1-20261006-A` 只补五个原索引0/3/4/5/7的 Native35，不重跑旧 WC/W1、不替换被拒 robot，原8/7/1分母保持；已有两匹配参考复用。3600秒总上限、3570 child、kill5，CPU前置准入规划30秒另从纸面机动余量扣，预付只3600秒；费用代理1743.586/2626.577秒不能作为硬界。加载、失败、输出与释放进入实际费用，CPU全93帧解码/LPIPS在释放后。本卡仍未获独立GPU范围批准。

生产入口沿用已实际CPU通过的五参考核心，显式关闭cache、绑定官方类forward、沿用原setup/request/seed/grid/28层eval/backend/guardrails及解码策略；仅改worldcache关闭和输出目录。共享f1锁、实际UUID/显存/进程两次检查、完整预算准入与预付、隔离自己的进程组、超时或冲突只终止自己的子进程、按原账本实际wall结算。技术异常保留原记录及完整五分母。

终态审计核对原PID退出、源/配置/CPU证明、全wall费用和可用旧/新视频SHA、93帧/PTS。未来别人使用GPU不阻止CPU评分。全接受时最多7匹配场景、14个Native相对loss；新参考被拒/中断则明确缺失，不补样、不计零。报告场景等权均值、中位数、改善/持平/退化与逐帧分布；逐帧不是独立样本，不要求七场景全胜。LPIPS为保真，旧MUSIQ/VQA混合结果仍保留，不声称物理/语义或独立CONF、部署速度。

[本机检查](../reports/wc_w1_native_reference_production_local_cpu_r1_20261006.json)通过21个损坏输入拒绝、全接受/含拒绝/中断的分母及正负持平评分。真实CPU子进程验证正常结束、启动失败、模拟外国GPU进程观测时仅停止自己的CPU子进程；三种临时账本均按实际wall结算、原子进程回收。合成metric和GPU观测不是真实视频/GPU证据。

[冻结配置](../configs/wc_w1_native_reference_production_r1_draft_20261006.json)及[CPU清单](../manifests/wc_w1_native_reference_production_cpu_r1_20261006.json)总159文件，原R2核心148文件不改，新增11文件包含本配置。下一实际CPU源/资产、生产合同、真实Native类及实际五请求/setup、四入口help；不重跑未改的完整五核心Toy。GPU执行仍等待W3-B的9600秒具体范围答复；W1完整卡CPU通过后再提交可审阅范围，不能把24GPUh预算视作任意新卡批准。
