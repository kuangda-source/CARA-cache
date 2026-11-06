# 完整24的CPU部署、收件与GPU监督代码已准备

2026-10-18。**连续修正四臂实验已补上不可变目录部署、完整生产CPU收件、按UUID监督及自动后处理的代码。** 这让N09实际观测完成后能接原完整范围，保留旧12对照和已有88数值证明。当前仍是本地代码准备，没有实际生产CPU或新A3结果。

## 本轮完成的执行支持

- [部署工具](../scripts/deploy_wc_drop1_window24_cpu_r1.py)：以原88数值目录为只读base，增加Git绑定的新入口、配置／报价／证据，拒绝覆盖任何旧payload文件。两份原simple26d数值证明从原N12目录只读复制，原目录注册身份固定，副本SHA纳入新注册。实际N09报价／配置缺失时在SSH之前停止。
- [CPU bundle](../scripts/run_wc_drop1_window24_cpu_bundle_r1.py)：四组控制＋原生真实运行入口的`--cpu-check`，共五命令；不重复已接受88数值计算，必须验证全部来源和runtime。成功还需完整24参数、matrix、原输入／校准、CPU禁止和真实原12端点文件通过。
- [一次收件工具](../scripts/capture_wc_drop1_window24_cpu_r1.py)与[离线接受器](../src/wcomr/drop1_window24_cpu_acceptance_r1.py)：按原句柄和时点检查，原PID仍活跃时保留等待，PID复用不误当原任务仍运行；检查全部payload／runtime、源版本、配置、数值88身份、五命令和真实生产证明。未来实际CPU启动后才按原receipt安排半程＋完整查收，本轮没有新CPU计时任务。
- [GPU监督](../scripts/supervise_wc_drop1_window24_r1.py)与[权限绑定](../src/wcomr/drop1_window24_execution_envelope_r1.py)：CPU证明与实际配置／source／scope／UUID／launch ID绑定，沿用现有v2短事务和逐UUID锁；完整上限预留、实际whole-wall加法结算。严格少于12沿已有自主规则，达到12必须具体完整卡批准，范围不缩。
- [自动CPU post](../scripts/watch_wc_drop1_window24_post_cpu_r1.py)：只等待原supervisor PID＋start_ticks，终态且source/config一致后单次调用已准备的完整24后处理；另一PID或另一GPU合法任务不作为本任务终态／释放失败。

完整科学范围不变：16正式＋8完整预热／864 pairs／1728 CFG／一次加载；全部12旧端点、四方法完整36 guided预热重复和两轮共同前21步，16个可配对正式视频完整93帧评分及六组固定比较保持。

## 本地验证与修复

[原件](../reports/wc_drop1_window24_lifecycle_source_local_preparation_20261018.json)：九项控制通过，包括原句柄／PID复用、提前收件拒绝、缺失和失败不当成功、源码／runtime／五命令／真实范围身份、严格12界限，以及真实临时文件锁与账本的监督测试。所有GPU、子进程均为明确模拟，账本只写临时目录。

监督测试验证：另一UUID保留原在途预留时，本卡仍可独立结束、结算和释放；忙卡准入拒绝时无GPU子进程、无新预留、无费用、锁释放，不停止或重启其他任务。初次测试发现输出父目录缺失导致结算写盘失败，[原失败记录](../reports/wc_drop1_window24_envelope_local_R1_output_parent_failure_20261018.json)保留；修复目录创建后完整九项通过，没有为通过而补模拟目录或改变范围。

当前152个Python依赖与原1686个payload没有覆盖冲突。五条实际CLI冷启动、远端CPU代码语法检查、提前ETA收件及未报价部署的拒绝检查通过；后两项均在SSH前停止。旧88数值源没有修改，本轮0 SSH／GPU派发／实际账本写入。

## 剩余接续

客户端GPU派发、完整GPU原件收件和最终逐帧／财务独立验收工具仍待补齐；本轮不把监督代码或本地测试称为完整GPU执行链已接受。N09完整40接受后，才能以真实组件区间生成已登记的整卡报价和配置、冻结新源，再部署实际生产CPU，通过后按fresh资源和权限执行原完整24。

N09 fresh R3实际生产CPU已接受，原GPU任务未启动，资源仍按每两小时一次查看；本轮没有提前再查卡。N10五模型和实际960输入已接受，评分生产／报价／GPU待，新质量分数0。累计cap226、origin79.99637737158223和全部历史账不变，最近接受快照实结110.8690611545／预留0余115.1309388455 GPUh，准入仍读fresh v2。F/B关闭，无训练、人评、付费VLM或OMR。
