# L0六个大依赖分段获取运行

2026-10-01。

六个大transitive wheel分段获取transitive-wheels-r1/sourceffaf53f 已唯一启动，3PIDs 2512783/2512784/2512785 实际live/下载锁持有；服务器6个official PyPI URL均exact206/64KiB前缀通过，CPU3600秒cap。当前cublas410594774字节完整官方SHA与metadata通过，cudnn已持久提交83886080字节/0retry，完整6包/fullSHA/meta尚未完成。旧UV install-r1已终态且新env仍空/source与GPU账本不变，无新GPU workload。

[launch](../reports/l0_transitive_wheels_r1_launch_20261001.json)/[live](../reports/l0_transitive_wheels_r1_live_observation.json)/[官方来源与CPU15](48_L0_INSTALL_TIMEOUT_AND_TRANSITIVE_RANGE_PREPARATION.md)。固定7 source/test/manifest在stage .sync/l0-native-transitive-wheel-cpu-r1；新cache .sync/l0-native-transitive-wheel-cache；唯一outputs/l0-transitive-wheels-r1，所有旧wheel/install/resolve/fusion/audit launch不可重跑。

同3PIDs/16MiB exact range/3retry/30秒socket/fullSHA至终态；partial前缀在完整officialSHA通过前不可信，不叫完整payload。source/manifest/test文件不可在live期间改写，观察超时检查同handle，不能duplicate download。owned forward16501由本CPUjob独占，full6 payload/metadata以及父子PIDs退出/下载锁/原source/GPU账本终态审计后只关该owned SSH PID；Shared FRPC/Clash保持。

六包版本与digest都来自原93hash graph与官方PyPI元数据，未更换依赖版本；完整通过后将六个local wheel显式绑定进原93图/记录derivation，再唯一安装重试。将复用其余UVcache，不删除shared cache，旧UV临时解压文件不作为可续传wheel前缀。actual native/ABI/825meta/tokenizer/model/GPU仍待，CPU15与prefix预检不证明它们。主线结果/预算不变，new4GPUh clean50提议与L1预算均未自动许可。
