# WorldCache净正刷新动作的新seed复验（v5.4）

2026-10-08；在H-T36结果已曝光后提出，不追认为旧实验登记。继续WorldCache/W3，不训练Head/LoRA/专家，不增加稀疏搜索或人评。原负结果、失败费用和旧判据保留。

## 从发现到下一问题

[149完整结果](../research/149_WC_W3_NATIVE_RESPONSE_ONSET_CORE_AND_CPU.md)表明，共同61/63交换后恢复67响应，比69响应保真改善13.0508%，实际完整调用均21/19；65响应改善26.8017%，但多两次完整调用。两者仍比原WC差25.0273%/5.2544%。结束这组坏配置的补救定位，不继续搜索该场景最佳响应起点。

[129既有净正例](../research/129_WC_W3_HUMAN_APPROVED_EXECUTION_AND_RESULTS.md)中，Human199/seed0在call46（CFG1）原生建议C时刷新一次，其后使用同一原生自适应政策：全93帧LPIPS降低2.8080%，后续完整调用18→16。新问题是：**固定这个已知动作，换两个预先指定seed后，其终点保真和未来计算需求是否仍有优势？** 不基于新输出选动作/seed，也不把一个正例变成学习路由已经有效。

## 完整独立卡

`WC-W3-D46-FRESH-SEEDS-R1-20261008-A`，run `wc-w3-d46-fresh-seeds-r1`。同一Human199原prompt、seed1和2，样本分别命名human_199_seed1/seed2。Cosmos-Predict2.5-2B、768×432、93帧、16fps、35请求/36 UniPC-Karras更新/72CFG、guidance7、dense/eager、guardrails开启。每个seed从新原生采样获得匹配Native35参考，随后新原WC父轨迹在step22/call44真实状态分叉。

- 总计2条Native父、2条原WC父、12完整后缀、10新视频、两组signed效果；单进程共用一次模型加载。每seed六后缀顺序OFF1、OFF2、BASE_first、REFRESH_second、REFRESH_first、BASE_second。编码Native、WC父、OFF1、BASE_first、REFRESH_first。
- BASE为不干预的原生WC自适应，**不强制C**。REFRESH只在call46执行D，随后完全恢复原生自适应。若该点原生已建议D，登记为no-op并保留，不能换seed/调用或强制C制造对照。
- 全部后缀从同一完整状态/own-CFG历史出发；真实call45输入、输出、cache banks、求解器状态和pre46状态必须相同，call46原输入相同。两臂当前paid probe/native proposal一致；REFRESH只消费一次D指令，后续不使用固定父掩码、当前deep真值或未来教师。合法历史、有限性、age1–32、70reset与71/72D保持。
- 每seed三组严格重复，OFF/BASE都必须与原WC父后缀及终态一致；父/OFF/BASE编码字节相同。no-op时REFRESH也须与BASE终态/原始输出/动作一致（请求指令元数据可不同）。Native禁用缓存并绑定原类forward、36/72全算；Native/WC之间恢复初始完整状态及缓存配置，防止前一请求污染。
- guardrail拒绝、无合法历史、no-op、技术失败、缺评分均保留两seed原分母，不重抽、不补生成。技术失败先定位实现；不把缺失当方向负例。新seed仍是同一已曝光prompt的CAL复验，不是独立新场景CONF。

## 分析和决策

每seed记录`Δq=LPIPS(BASE,Native)−LPIPS(REFRESH,Native)`、`Δt=T_BASE−T_REFRESH`、各CFG完整调用、逐帧分布和两重复诊断wall均值。全93帧CPU FP32/Alex、原尺寸、不抽帧/裁剪，各seed新Native/WC/REFRESH编码与PTS绑定。分别报告两个seed和等权均值，不把帧当独立样本。

同时报告所有seed与原生建议C的eligible子集。原生D的no-op是适用条件，不算一次策略成功；两seed都no-op意味着未检验可干预位置的泛化，下一轮另登记区分实验。若质量/成本方向混合，先结合原始动作、完整数和逐帧误差检查条件，不用单项阈值否定W3。若保真持续正、成本可接受，再提跨prompt确认；若只在seed0有效，保留机制发现并讨论更合适的廉价规则。不因两seed结果开始训练。

wall包含恢复、哈希等诊断开销；此卡不提供干净端到端加速或物理/语义非劣结论。正式加速和独立CONF需另设计。

## 预算、CPU和权限

累计18.906279766/24GPUh、55jobs，余5.093720234h，无在途。完整成本依据原Human六后缀3246.492340秒、去掉一次重复模型加载99.023049秒，加入两条Native参考（各取已有最慢364.915542秒）及120秒准备/状态检查，再加20%余量与30秒释放。具体算式见[完整成本](../reports/wc_w3_d46_fresh_seeds_complete_cost_20261008.json)。这是代理规划，不能保证新seed的动作数或实际耗时，不恢复旧秒数deadline。

**完整预测超过2GPUh，因此本卡GPU须单独确认；累计24GPUh不自动授予这项例外。** 不拆seed或删Native/重复来绕过门槛。先把代码、监督、审计和评分路径准备成可审查结果，完成必要CPU和实际生产导入/source/assets检查，再只提一次具体整卡问题。CPU准备和只读验证按已有授权继续；新GPU提交/预留当前均为0。
