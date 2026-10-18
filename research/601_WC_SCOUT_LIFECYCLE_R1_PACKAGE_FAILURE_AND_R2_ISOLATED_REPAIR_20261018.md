# 生命周期CPU R1失败定位与R2隔离打包修复

**两张R1生命周期CPU均未通过；根因是共用验证代码需要两张卡的配置，而各自的隔离stage只打包本卡配置。** 已保存原1787源／runtime、退出状态、完整日志与独立未接受回执，原stage不改、不重派。R2只修复部署依赖清单，算法、真实生成入口和已验数值保持原样。

## 1. 原件及明确根因

[逐原件诊断](../reports/wc_scout_lifecycle_R1_terminal_failure_and_R2_packaging_diagnosis_20261018.json)：

| 原CPU | 全源／runtime | 实际CPU wall | 已执行命令 | 结果 |
|---|---|---:|---|---|
| CAL12 R1 | 1787源全部一致 | 4.456899秒 | 第1组完整20控制 | 7个错误，全部缺BANK24配置 |
| BANK24 R1 | 1787源全部一致 | 4.142946秒 | 第1组完整20控制 | 10个错误，全部缺CAL12配置 |

两者均在首命令exit1后停止，第2项实际入口依赖核对未执行、CPU proof未生成。缺失文件分别为`configs/wc_scout_bank24_production_entry_r1_20261018.json`、`configs/wc_scout_cal12_production_entry_r1_20261018.json`，都不在原对应payload里。完整收件及独立未接受回执为`reports/wc_scout_<KIND>_GPU_lifecycle_CPU_R1_collection_20261018.json.gz`与`independent_acceptance_20261018.json`，source59be5980和所有失败原件保留。

这次是我在打包共用测试依赖时的遗漏。原已验248＋10数值和c1c95ce0真实生产入口证明未失效，也没有执行新的模型或视频。

## 2. R2最小修复与本地隔离验证

`wc_scout_gpu_lifecycle_cpu_r1.py`将配置闭包从单个本卡配置改为**两份已经冻结的配置及引用**，并在任何SSH前断言两文件都在注册payload中。没有改变测试逻辑或删减测试；没有改变计划、请求、报价、采样器、观察器或CPU接受规则。

每卡新stage预计1789源，相比R1只多另一份配置及其已有报价；原1772执行依赖字节变化为0。新stage继续直接以原已验c1入口为只读基底，不在失败R1上修改文件，不借用原24 scope通过标志。

[隔离包实际本地控制](../reports/wc_scout_lifecycle_R2_isolated_package_controls_20261018.json)：将每卡**实际注册overlay**复制到独立临时目录，以该目录为工作目录和唯一项目PYTHONPATH，各完整运行20项原控制，两卡均exit0。该检查可以复现并排除“工作区有文件、隔离stage却缺文件”的原失败机制；这不是服务器CPU通过，也不作为科学结果。

## 3. R2真实CPU与后续

冻结修复源码后，分别单次部署：

```sh
.venv/bin/python scripts/wc_scout_gpu_lifecycle_cpu_r1.py deploy --kind CAL12 --stage .sync/wc-scout-cal12-gpu-lifecycle-cpu-r2-20261018 --output reports/wc_scout_CAL12_GPU_lifecycle_CPU_R2_launch_20261018.json
.venv/bin/python scripts/wc_scout_gpu_lifecycle_cpu_r1.py deploy --kind BANK24 --stage .sync/wc-scout-bank24-gpu-lifecycle-cpu-r2-20261018 --output reports/wc_scout_BANK24_GPU_lifecycle_CPU_R2_launch_20261018.json
```

仍为完整20控制＋实际原入口／全部矩阵／完整依赖核对两命令，未运行前不判通过。复用数值248＋10及原入口两命令，不再次采样；source、registration、原句柄和+180／+360秒检查时刻由真实launch追加。未知派发不重放；长任务半程和ETA各一次，不持续监听。

原N10已接受不再查；原Window24资源任务00:51和原source／完整四臂不改，当前不提前查询资源。GPU仍原24完整接受→CAL12→四CAL冻结gate→BANK24，X-R共享。新卡预测／完整计费上限仍1.876666667／2.5和3.407222222／4.5，当前新增GPU／预留／费用均0。cap226／origin及历史、strict<12直接执行、F/B关闭均保持。
