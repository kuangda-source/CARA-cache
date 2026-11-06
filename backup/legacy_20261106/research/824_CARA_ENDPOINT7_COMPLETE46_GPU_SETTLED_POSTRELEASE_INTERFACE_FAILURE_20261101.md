# 824 — E1完整46路径成功与实耗结算；CPU接受接口失败

2026-11-01，北京时间。半程05:49检查原唯一E1：45/46完成、1运行、0失败，原四个PID/start ticks全部活跃，唯一runner2664726处于Exclusive_Process，87°C低于原90°C停止线。仅据计数与已耗墙钟，将同一个终验e1-2从08:50前移06:00，没有读取部分T_DD或科学分数。

资源检查期间原GPU容器于05:50:52正常退出，guardian全段于05:50:53.565203完成。原终态为46/46 COMPLETE、0技术失败；原四进程均退出、UUID/模式锁释放、Default恢复，GPU无计算进程。原40GiB内存/等额memory-swap限制、独占和源身份保持。实耗11000.422824110836秒，即3.0556730066974542GPUh，低于原硬7GPUh，已在四卡原唯一中央账本结算。cap226、旧16.5责任保持；中央已用194.03986128165678、预约16.5、可用15.460138718343217GPUh。该余额是本次结算快照，不是新卡准入。

原完整释放与结算通过后，仅一次启动无GPU、无网络、2CPU/26,27、8GiB且无额外swap、1800秒期限的CPU工件读者，调用原stage固定源released_artifacts。该读者在05:53:55报KeyError: 'model_sha256'，原容器退出1，原进程已结束；尚未进行13个RGB身份核验，没有产生完整packet，16新对CPU评分从未启动，完整28接受未成立。

根因是生产发布器publish_launch仅复制JOB_IDENTITY及ENDPOINT_IDENTITY，实际GPU-launch.json没有model_sha256；固定工件读者postrelease_manifest却读取该字段。旧CPU工件/管线fixture人工加入了这个字段，因此没有覆盖真实发布器到工件读者的这一接口。实际完整GPU执行与财务释放均有原件，但当前不能形成E1质量/时延结论，也不能据此判断任何方法成败。

首次CPU启动的外部响应包装发生stdout变量名冲突，导致本地返回未知；修复仅限外部运输包装，随后capture恢复同一个原CPU容器及PID/start ticks，没有重派读者或改变固定生产源。原失败启动回执、错误日志和完整原件均保留。运输响应回归通过；1268文件注册payload及runtime仍与原捕获一致。

一次半程e1和提前后的终验e1-2均已删除。本次按技术接受接口失败收尾：没有新科学冻结，不重评分原12行，不覆盖A32/B36/S/Q/搜索冻结，WC/RA仍为FIT UNMATCHED，四旧CAL/seed0范围保持。下一步只准备独立版本的CPU接受接口修复，针对实际原启动schema验证完整原工件；原GPU回执和失败读者不可补写，不需要重跑GPU，13RGB门通过前不派评分。

- [完整GPU原终态](../reports/cara_endpoint7_final_original_r1_20261101.json)
- [原实耗唯一结算](../reports/cara_endpoint7_final_settlement_r1_20261101.json)
- [原释放接受](../reports/cara_endpoint7_final_release_accepted_r1_20261101.json)
- [原CPU失败捕获](../reports/cara_endpoint7_artifact_CPU_capture_r1_20261101.json)
- [接口诊断与全部证据绑定](../reports/cara_endpoint7_acceptance_interface_failure_r1_20261101.json)
- [检查清理记录](../reports/cara_endpoint7_acceptance_schedule_closed_r2_20261101.json)
