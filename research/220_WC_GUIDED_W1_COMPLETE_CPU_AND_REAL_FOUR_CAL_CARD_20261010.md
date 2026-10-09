# guided-W1 完整采样CPU通过与四CAL真实整卡（2026-10-10）

完整CPU R2 source5c53399／200源实际98.868498秒退出0，原3885944／3885945消失，[原件与独立检查](../reports/wc_mf_a_collection_sampling_cpu_r2_terminal_20261010_capture.json)通过。flow OFF／ON各完整八父，另flow ON最后父写出失败完整八父，共24路径／864 UniPC更新／1728正常net；两成功批实际重读576 guided、16 latent、128 post-RF分支速度。四场景的采集开关父轨迹、最终latent、完整mock输出、条件字段／solver物理状态／RNG相同，教师不写锚点；十种语义变异、两文件实际截断及最后父写出恢复均执行通过。

它实际执行新batch、已安装原WC／RF／condition／完整UniPC与普通安全管线控制，权重、attention、prepare／decode／writer为声明的CPU夹具；没有Cosmos CAL、真实视频质量、GPU、训练或clean速度。首次完整CPU缺条件帧key导致默认1与zero-mask断言冲突的失败、核心R1—R3失败、所有旧正负记录保留。只显式传入T2V零条件帧的独立修订已通过，不改生成算法。

[真实完整卡登记](../manifests/wc_mf_a_collection_r1_preregistration_20261010.json)为 **WC-MF-A-GUIDED-W1-COLLECTION-R1-20261010-A**，独立run `wc-mf-a-guided-w1-collection-r1`。它回答：实际同状态、两CFG最终速度监督能否选出有意义的共享α，从而把W1接到RA／部分刷新组合，而不以单分支残差MSE替代guided目标。

| 项目 | 完整范围 |
|---|---|
| 场景 | AV28／Human／misc／AV51，原CAL seed0 |
| 视频和求解器 | 768×432、93帧／16fps，35请求→36 UniPC/Karras更新，guidance7（实际8／−7） |
| 原父对照 | 每场景固定共同D6采集OFF／ON，8完整父、8完整视频槽、288更新、576正常net |
| 同状态监督 | ON在CC的step12／30；8起点，历史D分别[6,7]／[19,25] |
| 方法 | ORIGINAL、β=1、原标量W1、从本步paid probe继续深层的DENSE教师 |
| 附加计算 | 16 score-only deep分支／416 deep-block调用、48附加head；64分支速度、16原始tensor文件 |
| 校准目标 | 真实post-RF FP32 BCTHW直接guided MSE；α∈{0,.5,1}，场景等权、并列选小α、λ=0 |

候选和教师不修改在线父缓存／校准锚点。共享α可以合法选择0；这不否定组合方向。选定α是曝光CAL局部目标的开发结果，不是终点视频质量证明，之后尽早接BASE-R与部分MLP的完整闭环，不要求A先单独获胜。保持所有缺失／拒绝场景原样，不换样、不缩拆对照。新批保存条件逐字段、实际mask和完整raw／numerical求解器配置，旧跨轮条件整体SHA不等的false不改。

[整项成本](../reports/wc_mf_a_collection_r1_complete_cost_forecast_20261010.json)沿已验收原件的较慢完整父925.025799秒×8、加载620.284490秒、附加同状态69.116672秒×8，另计恢复／保存／head／清理1756秒，整体乘1.2，得到 **3.4431414203119153 GPUh**。这是经验保守估计，不是严格时间上界；没有旧逐卡秒数截止。单次完整≤4 GPUh已获自主权限，不以拆分或删除范围准入。

[237源生产配置](../configs/wc_mf_a_collection_production_r1_20261010.json)及[本地22变异／全载荷AST检查](../reports/wc_mf_a_collection_production_local_static_controls_20261010.json)已实现。下一唯一真实生产CPU核对模型／guardrail／当前源／完整请求／批次proof和配置，再同源选定CPU与fresh UUID/sm86／VRAM／compute／锁／账本／磁盘准入，提交完整卡；GPU退出后在CPU实际重读所有tensor、完整解码八视频并独立重建共享α格点、全wall计费。当前尚未选定或执行新GPU，准备不能冒充真实校准结果。

[飞书组会](https://lcnssrlun9lz.feishu.cn/docx/HTSIdK0uLofCG5xUI1IcTKaCnAh)已追加R2保真与下一批，[全文核验](../reports/wc_ra_complete_video_r2_feishu_verification_20261010.json)revision42、179旧块完整保留、四新块正文与链接相符。RA第二工作点平均较首版保真改善10.65%，仍较WC失真高10.44%，共同刷新重复正信号／负帧保持，详见[219](219_WC_RA_R2_FIDELITY_AND_GUIDED_W1_FULL_PIPELINE_NEXT_20261010.md)。

权威结算仍32.674095026904／77.89524658965853，新增48窗口余45.22115156275453GPUh，70提交、无GPU在途。完整≤4自主／>4具体确认，旧16路6.704卡未批准，窗口起点不重置、无非必要人工评审，goal active。

后续生产CPU32.826063秒与选定CPU32.380441秒全量通过，独立原件绑定。source76516e4完整237源真实GPU卡已在≤4自主权限内唯一启动，详见[221实际执行](221_WC_GUIDED_W1_FOUR_CAL_REAL_EXECUTION_20261010.md)。本节之前尚未选定／未GPU的表述保留原阶段，不重复提交。
