# W3未干预恢复首卡：独立执行器及真实CPU回归通过

2026-10-04。承接[110冻结条件恢复与成本预案](110_WC_RV0_FROZEN_CONDITION_RESTORE_AND_COST_CARD.md)。上轮只复核旧104终态，没有推进新实验；本轮完成独立生产入口、预算监督和字段审计，属于progress。科学目标保持完整W3/RV0，当前首卡只是其中真实模型恢复控制，不把其通过改称完整因果验收。

## 固定范围和比较对象

[独立配置](../configs/wc_rv0_restore_r1.json)/[授权口径](../manifests/wc_rv0_restore_r1_authorization_20261004.json)：`wc-rv0-restore-r1`，`WC-RV0-UNCHANGED-RESTORE-R1-20261004-A`。两个已曝光CAL各一次完整官方WC父采样，在step22双CFG完成后各重复A/B两条未干预后缀；每条14个更新、28次CFG，恢复后父pipeline继续至36个更新、72次CFG和93帧768×432/16fps编码输出。共两父轨迹、四完整后缀、两个父视频，不解码child，不删分母。

每条后缀与本次恢复后的父continuation逐输入、输出、deep次数、solver输出、最终latent及全部状态组件相等；父视频另外复现已固定的历史官方WC SHA。这里没有新增无观察器父phase，因此对照口径是live parent continuation与历史官方编码桥。A/B是同动作重复，尚非交换C/D动作。没有RV标签、Head、LoRA、训练、独立CONF、人评、付费评分或干净速度测量。

## 本轮实际实现和验证

[独立runner](../scripts/run_wc_rv0_restore.py)先验证完整范围、费用代理、六官方源码、模型/CAL配置、真实CPU原件与当前35依赖、历史两实体视频和共享eval源码，复用旧S0的资产身份检查但不执行旧任务。新增CPU import检查当前恢复模块origin和实际Base/Text2World/GR00TV1Img2Vid冻结类；实际运行时再记录live条件类。

[恢复核心](../src/wcomr/rv0_restore.py)补齐历史官方桥使用的VAE scoped cuDNN策略：仅decode期间关闭benchmark、开启deterministic，采样backend flags前后须相同。旧入口没有这一设置，不能无条件承接历史编码桥。新增不初始化CUDA的内存观察，记录加载、父采样前后、快照前后以及每次后缀恢复后的allocated/reserved/max/free/total；PyTorch统计与外部GPU monitor分列，不视为全部进程峰值证明。原6GiB逻辑副本cap及free至少两倍副本加4GiB门保持。

[R4实际CPU](../reports/wc_rv0_frozen_restore_cpu_r4_20261004.json)/[独立原件审计](../reports/wc_rv0_restore_preparation_audit_r4_20261004.json)：197.041595秒，服务器原件SHA `02e50856f7ce8ea71a0ae9e617c270742fc1cbc4e1df549421ccc53341eaa020`，Torch2.7.1+cu128，CUDA不可见且lazy init禁止，35份当前依赖和六官方源码绑定。flow OFF/ON各两父四后缀、冻结属性恢复、mock视频桥、全部旧未干预/C/D接口回归通过；新增decode flags/冻结类/CPU观察器不初始化CUDA检查通过。Toy权重、decoder/writer仍非真实视频或GPU恢复证据，旧R1/R2失败和R3口径保持。

[范围费用22控制](../reports/wc_rv0_restore_scope_execution_cpu_20261004.json)/[独立回执18控制](../reports/wc_rv0_restore_audit_cpu_20261004.json)：拒绝删除父/后缀、缺CFG、输入/deep/solver/state漂移、未恢复、错误历史桥、可变条件、不足headroom、缺GPU观察、虚假peak/标签/完整验收、NaN wall和decode flags泄漏。后者为合成回执拒绝控制，不是GPU结果。

## 预算与提交规则

[监督器](../scripts/supervise_wc_rv0_restore.py)使用原全局f1锁和累计12GPUh账本，不重置44个历史job；只准入指定UUID、sm86、低VRAM且无compute worker，并在CPU身份验证后再次查询资源及账本。独立全wall最多3900秒，child3870秒、kill5秒、释放余量30秒。预付1.083333333GPUh，终态按导入、加载、失败、记录、退出和释放实际wall替换，保留失败分母及产物，不自动重试。发现其他进程只停止本job。

条件成本代理3828.379秒小于3900，但不是完成时间保证。现有权威账本10.713586944446/12GPUh、44jobs，无inflight，余4631.087秒；3900+15秒单独可容纳，尚未预付或提交。按现有自主实验goal和累计12h选择本卡，**不复用旧104/1800授权**，原4500秒C/D草案不与本卡共同承诺，后序按实费结算重算。

当前冻结payload51项加独立配置SHA。下一先commit/push，再实际部署/prepare/native-meta/资产/import/两条件metadata及独立部署审计，最后fresh UUID/VRAM/apps/锁/no-inflight/预算/磁盘门通过才唯一启动。终态用[独立审计](../scripts/audit_wc_rv0_restore_terminal.py)检查原PID、源码/费用/释放，重算两父四后缀全部字段和完整解码两个93帧视频。真GPU峰值、完整wall及恢复结果仍待测；完整RV0/C/D有符号收益仍缺，107稀疏净收益未成立的结论保持。
