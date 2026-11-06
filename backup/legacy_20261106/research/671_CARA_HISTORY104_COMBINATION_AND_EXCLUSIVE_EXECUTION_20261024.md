# 完整104路径组合验证与独占执行

用户已授权在组合检查通过后按新报价独占一张空闲卡运行。部署上限257.7712338712067秒、0.80×新Native与累计226 GPUh保持；完整104卡forecast11.423207 GPUh、硬上限11.9 GPUh，释放GPU后最多1.5小时/2CPU评分。原P1失败、原价卡和历史148路径CPU不重跑。

## 本次观察与实现

10月24日03:05:27四卡只读观察：GPU0为`user`账号的BeamNG.tech.x64（目录/data20t/shentong），GPU1/2为guanwenfei的Python PID937622/937623；GPU3无计算进程、24MiB、0%利用率、Default。该快照不等于实际派发准入，GPU前仍重查。原件：[资源快照](../reports/cara_four_card_resources_before_bridge104_20261024_030527.json)。未改其他用户进程或GPU模式。

104卡实现独立源文件，原P1执行器与stage不变。十角色、四CAL、两轮正式80路径、20warm、4诊断保持；GPU进程单load，不运行SELECT/DEV/TEST或搜索。诊断保留完整36guided输出，普通计时路径不复制guided。采集后核对104原件、Native/PG全D及audit/lean完整latent/RGB控制，再退出GPU runner；监督器按实际GPU墙钟结算，释放原UUID锁后才启动CUDA隐藏的CPU评分。

CPU评分保存72配对/6696帧原分数、PTS、指标/视频SHA。失败保留原视频和已完成分数，恢复时按精确配对与指标SHA复用，不重新生成。CPU阶段上限5400秒，超时保留原件；整卡终态接受仍要求评分完成、原进程退出、预算结算和完整独占记录。计时模型通过与否单独报告，不能把完整协议接受冒充时间模型或策略优势。

## 当前CPU状态

冻结source `5fc4dfe6`已发布。新stage `cara-pg-p1-CPU-history104-combination-r1-20261024`仅GPU隐藏1CPU/4GiB；实际生产请求/18采样入口、104路径序列化/15数值控制/72评分恢复路径、真实全93帧LPIPS、6种监督/guardian生命周期与14项终态故障检查已完成。既有历史148检查按原件与源码SHA复用；不存在真实Ada质量/速度结论。

本地25项合同/时间模型/终态检查通过。原CPU容器于03:20:22退出0；[完整终态](../reports/cara_history104_combination_CPU_terminal_r1_20261024.json)与[独立接受](../reports/cara_history104_combination_CPU_accepted_r1_20261024.json)均通过。104路径与72评分调度使用声明的CPU端点/分数替身，真实LPIPS独立运行全93帧，不能当作104条真实Cosmos视频或72组实测质量。随后通过空闲卡准入并实际提交，见下节。唯一CPU启动原件：[launch](../reports/cara_history104_combination_CPU_launch_r1_20261024.json)。

## 实际GPU启动与后续验收

2026-10-24 03:21:57.029531 +08:00，完整104路径卡单次启动。唯一launch ID `d6351496-ee8a-4428-8ede-898f53d665cd`，run `cara-history-boundary104-cal4-ada-r1`，执行源码 `5fc4dfe66a33a915fcc7bdf10700bae8810bb401`，stage `/data20t/gaokuangda/worldcache_workspace/.sync/cara-history104-full-ada-r1-20261024`。GPU3 UUID `GPU-d4868f0a-29df-9077-82db-77f7bf0f9934`，guardian PID1204767/start956838038，runner PID1204959/start956838489/UID1000。GPU0/1/2原任务未变。

[唯一实际启动](../reports/cara_history104_GPU_actual_launch_r1_20261024.json)、[硬独占原runner核验](../reports/cara_history104_GPU3_exclusive_active_r1_20261024.json)及[初始化技术状态](../reports/cara_history104_GPU_initial_health_r1_20261024.json)完整保存。最新技术收件为HISTORY104_MODEL_LOADING、0/104完成、0失败，guardian/supervisor/runner/container均匹配。首个准入回执上下文尚未建立，后续独占证明核验真实唯一CUDA进程；不能把初始化或CPU接受称为GPU结果。

实际预约11.9 GPUh后，累计池已用135.12066151587194、预约28.4（本卡11.9与旧两卡未知责任16.5）、可用62.47933848412806 GPUh，累计上限226保持。只在原GPU进程结束、独占记录完整、实际费用结算及原锁释放后开始72配对/6696帧CPU评分；CPU评分完成后独立终态验收。

已安排同launch的10月24日09:05技术半程（`cara-104`）和15:03全程检查（`cara-104-2`）。后者是检查时间，不保证届时评分结束；若仍运行按实测更新原检查。半程不看部分科学结果调参，提前退出保存原件与费用。未知只恢复原句柄，不重新派发。终态分别报告协议接受、计时模型验证、历史强基线结果，部署257.7712338712067秒及累计226 GPUh不放宽。

后续实际观测2026-10-24T03:28:24.130215+08:00：[首条路径运行收件](../reports/cara_history104_GPU_model_health_r1_20261024.json)已从模型加载进入RUNNING，0/104完成、1路径运行、0失败；原四类句柄与唯一runner保持，错误列表为空。
