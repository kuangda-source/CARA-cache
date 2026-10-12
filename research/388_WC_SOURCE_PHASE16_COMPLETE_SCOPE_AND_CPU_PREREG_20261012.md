# 来源/阶段自然16：完整当前状态校准与CPU验证登记

承接385/386/387及[优化设计](../plans/WORLD_CACHE_SOURCE_CONDITIONAL_BASELINE_RELATIVE_DEVELOPMENT_20261012.md)。384全54与全93已验收；新的校准卡不是原用户暂缓13h参考卡的缩卡，也不改E2的确认目标。完整采样/原件/实际生产CPU均通过，唯一真实GPU卡已准入并启动；实际16状态标签和全原件终态仍待。

## 科学问题与完整范围

原四P_OFF父策略、seed0、完整36更新/72CFG、768×432/93帧。固定16自然位置来自已登记的源/阶段/年龄选择，不看teacher/本轮候选胜负重新选点；其中Human/AV51晚P的父动作P，必须在执行前捕获状态。

每点同一实际latent/noise/条件/solver/cache/β/projection和RNG上评四种候选：C、旧D参考阶段A、冻结γ相关融合A、实际新P；共享一个真正同状态D teacher。γ保持0.7235237005554214，α遵循原阶段，不搜索新γ。D源两种A等价控制保留。新P不晋升真D，不将其出生误差设零。

四诊断父×36=144 ordinary pairs，16点×5个离线pair=80额外。进一步核对发现，原clean P_OFF保存终态/动作/视频，但没有逐步guided；因此增加四条普通π0重放，直接对比诊断的全部144步，不虚构旧guided哈希。完整八路径合计288普通＋80离线=368pairs/736CFG、64候选比较＋16teacher、16原件×12tensor=192tensor。八路径终态/动作/93RGB与已接受原P_OFF对比。不能因某点不可恢复而补选/删格；完整分母16和失败保留。

## CPU范围

两个真实flow入口、四Toy请求，每请求baseline/diagnostic两条全36路径，共16完整CPU路径；各flow16点，总32点和160个离线pair。合成场景特意让早D/早P/晚P/晚D都自然出现，并至少包含每请求一个原父P点。Toy元数据选点与真实16位置独立，禁止由Toy策略改真实参数。

全部候选和teacher前后完整物理/CPU-owned序列恢复；实际候选primitive可与π0动作不同，但不能绕过保护、无源/无paid proxy、projection不兼容或consecutive P限制。标明是离线校准，不假称原政策会选择该动作。

检查：C/A/P不写可信D；读出不变working source；P创建真实正误差工作源；D源A等价；新P/C/A输出与恢复后父实际动作逐位一致；全部36guided/动作/终态/Toy视频一致；原安装、条件对象、RNG、solver、缓存守恒。16点状态存在性、local标签、CPU通过和真实GPU完成分别报告。

## CPU结果与修复记录

R2完整两flow/16路径/32点/160离线pair在78.600725秒通过。独立读取全部32原件/384tensor并重构四读出的绝对guided MSE、归一化MSE及CFG交叉项，四个source/phase格各8点通过，CUDA未初始化，0GPU和账本写。这里全为合成CPU证据，尚无真实16标签。

R1合成晚P选点处连续P已达2，真实执行器拒绝；第一次finally恢复又触发健康边界守卫。保留两个原错误和stage，只修合成选点合法性与异常传播：失败pair不恢复毒化状态，成功pair才恢复；真实16点、参数、保护/连续P/projection限制均不放宽。真实16点已逐点核对partial readiness和连续P合法。

[CPU R2完整回执](../reports/wc_source_phase16_cpu_r2_receipt_20261012.json) · [独立384tensor](../reports/wc_source_phase16_cpu_r2_independent_raw_20261012.json) · [R1保留失败](../reports/wc_source_phase16_cpu_r1_receipt_20261012.json)。

## 费用与执行

局部pair计时包含两probe，属于研究挂钩下的当前动作耗时，不能直接覆盖旧post-probe增量费用或叫clean-video latency。完整startup/import/load/诊断/保存/失败清理都计费；实际后续报价需保持同一边界/维护开销。原快照逻辑cap、两-copy和workspace/paired-prefix headroom门不放宽；复用已有恢复框架，不新增通用跨进程快照工程。

完整卡 `WC-SOURCE-PHASE16-BASE4-DIAG4-FULL368-R1-20261012-A`，预计3.209418668GPUh，包含八条重放、16teacher、实际新P与两A/C、全部capture/五次restore、原件和视频保存、清理及1.5倍余量；并非所有组件均实测。绑定原16选择、旧γ/π0参数和全368范围，后续真实生产CPU/freshGPU门仍必需。≤8按用户持续授权自主，严格>8问完整卡，不拆规避。旧P13h/E276状态保持，不训练/OMR/新增人评。

## 实际部署与在途边界

source `4d51485db61a2f20541454e63254546823d8dc07`、652冻结payload；实际生产CPU包含完整输入/参数/资产/采样字节、实际child命令路径与哈希、普通guardrail、十项范围拒绝检查，通过且无CUDA/新GPU费用。第一次包装代码语法错误发生在服务器stage创建之前，0GPU/账本写；已增加本地远端代码编译，失败记录保留。

fresh A6000指定UUID、24MiB/noapps、kernel f1独占锁与当前余额全部准入，唯一监督424953、runner425044、自动CPU watcher424954已存活。第87提交，完整8/16/368和旧参数保持；观察时0/8路径/0标签，不能据启动报新机制或保真结果。启动前实结64.204693096/cap104.971363333，余额40.766670237；当前账本used=cap只表示在途预留，全wall实费终态结算。原384与CPU stage不修改，不因SSH短暂断连重投。

[实际生产CPU](../reports/wc_source_phase16_r1_production_cpu_accepted_20261012.json) · [完整卡启动](../reports/wc_source_phase16_r1_GPU_launch_20261012.json) · [原句柄/source/现场](../reports/wc_source_phase16_r1_start_observation_20261012.json) · [部署包装失败和修复](../reports/wc_source_phase16_deploy_wrapper_fix_20261012.json)。
