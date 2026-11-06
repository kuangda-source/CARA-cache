# 六输出小层组/低频S结果：保真改善有限，尚无质量—时间优势

2026-10-04。独立卡WC-SELECTIVE-HUMAN-R1-20261004-A/run wc-selective-human-r1/source 27df749a79ca3cb9fc3789a01bf1a73fa62211a2 完成一次提交、exit0。该后续卡来自既有自主goal和累计12GPUh，2400秒全cost/2370child；原104点≤1800秒授权保持已完成，不重提。仅曝光human_199/seed0，离线38-deep共同掩码为机制诊断，不是线上策略或独立CONF。

## 完成与独立证据

[六输出审计](../reports/wc_selective_human_r1_audit_20261004.json)、[终态源码/费用/释放](../reports/wc_selective_human_r1_terminal_20261004.json)、[指标](../reports/wc_selective_human_r1_metrics_20261004.json)、[机器摘要](../reports/wc_selective_human_r1_summary_20261004.json)。全部六条36个UniPC更新/72 CFG、一次真实prepare、93帧768×432/16fps完整解码；实际deep动作均等于38共同掩码。D/D九门、五处各1216原生组件/恢复与完整pipeline相同；三份D视频SHA一致，CPU全帧误差0/SSIM1。full-S视频SHA逐位复现上一轮811365…90e1后，才运行两个新变体。

实际policy/source/层回退/逐CFG序号/call70计数和来源失效/尾dense与核元数据独立重建通过。full-S和small-S分别22次S刷新、506/66真实算子；cadenced-S为11次S、253算子及27次全D。总825算子；三候选各26次后续cache读取近似来源，合计78。小层组混合残差仍标为approximate；间隔全D只保证自身当前状态下的真D，不能恢复官方latent轨迹。

[实际合同CPU控制](../reports/wc_selective_human_r1_policy_audit_cpu_20261004.json)三策略正例与9种错误记录拒绝通过，覆盖错层、非finite、近似冒充真D、换条件、未来来源、改掩码/序号、漏D刷新/漏reset。原共享审计默认11控制、partial binding8保持各自原source/hash；这些控制不替代实际文件和来源审计。

## 同一官方WC参考下的结果

| 变体 | 完整pipeline秒 | 相对D耗时减少 | PSNR dB | luma SSIM win7 | 帧差量比 | S刷新/算子 |
|---|---:|---:|---:|---:|---:|---:|
| fixed_D | 213.015 | 0.000% | inf | 1.000000 | 1.000000 | 0 / 0 |
| full_S | 206.442 | 3.086% | 17.8233 | 0.726741 | 0.966809 | 22 / 506 |
| small_S | 213.565 | -0.258% | 19.3702 | 0.785909 | 0.981109 | 22 / 66 |
| cadenced_S | 209.029 | 1.871% | 17.8763 | 0.729829 | 0.970494 | 11 / 253 |

D自身PSNR为无限（指标JSON以null/逐像素一致表示）。small-S相对full-S的RGB MSE下降29.966%，SSIM改善约0.05917，但相对官方WC仍有明显编码差异；本次耗时增加0.258%，没有显示加速。cadenced-S的SSIM仅0.729829，接近full-S0.726741，耗时下降1.871%；这一均匀低频方法没有解决保真缺口。

各变体只运行一次，固定D→full-S→small-S→cadenced-S顺序；全部wall含真实prepare、必要选择/来源/核检查、decoder、guardrail和write，首次S保留。D/D观察wall不入部署比较，host分段不作CUDA阶段归因。小幅耗时差不能作为重复确认；full-S历史复现也不是新独立场景。编码保真不是语义/物理质量接受，未设事后SSIM阈值；Native/少步/合理调过WC前沿与独立CONF仍缺。

## 关键诊断：降低S频率没有清空原生预测窗口

[原件CPU来源统计](../reports/wc_selective_human_r1_cache_footprint_cpu_20261004.json)显示各臂均34次cache调用。full-S/small-S为8次dense+dense、8次dense+sparse、18次sparse+sparse；低频S为8次dense+dense、14次dense+sparse、12次sparse+dense。低频虽然把S算子减半，后续26次cache仍至少读取一个S来源。

这区别于用于准入和选择的true-D历史：true-D元数据完全隔离并已通过，不意味着原生两个残差预测来源都已变为D。当前交替S/D在这些实际cache调用上没有清空近似来源。计数证据可解释为何“多一次D”未必保护后续预测，但不能据此断言终视频误差全由复用造成；本轮没有同状态反事实分叉或可加因果分解。

## 费用与下一步

全过程1671.191979秒=0.464219994GPUh≤2400；预付按实际替换，累计8.215651676683272/12GPUh、40jobs，余3.7843483233167277GPUh，无inflight。原三个PID2721519/2721535/2721537消失、全局f1锁可取、指定GPU24MiB/no compute；783条monitor峰值27754MiB。CPU分析未新增GPU。完整原件4,009,704bytes/SHA a752a19587552ca4842a3dec0683bbf42891a3a774c4987ca104c58cc0364265，[gzip原件](../reports/wc_selective_human_r1_runner_20261004.json.gz)与D/D快照分别保存，视频/权重/大张量保留服务器。

继续WorldCache，但当前23层S、三层S和交替低频S均不升级为质量保持加速候选，不据这张卡扩样或加入Trust Head/LoRA/训练。下一先用CPU重建原生两来源窗口的持久性与同CFG年龄，具体化“连续真D清空窗口”或限制近似残差复用的对照，并计入多出的deep计算/选择成本；不能把metadata清空当作latent纠正，也不能只少复用而不记额外费用。

如简单近似/寿命控制仍不可靠，应收缩或关闭当前S参数组合，把资源回到近似器和同预算计算分配；需要在具体可执行对照和成本出来后判断。当前没有下一GPU卡或预付，不重提本卡；W3有符号同状态预算匹配的刷新价值保持[68设计](68_WC_COUNTERFACTUAL_REFRESH_VALUE_DESIGN.md)，本轮不是RV收益标签。科学goal保持active。
