# E5 checkpoint类上下文指纹修复登记（2026-10-11）

R2 a12c034／4092087与4092088退出1并消失、10.326426秒，仍在Meta guard阶段、0条采样。416字节与账本hash保持，完整失败回执已另次读取保存。没有降低完整范围或将失败报为通过。

**错误来自严格指纹生成器，未发现生产head数值实现差异。** Torch CheckpointWrapper.forward含一个嵌套函数，CPython3.10将其qualified name作为字符串保留在外层co_consts：实际为CheckpointWrapper.forward.<locals>.my_function，单独编译方法为forward.<locals>.my_function。两个flags均15、所有其他字段相同。另次仅导入检查确认，按原完整CheckpointWrapper类节点和Torch全局命名空间编译后，完整递归code_identity严格相同；没有忽略co_consts、名称或flags。

独立R3仅改期望wrapper指纹的编译上下文，原native leaf、wrapper调用、context_fn／kwargs／参数／状态／hooks／no_grad／unpatchify guard和数值算法保持；R1／R2源与回执不改。完整24 UniPC路径／864更新／1728 CFG／24实际文件888张量／444直接比较／96完整自身恢复＋7wrapper动态拒绝原范围保持。

`.sync/wc-e5-complete-sampling-cpu-r3-20261011`承接416来源＋5新载荷＝421文件，提交后CPU执行待。原独立重读脚本只读实际原件、不重跑sampler。CPU仍禁止CUDA／下载／账本写入。Toy边界、2B Meta而非真实权重前向的解释保持。

原E4c三个原句柄存活；AV28 OFF／ON及Human OFF三父完整，Human ON开始，完整4父／16suffix／24teacher继续不改。终态自动CPU全读优先，新GPU0、无训练／人评，≤8完整自主／严格>8具体批准与新增48窗口保持。E2/E3准确问题仍待不重问。

来源：`reports/wc_e5_complete_sampling_cpu_r2_terminal_20261011_capture.json`，`reports/wc_e5_native_wrapper_nested_qualname_diagnostic_20261011.json`，`reports/wc_e5_native_wrapper_class_context_exact_diagnostic_20261011.json`。
