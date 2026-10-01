# L0完整native binary验收与CPU导入保护

2026-10-01。

四个native binary全部获取并fresh审计通过：997270087字节，CPU1533.184018秒；三PyTorch官方SHA匹配，Flash官方asset ID/name/size/URL和actual local SHA/CRC/metadata通过（官方digest仍UNKNOWN）。全部3PIDs退出/下载锁释放/source与GPU账本不变，仅此次owned forward已关闭。隔离env仍空，未安装/import或新GPU。

[完整fresh审计](../reports/l0_native_wheels_r1_terminal_audit_20261001.json)/[获取运行](44_L0_NATIVE_WHEEL_ACQUISITION_RUN.md)。下载source e7338fe身份保持；旧获取launch/终态audit/CPU guard stage helper不能重跑。

官方固定Wan的wan/modules/t5.py:478在定义T5EncoderModel时求值torch.cuda.current_device，原样CPU import会查询CUDA。新CPU probe使用独立native_cpu_import_guard：只在已attest的这一个class/default/line调用处返回CPU device，禁止其他查询/嵌套；query函数finally恢复，source不改、CUDA不初始化。该probe进程的T5构造器device默认值为CPU，必须明确作为CPU检查适配，不能叫原样native import或GPU兼容。实际GPU运行不使用这个guard。

保护测试本地/Linux4同范围通过（不是8份独立证据）：实际默认求值、未attest查询拒绝、hash变化拒绝、异常恢复。真实native包导入尚未执行；修改后的probe仅语法通过。 [本地4](../reports/l0_native_import_guard_local_cpu_20261001.json)/[Linux4](../reports/l0_native_import_guard_linux_cpu_20261001.json)。

下一CPU600完整依赖hash lock，然后仅新env CPU1800安装，再新固定source阶段/CPU600 guarded native import、实际Torch ABI、825 meta结构、tokenizer与conditional scope检查。所有模型权重加载/真实任务/GPU仍待。主线没有一致质量—时间收益；新4GPUh clean50提议仍待预算决定。
