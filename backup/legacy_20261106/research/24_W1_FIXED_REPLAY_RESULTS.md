# W1固定schedule scalar闭环结果

2026-10-01；FROZEN_REPLAY_TECH_PASS_QUALITY_UNASSESSED。继续有界自动成像评价，暂不加W2或宣称方法收益。

源31a797d；official14项/scalar OFF-ON18项严格检查全真，8shadow点；原8候选全部72call/frozen full-skip轨迹及past-anchor检查通过，295次scalar预测、0fallback，57次自然判据与冻结位置不同（不能当在线复用收益）。7接受/1 VIDEO_REJECTED(robot_054)，原WC8接受；拒绝记录保留，不替换/补跑，安全拒绝不自动等于物理错误。

| 场景 | 候选outcome | scalar调用 | 自然判据不同 | 对WC PSNR/dB | temporal RGB MAE候选/WC |
|---|---|---:|---:|---:|---:|
| av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632 | ACCEPTED | 38 | 3 | 18.239 | 0.517995 |
| common_sense_6487f37f-ef57-49ca-afdc-d898922b5191 | ACCEPTED | 37 | 3 | 17.426 | 0.932309 |
| human_199 | ACCEPTED | 34 | 8 | 14.349 | 0.946153 |
| industry_084 | ACCEPTED | 38 | 0 | 15.064 | 1.009583 |
| misc_13398218_3840_2160_60fps | ACCEPTED | 32 | 14 | 10.979 | 0.989078 |
| physics_045 | ACCEPTED | 40 | 5 | 17.206 | 0.838991 |
| robot_054 | VIDEO_REJECTED | 38 | 8 | NA (无接受视频) | NA |
| av_51b45829-502e-4143-9c32-c026bd6ab191 | ACCEPTED | 38 | 16 | 12.765 | 0.318910 |

完整接受视频7/7与WC有像素差异；6/7帧间RGB变化较小，两个AV变化幅度明显更小。这是描述，未区分动作/运动量降低与减少闪烁，不能用smoothness或像素保真替代质量。带逐call hashing/首门shadow/顺序cold成本不作干净速度结论。CAL仍是可复用开发数据，无独立确认。

监督exit0、无stop reason，全部原PIDs退出/锁可用，GPU1释放24MiB/noapps；424监控点没有观察到其他compute，峰值26286MiB。所有已接受9个生成artifact重hash/source witness核验通过；首scalar ON与OFF相同不作独立样本。监督2177.784138秒/0.604940038h，累计3.59998488161299/4h，余0.40001511838701h，无在途。

证据：[runner](../reports/w1_replay_r1_runner.json)、[supervisor](../reports/w1_replay_r1_supervisor.json)、[审计](../reports/w1_replay_r1_audit.json)、[重新校验完整汇总](../reports/w1_replay_r1_summary.json)、[账本](../reports/budget.json)。

下一步：[MUSIQ评价卡](23_W1_IMAGING_EVALUATION.md)，原8分母/7可比对，固定所有93帧、source/checkpoint/input hash，上限600秒从原预算扣除，reject保留，不补人评。即使成像单维度改善，也不能称动作/物理/质量—时间方法通过；更大quality/clean计时/独立确认需有界后续资源方案。
