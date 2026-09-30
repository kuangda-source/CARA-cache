# L0隔离运行依赖的有界CPU获取

2026-10-01；CPU11_BINARY_ACQUISITION_PREPARED_NOT_PAYLOAD_OR_ENV_READY。

四个固定native binary获取程序已实现；本地/Linux11同范围CPU检查通过（不是22项独立证据），涵盖range/rollback/完整SHA、错误wheel名称版本平台、Flash断流续传/冻结local SHA/损坏cache拒绝及官方asset身份改变拒绝。完整wheel尚未下载、依赖未安装/native ABI未验收。

[CPU获取协议](../manifests/l0_native_wheel_acquisition_20261001.json)/[本地11](../reports/l0_native_wheels_local_cpu_20261001.json)/[Linux11](../reports/l0_native_wheels_linux_cpu_20261001.json)。新实现download_l0_native_wheels + wheel_assets；generic ranged_download代码未改，旧融合/audit/source快照保持。官方Torch3文件共809464679字节，Flash官方asset187805408字节，总997270087字节（0.929GiB），不含后续PyPI transitive dependencies。

四轮子使用精确cp311/linux版本：Torch2.4.1+cu121、Torchvision0.19.1+cu121、Torchaudio2.4.1+cu121、Flash2.7.4.post1/cuda12/torch2.4/cxx11abiFALSE。三PyTorch保持官方SHA/16MiB精确range/3retry/30秒socket；Flash在每个新获取/复用前重查官方asset ID/name/size/URL，按remaining exact range保留每MiB fsync前缀，最多3请求，完整ZIP CRC/Name/Version/Tag后冻结实际SHA，不称官方SHA。所有HTTP错误只记录type/status，signedredirect URLs不出日志。没有install/import wheel，也没有Torch/GPU import。

下一新唯一CPU获取identity，source先Git同步/hash部署，fresh旧6PIDs/CPU锁/磁盘/账本/新owned loopback proxy route检查，CPU3600秒cap/持久父子PID及exit/wall。预计从既有本机proxy通过仅本任务拥有的临时SSH转发访问，禁止停止共享FRPC/代理。新cache .sync/l0-native-wheel-cache，原empty virtualenv未改。

完整4 payload+官方/本地digest+实际wheel metadata核验与进程/锁/source/budget终态后只关此次owned forward，再固定完整resolved dependencies/新env安装/唯一CPU600 native probe。资源complete不自动授予WorldCache clean50或L1 GPU；主线质量—时间结论保持无一致收益。

Linux首次collection读到主工程pythonpath中的旧模块，未执行新wheel测试；修正为-c /dev/null/独立rootdir/confcutdir后实际11全部通过。该失败保留在Linuxreceipt，不把首次collection当测试PASS。
