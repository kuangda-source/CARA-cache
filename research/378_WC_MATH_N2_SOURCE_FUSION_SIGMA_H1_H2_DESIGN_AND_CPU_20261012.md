# N2：来源一致融合与噪声间隔 H1/H2（预登记）

本轮是用户已授权的新核心方法开发；N1四自然父/12状态正在原独立目录运行。本CPU验证不修改638个在途字节，不使用未审计N1标签，不触碰用户暂缓P卡或原E2。

## 完整科学范围

四CAL、seed0、35请求/36实际更新、768×432、93帧、16fps；八方法32完整视频：Native、RA、原阶段β1 RA+A无P、NONZERO CPD、D来源A/P来源关闭A、相关误差融合H1、同融合H2、H2全动作固定但P位置以D替代。最后一项先从该场景H2实际完整动作记录冻结mask，再完整重新生成；是固定mask机制控制，不称部署策略。全部位置/拒绝/失败保留。

γ和风险表只来自N1完整审计后的四CAL开发标签，全局冻结，不按场景/seed调参。CPU合成参数标SYNTHETIC；它们不成为真实GPU参数。已有共享阶段alpha=1（step<25）、0.5（step≥25）和β=1、ROTATION050四层P、普通保护/guardrail保持。不采用FAST头省算，不训练。D只由本请求真实完整计算更新；P有正出生误差，不更新D。

## 新风险/成本模型的精确定义

融合发生在两个真正的post-RF A输出之间；γ端点只付相应候选头，内部γ付两种头，成本均保留。C动作可关闭A，四精度C/A/P/D共享CFG选择。

旧paid-probe guided_proxy输出误差范数，不是平方误差。N1统一teacher能量归一化后的OFFICIAL_C平方损失记qC。分来源拟合k_s=mean(qC)/mean((floor+local_proxy)^2)，来源C损失的单位因此显式映射为normalized guided MSE。相关融合A/C系数r_s=mean(qA_gamma)/mean(qC)，qA按N1冻结γ的相关二次式计算。D来源只有step8控制，后续/晚期是标注的TRANSFER；P也没有完整连续年龄标签，不能声称精确风险上界。

在当前已付浅层统计中，以sigma间隔构造范数漂移率d=local_proxy/max(|sigma_birth−sigma_now|,1e−12)。低维未来C风险为k_s*(floor+d*|sigma_birth−sigma_future|)^2，A为r_s倍。floor+drift的和式是经验保守代理，不声明误差独立或Gaussian。当前P风险为k_P*phase_P_floor^2；D当前新增近似误差为0。真实执行后才更新来源年龄/出生floor，已有latent与UniPC误差不被清空。

目标是每步费用+λ*propagation_gain*q，λ=D_pair_cost/(k_D*original_RA_threshold^2)，一次冻结、不用视频挑λ。若N1分母近零或尺度非finite则明确回退并修改新版本，旧表保留。H1一步与H2两步只推演已知sigma/来源/出生误差/当前漂移率；不预测未来真实latent，不免费算P/D、不访问teacher。未来σ为求解器已知schedule，未来漂移斜率保持当前值是显式TRANSFER假设。算法保留真实费用、原max consecutive P和末步dense保护；H2若无收益保留廉价H1，不否定融合。

## CPU实现验收范围

新实例只绑定控制器/读出工厂，固定上游/旧实现不改。CPU使用原生block/RF/UniPC源码加明确Toy输入/权重：两flow各四请求×八方法32完整采样，以及每请求γ0/γ1与旧ComparisonReadout两端点各两条完整路径16，合计96CPU路径。新旧端点全部36guided、动作、final和Toy视频逐位匹配；成对A共用γ/alpha；C/P不写D；H2 P→D控制无P；重放全36决策并扰动后恢复。另核对完整请求初态/RNG/网络模式与挂钩恢复。

CPU只能证明实现；当前尚无N2真实GPU/视频/净速度结论。N2正式卡成本在N1费用/标签后冻结，所有32路径、加载、预热、保存、失败和清理整体计费；严格>8才询问，不拆卡。完整方法结果须全部有效93帧评分及真实主计时，局部N1不得代替终点。
