# 自动质量资源准备：四份现有权重实际哈希与ViCLIP资源缺口

2026-10-16。**等待N07整卡审批期间，完成了不占GPU的评分资源核查：四份现有权重可读、大小保持，MUSIQ权重和架构与原测量协议相同。** 这减少了后续N10的部署不确定性；未加载指标模型或读取任何最终测试视频，尚无新质量分数。

## 已有资源的实际身份

本次只读实际生成Python环境和明确的缓存路径，四文件在流式读取前后大小/mtime/inode稳定，0读取错误。

|模型|实际字节|完整SHA256|
|---|---:|---|
|DINO|343242485|`bf34ad0f424b9029b593e8dc3ed553bf26e88bcba0d32bf3e62a6209cb64c85e`|
|AMT_S|12038359|`07e7e03405c213fe4405678db9b42d05671e48c56faf6a441b99bb0047d3cf77`|
|RAFT_THINGS|21108000|`fcfa4125d6418f4de95d84aec20a3c5f4e205101715a79f193243c186ac9a7e1`|
|MUSIQ_SPAQ|108610983|`358bb6af275e28ea56821d44fb55c6cb83645db11f394d3ad65b2d149965ab50`|

MUSIQ SHA与原SPAQ测量协议逐字一致，实际`pyiqa==0.1.10`架构SHA仍为`ddab924a5ff529e1668404fa058777a9d00890390166c2b12ef7fffdc0baebb3`。DINO/AMT/RAFT这次绑定的是现存文件的实际字节身份，尚未额外证明官方原下载字节或模型载入/推理成功；后续严格模型CPU需与这些哈希绑定。

同一回执记录了缓存DINO的12份Python源码SHA与hubconf文本，以及实际Torch2.7.1、torchvision0.22.1、VBench0.1.5、PyIQA0.1.10和依赖元数据。包元数据不替代真实模型导入；评分仍使用493选择的固定VBench代码，避免与已安装旧版本混用。

## 仍需取得的资源

原指定`ViClip-InternVid-10M-FLT.pth`在本次五处限定目录均未发现：用户VBench缓存、用户和项目的指定HF模型缓存、项目models及用户gkd/models；这些目录当前都不存在，没有遍历整机或据此声称整机没有该文件。原期望为1,710,545,812字节、SHA256 `7a4d6ad6eac6632db3693f4b97f9f8f6445b65b1e139a6fc6686150522238c56`，保持493的HF固定修订，不换成其他CLIP或4.14GB的不同ViCLIP文件。

为原六维评价补齐资源，准备只在fresh `.sync/wc-N10-viclip-resource-r1-20261016`取得这一个公开固定checkpoint；不改全局缓存、原生成stage或依赖环境。worker逐字节检查完整大小/SHA，只有完整匹配才把part重命名为正式资源；失败保留part和错误，禁止把残缺文件当模型。四项小字节CPU控制通过，网络为mock、不是已取得权重。

资源worker本身为纯标准库、CUDA可见集置空，不import指标/生成模型或触发GPU，不占用GPUh预算。Git绑定源码单次派发后，按约30分钟一次查收；只接原PID和原文件，独立重算终态SHA，未完根据剩余字节估时一次，不持续监听或重复派发。下载为准备资源，并非启动一张质量评分GPU卡。

项目分区当前可用约431.54GB，原缓存分区约26.37GB；该资源留在独立项目stage。正式N10仍待完整固定代码/资源的模型CPU验证、最终160输出与960指标位置及完整费用，不因资源存在宣称已评估语义、运动或物理质量。

## 主线与权限保持

N07真实生产CPU已完整接受501。完整180卡15.055555556GPUh及拟议同一累计cap113的具体询问仍待人类回复；当前服务器cap104.971363333、origin和used不改，无新GPU/预留。主线N07→N08→N09/10，当前只是与等待无依赖的N10资源准备；方法、最终输入和原六维指标不变，P/T1后排，F/B关闭，无训练/OMR/人评。

## 原件

- [服务器实际哈希与限定检索](../reports/wc_paper_N10_existing_resource_hashes_scoped_20261016.json) · SHA256 `9e946faf1298ac487fb19c167fc16a80c26df67e756cf6b5963c1e44151dd8df`。
- [资源worker CPU控制](../reports/wc_paper_N10_resource_fetch_worker_CPU_controls_20261016.json)。
