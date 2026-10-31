# 817 — 预算搜索完整验收与一次冻结赢家

原预算搜索完整 **112/112路径、51/51次双FIT查询** 已通过固定源完整读者接受。原GPU于2026-10-31 23:56:56.112259退出释放，原guardian实耗 **7.197644817485577GPUh** 已中央唯一结算，低于原14GPUh硬限；原CPU读者于11月1日00:25:44.617394正常退出0、无OOM，耗时456.939373秒。没有再次生成、重复评分或重复收费。

## 完整校准结果

全部初始1＋SA30＋HC20完成，共51个不同mask、0个重复查询。按原规则选择完整51查询中的最小双FIT等权RGB MSE，第39查询（HC）胜出；未改选择目标、未使用CHECK或新输入。

| FIT输入 | 初始Uniform19 RGB MSE | 选中布局RGB MSE | 相对下降 |
|---|---:|---:|---:|
| AV28 | 0.01638323184300855 | 0.006514209789262223 | 60.2386% |
| Human199 | 0.06912334525427020 | 0.04172696899050656 | 39.6340% |
| 两输入等权平均 | 0.04275328854863938 | 0.024120589389884393 | **43.5819%** |

平均下降以“1−选中均值/初始均值”计算，不是两个百分比的平均。RGB取原完整93帧、guardrail后/编码前CTHW float32数据，不是MP4解码后的LPIPS。

选中19个D位置：

```text
1,2,3,4,5,6,7,10,12,14,16,17,18,20,22,24,25,32,36
```

策略指纹：`55f7dacb7761f9e879e4478eb8d65932cc54cddc6ef57538884f6c5fa6a8ead8`。

一次冻结SHA：`f1e0b08b9dc31fd9cd3c02a80b01cbb874e9348003ec6aad3a5aa9f82d848c86`。原远端冻结保留在该run的`calibration-frozen-mask.json`，本地副本保持原字节；没有覆盖A32或S的冻结。

## 证据与接受范围

完整读者来自原GPU source `33fc2263405baaa77f6dbcfdfdfabedb20f066bc`，完整接受模块SHA `9397917e26ce6194e405b03d5cc618bc9d00c393c300744139ab4b9d4eb12064`。它先核对原账单、唯一结算、四原GPU句柄终态和真实释放，再逐项回读112条原RGB/生成工件，重建51次确定性查询，并检查源、精度、RNG、固定D预算、Native/allD及计时开关等价。回读不允许执行新请求。

原CPU容器ID `19aa511e058d161bcdaccd3cf33686aeedef0ffe78f4331b440c0bcf71a22e7f`、reader PID2654036/start ticks675839119均与原启动记录一致，最终不再存活。2CPU/8GiB/无额外swap/无GPU/无网络边界保持。接受回执、冻结和collection均按原始字节导出并核SHA，本地再次检查51行均完整、三个阶段计数、每行双FIT均值、首次最小值选择、原账单及冻结对应关系；这不是重跑原验收器或重新评分。

## 解释与下一步

43.58%是**被优化的两个旧FIT输入上的RGB MSE校准下降**，不构成独立泛化、LPIPS改善、搜索收敛或部署时延收益。相同14GPUh允许上限不等于S与搜索实际费用相同；搜索完整实耗7.197645GPUh，原S采集实耗3.039352GPUh，范围与评价方式不同，必须分别披露。

选中策略与准备中的Uniform起点S-BR/DIAG、S-CFG策略指纹均不同。因此既定六方法/24逻辑位置端点比较仍按标准32物理路径准备，不能套用25路径同mask去重。真正端点绑定、受影响策略CPU、整卡入口/资产/存储组合、汇总图表及最终报价仍待；没有自动批准或启动下一卡。

两个一次检查14h和14h-2均已删除。中央cap226、旧未知责任16.5保持；结算后可用18.515811725GPUh仅为结算时快照。A32冻结、B36/S/Q原结果、WC/RA FIT UNMATCHED和旧CAL范围保持。

- [完整机器摘要](../reports/cara_budget_successor_complete_summary_r1_20261101.json)
- [原完整接受回执](../reports/cara_budget_successor_complete_accepted_r1_20261101.json)
- [一次冻结原字节副本](../plans/cara_next_stage_20261028/mainline/r2/BUDGET_SUCCESSOR14_FROZEN_MASK_R1_20261101.json)
- [完整collection原字节副本](../reports/cara_budget_successor_complete_collection_r1_20261101.json)
- [全部51查询CSV](../reports/cara_budget_successor_complete_queries_r1_20261101.csv)
- [原CPU终态及原字节捕获](../reports/cara_budget_successor_final_CPU_capture_r4_20261101.json)
- [原结算](../reports/cara_budget_successor_final_settlement_r1_20261101.json) · [释放接受](../reports/cara_budget_successor_final_release_accepted_r1_20261101.json)
- [自动检查清理](../reports/cara_budget_successor_complete_check_cleanup_r1_20261101.json)
