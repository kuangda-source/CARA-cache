# 完整104路径组合验证与独占执行

用户已授权在组合检查通过后按新报价独占一张空闲卡运行。部署上限257.7712338712067秒、0.80×新Native与累计226 GPUh保持；完整104卡forecast11.423207 GPUh、硬上限11.9 GPUh，释放GPU后最多1.5小时/2CPU评分。原P1失败、原价卡和历史148路径CPU不重跑。

## 本次观察与实现

10月24日03:05:27四卡只读观察：GPU0为`user`账号的BeamNG.tech.x64（目录/data20t/shentong），GPU1/2为guanwenfei的Python PID937622/937623；GPU3无计算进程、24MiB、0%利用率、Default。该快照不等于实际派发准入，GPU前仍重查。原件：[资源快照](../reports/cara_four_card_resources_before_bridge104_20261024_030527.json)。未改其他用户进程或GPU模式。

104卡实现独立源文件，原P1执行器与stage不变。十角色、四CAL、两轮正式80路径、20warm、4诊断保持；GPU进程单load，不运行SELECT/DEV/TEST或搜索。诊断保留完整36guided输出，普通计时路径不复制guided。采集后核对104原件、Native/PG全D及audit/lean完整latent/RGB控制，再退出GPU runner；监督器按实际GPU墙钟结算，释放原UUID锁后才启动CUDA隐藏的CPU评分。

CPU评分保存72配对/6696帧原分数、PTS、指标/视频SHA。失败保留原视频和已完成分数，恢复时按精确配对与指标SHA复用，不重新生成。CPU阶段上限5400秒，超时保留原件；整卡终态接受仍要求评分完成、原进程退出、预算结算和完整独占记录。计时模型通过与否单独报告，不能把完整协议接受冒充时间模型或策略优势。

## 当前CPU状态

冻结source `5fc4dfe6`已发布。新stage `cara-pg-p1-CPU-history104-combination-r1-20261024`仅GPU隐藏1CPU/4GiB；实际生产请求/18采样入口、104路径序列化/15数值控制/72评分恢复路径、真实全93帧LPIPS、6种监督/guardian生命周期与14项终态故障检查组合运行。既有历史148检查按原件与源码SHA复用；不存在真实Ada质量/速度结论。

本地25项合同/时间模型/终态检查通过。原CPU容器于03:20:22退出0；[完整终态](../reports/cara_history104_combination_CPU_terminal_r1_20261024.json)与[独立接受](../reports/cara_history104_combination_CPU_accepted_r1_20261024.json)均通过。104路径与72评分调度使用声明的CPU端点/分数替身，真实LPIPS独立运行全93帧，不能当作104条真实Cosmos视频或72组实测质量。正式GPU尚未提交。唯一CPU启动原件：[launch](../reports/cara_history104_combination_CPU_launch_r1_20261024.json)。
