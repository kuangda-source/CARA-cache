# 相同S次数的刷新位置结果：保真明显改善，时间因素仍需拆开

2026-10-04。独立 `wc-forecast-placement-human-r1` / source395eae6dee91730cdb8f6f7997a1fba50913c2a1 已退出并完成独立审计。[机器摘要](../reports/wc_forecast_placement_human_r1_summary_20261004.json)、[六输出与来源审计](../reports/wc_forecast_placement_human_r1_audit_20261004.json)、[CPU视频指标](../reports/wc_forecast_placement_human_r1_metrics_20261004.json)、[费用和释放](../reports/wc_forecast_placement_human_r1_terminal_20261004.json)。继续WorldCache，下一先检验首次S及晚期两次S的作用；当前不训练路由器、不扩场景，也不把这一曝光oracle升级为质量保持加速方案。

## 已完成的实际对照

六视频全部完整93帧解码、36 solver/72 CFG/每臂一次官方prepare。全部采用相同38-deep/34-cache曝光掩码；两D/D的九门、五检查点各1216组件及完整pipeline通过，三份D视频SHA均为4d0f…82fb。旧legacy SD精确复现7caed…119b，再进入两个新位置。三候选均实际逐CFG执行6/5次S、共11次刷新/253算子，6/23/27继续dense，sim0.1/cdf0.98/no-PV；所有真实来源窗口、true-D隔离及native70清理通过。

所有数值相对于同输入、同初始噪声的官方WorldCache D参考，参考完整pipeline为210.452893秒。

| 方案 | 读取S来源的cache调用 | S来源读取数 | PSNR dB | mean luma SSIM | RGB MSE | pipeline秒 | 相对D单次wall减少 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 旧周期legacy SD | 26 | 26 | 17.8763 | 0.729829 | 0.016306759 | 208.814246 | 0.779% |
| 首次S匹配first_S_matched | 15 | 16 | 18.2083 | 0.744880 | 0.015106630 | 207.529735 | 1.389% |
| 自由位置minimum_footprint | 2 | 3 | 27.3758 | 0.927207 | 0.001829858 | 207.248970 | 1.522% |

首次匹配的MSE比旧周期低7.360%；自由位置低88.779%。三候选帧差量/参考分别为0.970494、0.974538、1.001724，temporal difference MSE为0.020970480、0.019353577、0.003082231。它们是编码视频保真、帧差及时间差分代理，不是动作、接触因果或物理正确性结论。自由位置仍与参考有差异，且没有独立场景/seed确认。

实际来源下界与此前CPU预测吻合：26→15/2；最大同CFG近似来源年龄为8/8/2。全卡759个真实S算子、43次cache读取S、45个近似来源读取。记录的平均selected fraction为0.677775/0.681416/0.670741，所以匹配的是刷新和算子数量，不是严格相同的稀疏工作量。四测量仅各一次、固定顺序；不得把约1.5%单次wall差解释为稳定速度收益。Native/少步/调过WC前沿、语义物理和CONF仍未验收。

## 结果改变了下一问题

保留首次S后，尽管后续读取近似的cache由26减少到15，保真只小幅改善；自由位置的改善明显更大。两个新方案共享九个S calls：45/47/48/49/50/51/52/53/54。它们的区别恰好是：first_S_matched加入23/24，minimum_footprint加入55/58。

23/24是第12个solver更新的两个CFG分支；55/58分属第28/29个更新。这里的早/晚是去噪执行顺序，不是视频帧顺序。相同11 S预算的两个新方案只交换这两次S，SSIM从0.744880到0.927207；与旧周期的比较还涉及其他位置改变。即使后续native预测窗口被连续D清空，之前注入的latent偏差仍可能影响最终视频。但当前结果尚不能证明是早期敏感性、晚期补偿、来源复用或这些因素的交互主导。

因此，暂不训练importance/risk head，不把来源读取数直接当risk target。先完成冻结mask下的两因素机制对照；若早期保护得到确认，再准备廉价的时间门和预算策略，恢复官方adaptive schedule后验证。曝光未来掩码的整体策略不能因选择器只读历史计数就改称online。

