# L0 native binary CPU获取运行

2026-10-01。

native-wheels-r1/source e7338fe 已唯一启动，3PIDs 2507524/2507525/2507526 实际live/下载锁持有；四个源exact206/64KiB前缀通过。当前Torch已持久提交 167772160 字节，完整4 wheel/hash尚未完成；CPU3600秒cap/source与GPU账本不变，无安装/import/GPU。

[launch](../reports/l0_native_wheels_r1_launch_20261001.json)/[live](../reports/l0_native_wheels_r1_live_observation.json)/[获取准备](43_L0_NATIVE_WHEEL_ACQUISITION_PREPARATION.md)。同outputs/l0-native-wheels-r1观察至终态，禁止重复launch/改stage7文件。新owned loopback16499由此job独占，完整文件/终态审计后只关闭其SSH PID；共享FRPC/Clash不动。三PyTorch官方SHA与Flash官方asset身份/冻结本地SHA须分别记录。

下一完整payload fresh检查/进程退出/锁与账本核验，再完整依赖hash lock、隔离env安装和CPU600 native probe。新4GPUh clean50提议仍待决策，L1未自动获预算。

隔离依赖phase程序 prepare_l0_native_environment.py 已准备/语法检查，尚未实机执行：resolve CPU600/install CPU1800，各自新output/PID/子进程/锁/退出和源/账本/安装前后清单回执。四个已审计local wheel固定输入，完整PyPI依赖生成hash lock后才安装；默认只取wheel。如antlr4-python3-runtime只发布source，需记录失败后仅对此pure Python包开启source，不允许Torch/Flash编译。
