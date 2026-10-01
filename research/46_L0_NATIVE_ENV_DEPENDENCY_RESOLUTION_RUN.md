# L0隔离原生依赖解析运行

2026-10-01。

隔离env-resolve-r1/source78308f9 已唯一启动，4PIDs 2509814/2509815/2509816/2509822 实际live/环境锁持有；CPU600秒上限，官方PyPI TLS metadata预检通过。四个已审计local wheel是固定输入，完整transitive hash lock尚未完成；新env仍未安装/source与GPU账本不变。

[launch](../reports/l0_native_env_resolve_r1_launch_20261001.json)/[live](../reports/l0_native_env_resolve_r1_observation_20261001.json)/[二进制验收和CPU保护](45_L0_NATIVE_BINARY_ACCEPTANCE_AND_CPU_IMPORT_GUARD.md)。独立stage .sync/l0-native-environment-code-r1 有三个fixed source/manifest/audit输入；不能改stage或重跑launch。新owned forward16500继续持有直到完整resolve/install终态审计，只能关闭该owned SSH进程，Shared FRPC/Clash不动。

当前默认只取wheel；若纯Python ANTLR只发布source导致解析失败，完整审计原4PIDs退出/锁与empty inventory/source/预算后另新resolve-r2允许仅antlr4-python3-runtime source，不允许Torch/Flash编译。没有方法或质量结论；任何CLI/获取失败按技术资源问题记录。

解析成功需完整hash lock/Git同步，然后唯一CPU1800 newenv install；安装后实际guarded native import CPU600尚待，CPU4保护测试不等于native import。WorldCache新4GPUh/clean50仍待决策，L1也未自动获得预算。

R1已终态失败/原4PIDs全部退出/环境锁释放，empty env安装前后完全一致，source与GPU账本不变。实际原因是omegaconf2.3所需antlr4-python3-runtime4.9系列没有可用wheel；不是Torch/Flash获取失败或方法否定。按既定回退，下一新resolve-r2仅允许这个pure Python依赖source，并保持所有native binary local wheel。 [终态](../reports/l0_native_env_resolve_r1_terminal_audit_20261001.json)。

R2完整成功：完整原生依赖图93包已解析并hash lock验收，CPU r2退出0/4.079835秒、全部4PIDs退出/环境锁释放；新env安装前后仍空/source与GPU账本不变。R1因ANTLR无wheel技术退出，R2仅准许纯Python ANTLR4.9.3 source，Torch/Flash不编译。实际安装/native import/模型与GPU仍待。 [完整终态审计](../reports/l0_native_env_resolve_r2_terminal_audit_20261001.json)/[93包hash lock](../manifests/l0_native_environment_resolved_requirements_20261001.txt)。requirements SHA256 576df6a7b5c36bef10893d7fe5dddfcfd8cfee2e0b0813195d8807171ce43c75；全部24选定major pins/Flash及4 binary SHA逐项一致，每包有SHA。锁内file URL是服务器本地绝对artifact路径，不含credentials；不能直接在其他主机运行。
