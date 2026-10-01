# L0安装超时与六个大依赖分段获取准备

2026-10-01。

隔离install-r1因下载未完到CPU cap退出：1755.194480秒、UV被TERM，全部4PIDs退出/环境锁释放；fresh93安装清单仍0包，原4 wheel payload hash未变/source与GPU账本不变，仅此次owned forward16500关闭。原93包hash lock保持，6个未完成大包已锁官方PyPI URL/size/SHA（均在原hash lock内），共1781156006字节。分段续传程序及精确vendor tag检查本地/Linux15同范围通过，六个完整payload尚未获取。

[install终态审计](../reports/l0_native_env_install_r1_terminal_audit_20261001.json)/[实际UV I/O快照](../reports/l0_native_env_install_r1_io_observation_20261001.json)/[官方6包锁](../manifests/l0_native_transitive_binary_sources_20261001.json)/[本地15](../reports/l0_transitive_wheels_local_cpu_20261001.json)/[Linux15](../reports/l0_transitive_wheels_linux_cpu_20261001.json)。观察到原UV进程写入2.27GB/cache临时解压文件，仅说明I/O进行中，未完成6包/全93，不能把UV临时解压文件当作可续传的原wheel前缀或已验证payload。原UV已退出；共享UV cache不删除。

未完成6包为cublas12.1.3.1、cudnn9.1.0.70、cusolver11.4.5.107、cusparse12.1.0.106、nccl2.20.5与Triton3.0.0；选择cp311或py3/none/Linux x86_64的唯一官方wheel，SHA逐项属于原93锁。default native4 cp311/linux检查保留；新显式required_tags必须与实际WHEEL全部tag集合相等，可检测Windows或额外错误tag。已有range16MiB/3retry/30秒socket/fullSHA/失败回滚代码未改；新fetch仍不import/install Torch或NVIDIA。

下一Git同步后新唯一transitive-wheels-r1/CPU3600，stage .sync/l0-native-transitive-wheel-cpu-r1 已固定7source/manifest/test文件并完成Linux15（helper不可重复）。fresh旧安装4PIDs/环境与下载锁/磁盘/预算检查，新owned loopback16501与官方6个exact206/64KiB前缀预检，再真实下载；不能改旧install-r1 stage/source3、重复UV install或关闭Shared FRPC/Clash。

完整6包/fullSHA/meta及终态审计后再将这6个固定local files显式绑定进原93图（版本/范围保持，记录新lock与原lock SHA关系），复用其余已下载cache、唯一newenv安装重试，再actual Torch/Flash/native guarded CPU probe。现不是environment/model/GPU就绪，更不是新quality或speed结果；GPU4h cap与新clean50预算提议未改变。
