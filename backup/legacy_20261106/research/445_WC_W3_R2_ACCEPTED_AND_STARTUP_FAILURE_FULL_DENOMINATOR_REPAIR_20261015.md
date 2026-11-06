# W3完整R2 CPU接受与启动失败分母修复

2026-10-15，06:45一次查收原860020/source754fcd1。**实际入口/资源/完整矩阵及scope4、fullpost7、launch11共22控制接受，原进程已结束、预算不变、GPU0。** [原查收](../reports/wc_w3_label64_actual_production_CPU_r2_collection_20261015_0645.json.gz)、[独立接受](../reports/wc_w3_label64_actual_production_CPU_r2_independent_acceptance_20261015.json)保留。

随后完整源码复核发现启动失败的后处理边界：如果supervisor创建GPU child前退出，旧watcher对不存在的child_pid取值会失败；如果child已开始但没有runner回执，原post在初始化结果之前读不存在文件，不能完整输出计划分母。没有实际GPU遭遇这类错误，本轮不是方法负结果。

现已修复：监督初态明确记录child_pid/exit/runner SHA为空；watcher接受原监督释放后的“未创建child”状态；CPU post仍生成全部18父、64正式＋8warm标签位置，未开始时实际pairs0，child开始但回执缺失时实际pairs UNKNOWN，均不编造原件或真实teacher。原件存在则仍逐份检查，原scope与普通H1不改变。

新增一项负控制覆盖未创建child和缺runner两种情况，本地launch12＋fullpost7通过。新计数4＋7＋12共23应在fresh生产R3实际CPU再接受；原R2没有这版修复，不能用其旧SHA批准新GPU。

下一仅提交后source到fresh `.sync/wc-w3-label64-production-cpu-r3-20261015`，约5分钟一次查收。原R1/R2及数值R3均只读保存，已结束、不重查。通过后交付完整11.645828GPUh／建议上限12的具体卡供人决定；新GPU仍停止，PA715cae7原许可未回，原余24.974986不重置。无真实标签/拟合/新方法端点，不恢复F/B或加入人评/训练/OMR。
