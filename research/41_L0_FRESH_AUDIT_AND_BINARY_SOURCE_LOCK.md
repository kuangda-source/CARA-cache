# L0独立产物审计实际运行与官方二进制资源锁

2026-10-01；实际状态见最后观察，不叫模型/GPU就绪。

## 审计实际执行

[独立audit-r1 launch](../reports/l0_cpu_fusion_audit_r1_launch_20261001.json)，audit脚本source dbe863c/SHAa9caec6f、独立生成监督wrapper SHAeaf007d4；CPU900秒cap，固定原fusion sourcec69e492/stage7文件不变。实际父2505483/timeout2505484/auditor2505485均/proc live，CUDA空，fusion审计锁持有/source与GPU账本不变。

已fresh重算18原输入与融合前后digest一致，并fresh检查CFG-only全部825实际serialized tensor/3输出shard/525未目标基座bytes，shape/dtype/finite和字节digest通过。当前few-step+CFG fresh核验尚未完成，任务仍live，不将分臂PASS称整个审计PASS；原fusion自身已exit0/1960.417015秒。

[同handles观察](../reports/l0_cpu_fusion_audit_r1_live_observation.json)。使用ignored `.sync/observe_l0_cpu_fusion_audit_r1.py`，观察超时不能重启。只在parent/timeout/auditor消失且exit0、完整audit状态/全两臂1650、CPU锁释放/source与账本一致后结算。旧fusion/helper不重跑，audit-stage在跑时不改。

## 官方二进制元数据

[固定binary源](../manifests/l0_native_binary_sources_20261001.json)：官方PyTorch cu121索引确认Torch2.4.1+cu121、Torchvision0.19.1+cu121、Torchaudio2.4.1+cu121的cp311/Linux x86_64 wheel与官方SHA256。索引给出的真实download host是download-r2.pytorch.org，保留索引URL/bytes SHA与实际wheel URL，不虚构旧hostname。

官方FlashAttention v2.7.4.post1 release确认匹配cu12/torch2.4/cxx11abiFALSE/cp311/Linux asset，记录官方asset ID与size。该release API没有公开digest；官方SHA记UNKNOWN，未来下载后冻结实际payload SHA并绑定官方URL/asset ID/size，不称官方SHA验证。没有下载/install上述wheel，不能从元数据称Torch/Flash ABI或runtime通过。

[新环境pins](../manifests/l0_native_environment_proposed_pins_20261001.json)已补explicit Flash version与期望Torch CPP ABI False。[CPU runtime probe](../scripts/probe_l0_native_runtime.py)现在还必须传`--environment-lock`，逐pin核对实际installed metadata并在import Torch后实际核对ABI，再full native package import；只语法检查/未执行。新virtualenv目前为空，缺依赖；不改共享环境，不绕过Flash缺项。

后续先settle audit-r1，再官方wheels/完整resolved依赖锁、唯一bounded新环境安装/CPU600 probe。不得自动提交L1或WorldCache clean50 GPU，新预算决定仍待。
