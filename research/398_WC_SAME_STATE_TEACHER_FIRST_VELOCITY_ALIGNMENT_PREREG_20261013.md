# 四状态teacher首velocity控制：局部目标与终点对齐

2026-10-13，CPU实现及真实标签前登记。397完整H1卡仍在原595382e/661部署执行，不修改或并行新GPU。本项承接396三个精确同状态的局部改善与终点反例，不替代完整方法开发、独立确认或原E2/P13h卡。

## 要区分的解释

396中AV28一次A局部和终点均改善且未来深算8→7，Human/misc虽局部改善24.1%/60.7%却终点轻微退化。究竟是A的方向/强度不够合适，还是“在当前偏离轨迹的状态上接近完整输出”本身就未必改善到最终Native的距离？

在与396相同的四自然C状态上，额外取得当前完整D输出，仅在首步替换velocity，而不采用D缓存刷新。这是离线目标诊断，不是可部署加速器，也不把“当前teacher”当作Native轨迹真值。

## 四点与两臂，全部保留

|状态|step/age|原来源|两完整后缀|
|---|---|---|---|
|AV28 D早|10/3|D|C_REPLAY、TEACHER_FIRST|
|Human D晚|29/2|D|C_REPLAY、TEACHER_FIRST|
|misc P早|21/2|P|C_REPLAY、TEACHER_FIRST|
|AV51 P晚|27/1|P|C_REPLAY、TEACHER_FIRST|

沿原π0父路径，在动作前复制完整net/cache、latent、UniPC历史、RNG/generator、条件及算法所有状态。每点只运行一对共享同状态D teacher（2 CFG），保存后严格恢复。四个teacher都重新计算，增加4 pairs，避免旧复用输入/版本差异；不把AV51旧step26冒当27。

两臂首物理动作都为C、读出明确plain C，paid probe与工作源维护按C执行。C_REPLAY返回其真实C velocity；TEACHER_FIRST仅把该首c/u速度换成已保存的当前D速度。之后均同π0自然演化，首干预不续用、不更新可信D/working缓存、不用于在线路由，也不拟合γ/λ。

保留取得teacher时临时D的完整记录，但该离线D更新必须恢复，不带到父或后缀。首teacher读出因此不能称D刷新；原C维护和teacher网络输出形成刻意构造的因果控制。已有396 C/A后缀、匹配Native和父路径保持，新的C_REPLAY须逐步/终态/RGB对原C后缀等价，父144步对原π0等价。

完整科学范围：4父×36=144pairs、8后缀合计122pairs、4共享teacherpairs，**270pairs/540CFG、12新视频、4既有Native，一次加载**。首臂C/T顺序正反交替。CPU两flow四格须完整验证普通与诊断父、两臂完整终点、teacher未提交、首干预一次、尾部同π0、原条件/RNG/参数/缓存恢复。

## 分析口径和下一步

同状态teacher原始c/u、C首输出、latent/timestep、输入签名、前缀源/真D状态和物理C后状态均绑定。teacher注入值须与保存速度一致；两臂在首次velocity返回前的C计算/状态相同。未来动作差异是干预后果。首替换不是免费的实际算法动作，完整获取/恢复/导出/解码/清理计GPU账本。

全部12新视频审计93帧；比较C_REPLAY/TEACHER_FIRST与396相同状态A，报告每状态全部帧和未来动作变化。只评价终点保真，不以此代替物理质量。此单次instrumented诊断不作速度确认；decoder顺序/驻留影响已在396观察，不能用合并区间选赢家。

- teacher首输出也不优于C：支持局部teacher目标/历史偏差和终点不一致的线索，不能直接判A或D全程无效。
- teacher首输出改善而A退化：优先检查A插值/方向/阶段强度与实际目标，不急着增加回归网络。
- 两者混合：保留适用条件，后果价值需按状态估计；不给四个状态编泛化概率。

这项与完整H1方法共同推进；不成为所有候选/确认的新前置门槛。GPU完整费用、生产CPU、原件/评分与严格≤8准入另冻结；当前尚未运行此真实卡，不取消原H1、原E2或用户暂缓P13h。

## CPU R1保留与局部修正

独立R1阶段source72a6aed/649在真实源码的Toy完整采样中被前缀校验拦住，未CUDA/权重/GPU。原因是完整九字段controller状态误与来源三字段tuple比较；修正只核对前三字段的来源身份，完整九字段恢复校验保持。原R1阶段、日志与失败回执不修改，见[原R1回执](../reports/wc_teacher_first_velocity_cpu_r1_receipt_20261013.json)。下一独立R2重验两flow全部普通/旧C/新teacher父后缀，不缩科学范围，不改变397在途bytes。
