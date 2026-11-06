# W1固定重放后：自动成像质量维度评价

2026-10-01；FROZEN_INPUTS_LOCAL_CPU_PASS_PENDING_DEPLOYMENT。重放已终态/审计，原8候选7接受、robot VIDEO_REJECTED保留；无GPU评价运行。已绑定完整输入回执/哈希，待独立部署与LinuxCPU/准入。

当前科学缺口：CAL8同状态scalar误差改善不能说明闭环视频质量；重放首AV较低帧间变化也不能区分更稳定和动作消失。下一步优先用已有官方评价资源取得真实视频成像质量维度，而不是要求人工评审或先加W2。此维度不能验证动作完成、语义遵循或物理正确性，不能单独给方法PASS/FAIL。

## 已核验资源

[只读资源审计](../reports/w1_quality_resource_audit_20261001.json)显示生成环境有pyiqa0.1.10、decord、torch2.7.1+cu128/torchvision0.22.1，缺vllm/openai/detectron2；默认VBench缓存有MUSIQ、AMT和部分aesthetic权重，CLIP/ViCLIP/DINO的指定默认路径不完整。额外torch hub有DINO，但未验证路径重用；包存在不是完整runtime验收。只核验指定路径，没有断言整台机器不存在其他资源。

[Qwen3-VL小模型库存](../reports/w1_small_judge_cache_inventory_20261001.json)中2B/8B快照仅processor/tokenizer/config，无safetensors权重。因此不能把缓存目录视为可运行judge。Qwen3Guard安全组件与Cosmos Reason1不自动充当标准benchmark judge。当前不调用付费API，也没有大judge评分。

[MUSIQ CPU预检](../reports/w1_musiq_cpu_preflight_20261001.json)：本地108610983字节checkpoint SHA256 `358bb6af275e28ea56821d44fb55c6cb83645db11f394d3ad65b2d149965ab50`，与官方代码下载文件名中的8位digest前缀匹配；完整外部release digest未独立验证。pyiqa MUSIQ源码hash绑定；离线CPU模型加载+常量图forward有限，CUDA未初始化。是实现兼容性检查，没有视频质量分数。

[原8场景VQA输入完整性](../reports/w1_cal8_vqa_input_integrity_20261001.json)固定公共dataset revision c36b7beb69bd7c4adcedc1431407fce98f9dfe44，原问题共42条（4/1/4/3/9/14/3/4），原样下载至ignored `.sync/quality_inputs/vqa/`，记录SHA256/Git blob SHA1；未评分，不把问题当独立视频样本。与本批MUSIQ无关，供后续标准语义/物理评价准备。

## 评价协议

- 原8完整WC/scalar pair，seed0，93帧432×768；不筛除misc或按已有视频差异选子集。官方参考用CAL8 OFF，候选用scalar OFF；首scalar ON只是parity门。
- 首先重校验完整重放receipt、reference hash、official/candidate parity和8固定schedule；hash绑定每个已接受视频。TEXT/VIDEO_REJECTED保留原8分母，无视频就不伪造分数。
- 使用已有MUSIQ SPAQ checkpoint/pyiqa0.1.10，同一个eval模型，逐帧microbatch1，全部93RGB；如长边>512则保持比例取整缩放，bilinear/align_cornersFalse/antialiasFalse，像素除255，与固定官方`imaging_quality.py`的longer默认相同。原始帧分数均值/100；比较同场景候选减WC，然后场景等权，不把帧独立化。
- 记录score、PTS、frame count、视频/source/model哈希、包版本、显存和完整wall。任何非有限/帧数/PTS/输入hash/技术错停止，不补分或重跑凑全。
- 新单batch最多600秒，从原4GPUh实际余额扣除，GPU成本尚未测量，不能保证600秒完成。提交必须等旧任务全部退出/锁释放、账本结算、输入manifest冻结、source部署/LinuxCPU、新GPU准入；所有加载/失败/评价/flush计费。硬cap下部分结果显式INCOMPLETE，不叫整体质量。

代码：`src/wcomr/imaging_quality.py`、`scripts/run_w1_imaging.py`、`supervise_f1.py --w1-imaging`。本地17项针对性测试通过（imaging2/supervisor12/replay_results3），py_compile通过。Linux和CUDA/视频评分未做。MUSIQ score变化只改变成像维度证据；下阶段仍需动态/语义/物理、干净重复计时和未调参确认，不能拿漂亮单维度代替质量—时间曲线。

预处理额外在真实Linux CPU按四种RGB几何与官方torchvision Resize对照，全部bitwise相同；[回执](../reports/w1_imaging_preprocess_cpu_20261001.json)。新[冻结manifest](../manifests/w1_imaging_protocol.json)绑定终态两臂输入/权重/source，原8分母不变，实际最多7接受视频对。显式model.eval/inference_mode与本地pyiqa源码hash记录；没有声称完整官方环境复现。
