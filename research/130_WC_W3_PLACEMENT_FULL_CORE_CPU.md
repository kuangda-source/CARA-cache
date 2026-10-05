# W3同配额位置交换：完整核心与CPU准备

2026-10-05。接续129已完成Human结果和128跨卡R4；本轮不重跑GPU、不改变已有C/D结果、失败成本或累计24GPUh账本。

完整B范围保持2父、16完整后缀、10新编码输出、2历史Native、6视频损失及4有符号双位置诊断。真实位置仍为Common CFG0 47→49、CFG1 48→50；Human CFG0 61→63、CFG1 46→48。旧冻结scope不修改。9600总/9570child只是费用重估草案，未选择GPU执行。

新增`rv0_placement_causal.py`将固定mask接口接入完整官方源派生的UniPC、WC、解码、安全管线与编码尾部。每父从step22开始依次OFF1/OFF2/BASE1/SWAP0_first/SWAP1_first/SWAP1_second/SWAP0_second/BASE2。OFF保持原自适应且不arm；BASE固定历史原mask；SWAP只交换同CFG两动作。四种重复均续推14更新/28CFG到终点，独立状态与缓存恢复；OFF和BASE要求与父完整轨迹、最终状态、五个pipeline事件及编码SHA一致。固定分支逐CFG刷新次数相同，保护末端动作不得override，非法源龄/自身历史/自然保护动作冲突显式失败，无fallback。

新增纯stdlib`rv0_placement_evaluation.py`检查完整行，生成10新+2旧、6损失与4桥的评分计划。新文件与预期根同时canonicalize，保留已发现符号链接路径修复的原则。20个范围/评分拒绝与两种根路径接受本机通过；这只是文件拓扑，不是视频或GPU。

完整CPU测试使用冻结的真实官方函数/Video2World类AST、Toy网络/权重/输入/解码/写出；flow OFF/ON各2父16后缀10模拟输出，并检查写出缺失、安全拒绝、前缀mask变化、自身CFG历史缺失及保护动作冲突时恢复。Toy交换位置从未instrument的Toy父轨获得，显式不冒充四个真实CAL位置。真实GPU可行性、真实视频、质量收益、干净端到端耗时仍待。

CPU代码已准备，实际服务器结果待执行与原件审计。仅独立新目录，旧Human/A生产CPU与GPU目录不变，CUDA禁止，账本不改。下一CPU通过后补生产CLI、监督器、终态审计及全93帧评分绑定；全部具体化后再处理新GPU卡范围。