## 下一CPU设计：早期E×晚期L的四组合

[CPU来源设计](../reports/wc_timing_factorial_source_cpu_20261004.json)/[草案](../manifests/wc_timing_factorial_draft_20261004.json)使用本卡raw f6fb44d6b9f6133c23d7b7b291e22e53d60f55db14beb9117132b0e901d3d11c；先逐来源复现已实测的E1L0和E0L1，另外两臂只有来源图推导，没有新latent/kernel/video。

| 组合 | 公共九次S | 23/24早期S | 55/58晚期S | S次数/逐CFG | 算子 | 读S的cache/来源数 | 状态 |
|---|---|---|---|---|---:|---|---|
| E0L0 | 开 | 关 | 关 | 9 / 5,4 | 207 | 1 / 2 | GPU未做，CPU图 |
| E1L0 | 开 | 开 | 关 | 11 / 6,5 | 253 | 15 / 16 | 已实测first_S_matched |
| E0L1 | 开 | 关 | 开 | 11 / 6,5 | 253 | 2 / 3 | 已实测minimum_footprint |
| E1L1 | 开 | 开 | 开 | 13 / 7,6 | 299 | 16 / 17 | GPU未做，CPU图 |

每个因素只在对应两call把D换成S，其余mask和公共九次位置固定；四臂的S预算刻意不同，不能声称四臂同成本。定义相对同D参考的损失d：早期条件效应d(E1Lx)−d(E0Lx)，晚期条件效应d(ExL1)−d(ExL0)，交互为d(E1L1)−d(E1L0)−d(E0L1)+d(E0L0)。保留正负号，不截为“风险”；这些是固定mask下完整干预含传播的效应，不是隔离的局部误差或68的预算匹配RV收益标签。

下一只准备缺失E0L0/E1L1的生产接口和CPU合同、历史D/legacy复现止步及完整成本。可复用已实测两臂的字节级输出，但新卡必须重新绑定同模型/条件/RNG、旧原件和物理视频，不能把CPU来源图当已生成结果。现有forecast比较强制6/5配额，不能静默放宽旧guard；须显式新比较和独立范围、六输出分母/失败清理、实际CPU源码门。当前未选择下一GPU卡、未冻结其source或提交/预付。

若两种L背景下加早期S都明显恶化，支持优先保护首次可选刷新；若增加晚期S改善，须检查补偿和交互；若方向不稳定或只有同曝光seed有效，保持机制观察并回到强基线与跨seed验证。无论如何，不据单seed oracle训练路由器或宣称发表贡献。

## 全费用和资源已独立结算

实际GPU墙钟1642.439667秒=0.456233241 GPUh，覆盖导入/加载、两D/D、四测量、必要选择/来源/核、decoder/guardrail/write、退出和释放，低于独立2400秒上限。预算累计8.67188491753794/12 GPUh、41jobs，余3.32811508246206h，无inflight；2400秒预付已被实际费用替换，历史账目未重置。服务器监督账本的REQUIRES_RESULT_AUDIT字符串保留，接受证据见独立audit，不为改字符串重写服务器账本。

原supervisor2732730/timeout2732748/runner2732750均不存在，全局f1锁可获取，指定GPU为24MiB/no compute；770条监控峰值27730MiB，均无外来PID。源码payload、postrun无Torch/CUDA资产验证、费用和释放通过，CPU视频分析时原GPU任务已结束且账本不变。

[终态原件元信息](../reports/wc_forecast_placement_human_r1_runner_meta_20261004.json)raw 4,116,447 bytes，SHA f6fb44d6b9f6133c23d7b7b291e22e53d60f55db14beb9117132b0e901d3d11c；无损gzip148,955 bytes，SHA cad7fb12f0a07ff9b0584b37e28a7b3ac55cadfc7063656474c39e2ba1f09d1e。D/D快照单独保留。Git只存源码、文档、清单和小回执，视频/权重不入Git。原104点和本卡单次身份不重用，科学goal保持active。
