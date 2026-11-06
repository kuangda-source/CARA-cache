# 825 — E1验收接口修复；13RGB通过，16新对CPU唯一评分已创建

2026-11-01，北京时间。用户直接要求“修复验收接口，然后验收”。独立兼容层与8项本地回归已提交af620e99并推送；原GPU stage的1268文件、原启动回执、原失败工件读者和3.0556730066974542GPUh唯一结算全部保留，未再次运行GPU或记账。

兼容层先通过原财务/资源释放验证，再核验原注册proposal、资产清单和实际4.12GB模型blob的完整SHA。它只给原工件读者的进程内launch视图补充经独立核验的model_sha256；财务读者继续读取原字节。原管线与工件读者的字节码、RGB/PTS/全帧/原分数复用规则保持，原模块全局对象不改。packet另行记录适配器SHA、模型证据、原source/launch SHA，随后由原评分manifest整体摘要绑定。

本地8项回归直接使用缺字段的真实GPU发布回执，重建proposal与原注册SHA相同；覆盖实际/显式模型冲突、重复或未注册模型、错误GPU、未释放时禁止读回、原函数/回执不被改写。没有手工修改原发布回执来制造测试前提。

修复读者是独立无GPU、无网络、2CPU/26,27、8GiB/无额外swap、1800秒限额的CPU容器，14:18:41启动、14:19:40正常退出。完整46视频及原张量、请求参数、93帧/PTS和全部13/13RGB身份门均通过；12原B36分数行保持。原失败CPU容器仍在原处，没有清除失败或重新启动它。

随后仅一次创建16新对CPU评分intent，时间14:21:27，原stage/endpoint-score-control。使用原固定评分器、原Fidelity-v2及离线Alex/PIQ环境：2线程/26,27、8GiB、无额外swap、硬2小时。原manifest SHA为ed1ff86272d45257707d3447f44a078997f24048ba97d4ceadbc9f1c51482935，原intent SHA为658844fae9714727bfdb8c1260bf4006427296536123a11c96995f50829344a7。任何未知只capture恢复原句柄，不再次score。评分尚未完整接受，不读取部分科学分数。

另安排同一条CPU完整终验e1-cpu在14:35兜底；若本对话先完成接受则删除。下一步完整16新+12原行的28位置接受后，导出双时钟、93帧曲线和原图表，按原决策树解释四旧CAL/seed0；保持旧冻结、WC/RA FIT UNMATCHED、保护TEST及无自动下一GPU。

- [用户修复/验收授权](../plans/cara_next_stage_20261101/e1/ENDPOINT7_CPU_ACCEPTANCE_REPAIR_AUTHORIZATION_R1.json)
- [8项接口回归](../reports/cara_endpoint7_acceptance_repair_local_CPU_r1_20261101.json)
- [完整46与13RGB接受](../reports/cara_endpoint7_repaired_artifacts_accepted_r1_20261101.json)
- [原完整packet](../reports/cara_endpoint7_repaired_artifact_packet_r1_20261101.json)
- [原16对CPU启动](../reports/cara_endpoint7_original_score_CPU_launch_r1_20261101.json)
- [CPU终验日程](../reports/cara_endpoint7_repaired_CPU_acceptance_schedule_r1_20261101.json)
