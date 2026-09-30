# 跨进程后模型阶段复现诊断准备卡

2026-09-30；状态RUN_TERMINAL_DECODE_INTERVAL_LOCATED。进入依据：两次任务内部off/on全部通过、跨进程72模型输出与缓存相同，却出现93帧解码像素差异。当前不能确认差异发生在哪一阶段；本卡实现已完成，13项本机CPU/模拟监督检查通过；尚未启动GPU任务。

## 最小实验

官方WC、同AV工程输入/seed0、原36时间点/72CFG/WC70协议、同环境/权重/eager/offload/安全配置，两个全新进程顺序执行，每个生成一次。一次监督任务、原共享锁与GPU准入/冲突停止/记账保留，上限900秒/0.25GPUh（包括两个进程加载、失败及flush）从现有2.439848849GPUh余额扣除。不修改模型、缓存近似、VAE、过滤器、编解码参数或共享环境，以观测定位先行。

## 阶段见证

1. 保留72模型输出hash、CFG计数/trace、实际采样网格和最终缓存hash。
2. wrapper观察`model.generate_samples_from_batch`的最终sample返回值并hash，包含shape/dtype；支持list chunk，不额外调用模型。
3. wrapper观察`model.decode`的输入latent与raw视频输出；保存张量hash、shape/dtype、有限性，不保存bulk张量、不改变返回值。
4. wrapper观察`guardrail_presets.run_video_guardrail`的uint8输入与处理后输出，保存array哈希/shape，拒绝状态照原返回，不关闭或绕过检查。
5. 观察`save_img_or_video`实际输入tensor与编码参数；保存MP4文件hash、codec/container元信息并CPU完整解码RGBhash/时间戳。
6. 记录模型/tokenizer/source/环境哈希与cudnn/TF32/benchmark/deterministic当前设置；初轮不改变这些开关，不把潜在解决办法当作已验证原因。

正常阶段只进行detach/read-only/hash，保存原函数并恢复，不改变RNG/registered buffers/部署状态；若观察hook导致同进程差异、非有限或输出拒绝，记TECH_BLOCKED并保留失败。只终止自有进程组。两个新进程的首个不同阶段决定下一个确定性修复；不得从最终MP4不同直接假定编码器或VAE出错。

## 验收与证据边界

先做wrapper在正常返回/异常/拒绝/list-chunk/恢复下的针对性CPU检查与源码哈希部署，运行前重核实际预算、锁、GPU UUID/VRAM/compute apps。原进程已终态不代表将来准入。

不同阶段的hash严格比较；只定位到某一区间时写UNKNOWN/范围，不补造阶段内具体原因。修复需要新版本、两条对照共同使用并重新验证；重大采样协议改变再留给用户决策。源端/后处理稳定性问题解决前，不开展候选质量归因或将跨进程视频差异当作候选效果。当前数值负结果仍是工程样本上的机制结果，整个WorldCache方向保持探索状态。

## 实现与执行接口

`stage_witness.py`保留输出对象与原实例方法命名空间，支持list/None/异常/推理张量；记录哈希时核对RNG。`check_stage_witness.py`每进程只生成一次，完整93帧RGB解码；`supervise_f1.py --stage-witness`两个全新child、每次重新准入，共享900秒单调时钟截止与原预算。先核对源部署哈希与Linux CPU检查，再提交；实际运行回执另行归档。

## r1输出目录问题（已终态，不是复现通过）

源5ddd634：首进程生成一次成功、六阶段见证齐全、93帧完整解码。第二进程计划输出目录与首进程相同；在开始加载前0.149秒终止自有timeout进程组，监督器FAILED、费用正常结算。首进程312.661秒；总成本0.086891471GPUh，账本1.647042622/4。失败/首个见证/明确取消记录分别为reports/stage_r1_{supervisor,stage_a,cancel}.json，不能当成两进程通过。源80014d3修正独立目录；模拟child实际创建各自video目录的回归检查通过。准备新身份r2重新执行两进程，不改变模型或数值逻辑。

## r2终态

两个同源新进程均exit0，首个不同边界decode_output，latent/decode输入严格相同；根因UNKNOWN。合计634.230530秒，累计1.823217769/4h。详见17_DECODE_INTERVAL_RESULTS.md；下一步18_DECODER_POLICY_GATE.md尚未实现/运行。
