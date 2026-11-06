# N10自动质量：源码、资源与适用范围准备

更新：2026-10-16。**最终质量评价已有可复用的模型候选和明确的接线规则。** 本轮只读取官方源码、生成环境的包元数据和静态缓存文件；没有加载模型、运行评分或查询原N06/N05任务。

## 1. 先明确评价对象

LPIPS继续承担“保持匹配Native”的保真指标。N10复用最终共同测试视频，补充主体一致性、运动、文本一致性与成像质量，逐维报告，**不把少数维度加权成完整VBench总分，也不当作物理正确性真值**。

|维度候选|用途|当前资源与实现状态|
|---|---|---|
|subject_consistency|主体外观的一致性，和动态程度一起看|DINO checkpoint及hub源码有候选元数据，未验权重SHA/真实import|
|motion_smoothness|插帧重建相关的运动平滑|AMT-S候选文件存在，模型兼容仍待CPU验证|
|dynamic_degree|防止静止输出被单独奖励为“更平滑”|RAFT-things候选存在；活动程度不是越大整体质量越好|
|overall_consistency|视频—文本对齐|所查标准目录未见ViCLIP权重和tokenizer，需补资源核查；不推断机器其他位置不存在|
|MUSIQ_LONGER512|成像质量辅助维度|已有108610983字节MUSIQ候选，可复用原全93帧longer512规则，仍需最终源码/权重绑定|
|temporal_flickering|静态前提下的闪烁；移动场景仅描述性或不适用|不作为任意运动视频的统一“越高越好”质量结论|

原VBench的闪烁实现以相邻帧变化为基础，并明确要求静态视频；需按这个前提报告。[固定版本实现](https://raw.githubusercontent.com/Vchitect/VBench/fd18b3d055cb0fc6f066ca90fe2c3c8cbb698490/vbench/temporal_flickering.py)

## 2. 当前实际资源盘点

使用原生成Python `/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python`只查metadata：Torch2.7.1+cu128、torchvision0.22.1+cu128、VBench0.1.5、pyiqa0.1.10、decord0.6.0、av16.0.1。标准cache检查记录13个文件，**只是大小/mtime，不是权重哈希或可运行验收**。

可见DINO343242485字节、AMT-S12038359字节、RAFT-things21108000字节、MUSIQ108610983字节。CLIP模块文件可定位，且`.cache/clip`中有B/32与L/14候选；发行元数据`clip=null`不能被解读成模块不存在。CLIP也不能不加区分地替代ViCLIP并沿用相同指标名。

第一次查询使用了系统Python，其包元数据全部空；原快照保留，**不作为生成环境包缺失证据**。随后已改用原Cosmos环境重核。两次静态metadata及一次安装源码读取均不读模型权重、CUDA、GPU状态、账本、原任务句柄或stage，不改共享runtime。

原件：

- `reports/wc_paper_N10_static_resource_metadata_20261016.json`（系统解释器快照）
- `reports/wc_paper_N10_generation_env_static_metadata_r2_20261016.json`
- `reports/wc_paper_N10_installed_source_hashes_20261016.json`
- `reports/wc_paper_N10_source_and_resource_readiness_inventory_20261016.json`

## 3. 源码与输入绑定

官方repo固定到`fd18b3d055cb0fc6f066ca90fe2c3c8cbb698490`，只取9个源码/说明文件，未执行上游代码。已安装0.1.5的主体/闪烁/动态/总体一致性文件与所取pin一致，`__init__.py`、`utils.py`和motion_smoothness不同。**实际评分前必须选定一个完整源码版本并做CPU接线，不能混称同一实现。**

自定义输入必须把原生成prompt显式绑定到视频路径，不从`av_*`等实验文件名猜文本。官方支持显式prompt映射。[固定版本入口](https://raw.githubusercontent.com/Vchitect/VBench/fd18b3d055cb0fc6f066ca90fe2c3c8cbb698490/vbench/__init__.py)

所有源视频先通过93帧/FPS/几何和原SHA审计；指标内部采样另记。例如所查dynamic_degree在16fps输入使用间隔2，93帧对应47帧；overall_consistency使用8帧，不称“93帧语义评分”。[动态实现](https://raw.githubusercontent.com/Vchitect/VBench/fd18b3d055cb0fc6f066ca90fe2c3c8cbb698490/vbench/dynamic_degree.py) · [文本一致性实现](https://raw.githubusercontent.com/Vchitect/VBench/fd18b3d055cb0fc6f066ca90fe2c3c8cbb698490/vbench/overall_consistency.py)

不能依赖`local=True`自动保证无下载：所查初始化函数仍可能获取缺失资源。实际执行将显式绑定已核对的本地权重、源码与路径，在评分启动时禁止隐式下载，不修改生成环境依赖。[资源初始化](https://raw.githubusercontent.com/Vchitect/VBench/fd18b3d055cb0fc6f066ca90fe2c3c8cbb698490/vbench/utils.py)

## 4. 下一步与预算

初稿协议`manifests/wc_paper_N10_automatic_quality_protocol_draft_r1_20261016.json`已登记候选维度与输入/聚合规则。先确定实际源码、补ViCLIP资源核查及权重SHA，再完整CPU接线与费用估计；**当前未选择评分GPU卡，费用未知不填0**。

最终复用N07所有原注册位置，按视频标量→两seed的prompt均值→prompt等权；拒绝、失败与缺指标保留分母，不补样、零填或按好看的维度筛选。全部评分GPUh计入原v2池，评分时间与生成延迟分开，无需新增人评或付费VLM API。

原N06仍04:55一次验收；N05生产R2已在464接受，N06通过后优先启动完整66。原预算104.971363333、严格<12GPUh自主规则、N06/N05源码与运行保持。本轮没有新生成、质量结果或GPU提交。
