# M2：终点指标梯度已接通，继续真实模型反向

2026-11-01。继[M1完整机制结果](834_CARA_M1_COMPLETE_READ_WRITE_MECHANISM_AND_M2_CONTINUATION_20261101.md)，本轮补齐两项实际Linux CPU组件：原Wan2.1解码函数的小权重前向/跨时间反向，以及固定真实Alex权重的全93帧输入梯度。两个原容器均正常退出，新增GPU与中央账本事务均为0。

这使M2的终点估值链更具体：对完整浮点视频求Alex梯度，再经原时间耦合VAE与实际UniPC/缓存转移向前一状态传播。完整真实Cosmos伴随和固定19D硬交换收益仍待验证；本轮不增加科学结果行。

## 两项原终态

|组件|实际检查与结果|范围|
|---|---|---|
|Wan2.1校准解码|三项通过，36.916秒，原容器退出0；一帧/93帧对原no_grad接口逐值等价，调用者缓存保持；最后一帧对前一latent块梯度非零，方向差分误差约4e-15|实际Linux导入、固定原decode源码；明确小卷积权重，尚无预训练VAE或432×768显存证明|
|Alex终点输入VJP|三组通过，38.339秒，原容器退出0；93帧流式损失与完整计算图值相同，最大梯度差0；两档差分相对误差0.0323%/0.0353%|真实固定AlexNet与LPIPS0.1线性权重；合成93×64×64视频，无原实验视频或真实Cosmos/VAE权重|

原件：[VAE接受](../reports/cara_read_write_vae_Linux_CPU_accepted_r1_20261101.json)、[Alex接受](../reports/cara_read_write_terminal_Linux_CPU_accepted_r1_20261101.json)、[组合进展及SHA](../reports/cara_read_write_M2_terminal_progress_r1_20261101.json)。VAE实际源码885aaa…65bb；真实指标的两个checkpoint沿用正式评分固定SHA，只允许加载这两份。两项均独立1CPU/4GiB、零额外swap、无网络、无GPU，原26核；600秒工作/60秒退出界及8GiB宿主余量核验通过。

## 计算边界

`StreamingAlexTerminal`每次仅保留一帧Alex激活，完整93帧等权平均；自定义一阶VJP再交给上游VAE。四项本地控制包括合成指标下流式/整图等价、clamp像素零梯度和有限差分、小型原因果VAE到93帧终点的链式梯度、分母及冻结模式拒绝。真实Alex在Linux上又独立核验了值/梯度、两个epsilon和部分视频/外来权重拒绝。新旧接受器10项回归通过。

拟合边界是原解码输出经`(1+video)/2`、clamp后的未编码浮点RGB，再按Alex输入归一化。正式硬候选仍以完整编码视频Fidelity-v2评分接受；浮点拟合值不冒充编码后科学分数。64×64合成输入也不冒充432×768生产视频。

流式指标只减少Alex激活存储；完整解码视频、Native及视频余向量仍占空间，VAE时间缓存与真实模型激活另外计算。它没有证明48GiB能承载全轨迹反向。校准适配保持原生产no_grad入口不变，未静默引入逐帧独立VAE、latent MSE或Euler近似。

## 下一项实际工作

1. 绑定实际加载的Cosmos网络/tokenizer身份，接通输入及完整缓存VJP；按真实硬C/D与原生产前向做数值对照。
2. 保留三个物理窗口槽、validity、step/sigma及两CFG来源；对warmup、移位和原70-call reset逐一核对。不能只保留最后两个逻辑anchor。
3. 在私有校准入口验证分块重算与buffer/参数恢复一致，测实际VAE93帧和单转移峰值，再冻结全段GPU报价。原网络已有checkpoint入口，复用前仍须证明与functional_call及实际后端兼容。
4. 准备完整M2：同Uniform19、两旧FIT/seed0、相同合法约束与硬候选额度，对比原S局部q、同伴随read-only及full；完整硬swap终点评价决定是否接受。既定每轮至多两个新候选与后续M3上限不变。

M1原14路径、八评分、1.500620266GPUh唯一结算和已删除检查保持；不再派发、评分或收费。M2新卡不能继承M1的四卡账本例外；在整卡可审阅后再按原权限边界处理。当前只有两卡CPU准备，不探四卡、不读保护TEST。

本轮一次准备命令误填完整Git版本，在本地`git show`阶段即被拒绝，发生在凭据加载和SSH之前；[原拒绝记录](../reports/cara_read_write_terminal_CPU_local_source_refusal_r1_20261101.json)保留。随后使用Git返回的已发布版本660b08759a23f65ddbec13b6b49f9f24b0d8e26e完成唯一实际Alex CPU启动，没有远端重派。
