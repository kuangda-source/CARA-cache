# L0隔离原生环境安装运行

2026-10-01。

隔离env-install-r1/sourcee95adcb 已唯一启动，4PIDs 2510384/2510385/2510386/2510389 实际live/环境锁持有；CPU1800秒上限，固定93包hash lock安装到新env，NVIDIA运行库等transitive获取进行中。未完成安装/native import/ABI或模型验收；source与GPU账本不变，无新GPU workload。

[launch](../reports/l0_native_env_install_r1_launch_20261001.json)/[live](../reports/l0_native_env_install_r1_observation_20261001.json)/[已审计93包hash lock](../manifests/l0_native_environment_resolved_requirements_20261001.txt)。安装用uv pip sync --require-hashes，只在new .sync/l0-native-env-r1；原runtime/shared env及驱动不改。四个固定local binaries不编译，仅纯Python ANTLR source例外。

同outputs/l0-native-env-install-r1观察到终态，禁止重复提交/改stage固定source3。owned forward16500保持直到安装终态+完整清单/hash lock/source/账本/4PIDs/锁审计；只关闭该owned SSH进程，Shared FRPC/Clash不动。观察超时需检查同handle，不能重启安装。

安装完成也不等于native/ABI/model就绪。下一唯一新CPU600 guarded native probe；检查实际Torch ABI、全native package module origins、825 meta DiT keys/shapes、真实tokenizer及conditional scope。保护仅CPU import T5默认设备求值；GPU运行不用guard。主线仍无一致质量—时间收益，新4GPUh clean50提议待重要决定，L1不能自动启动。
