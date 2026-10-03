# 轻量完整生成路径：CPU 控制通过，真实部署测量待验证

2026-10-03。按 [84 的 CPU 方案](84_WC_VIDEO_GATE_AND_CLEAN_TIMING_NEXT.md)完成接口实现与验证；原 [83 六输出 GPU 卡](83_WC_FULL_OUTPUT_R1_CARD.md)和 [75 单次104点补验](75_WC_FULL104_R4_CARD_AND_RESULTS.md)均已终态，冻结源码、失败记录、输出和费用保持。本阶段没有新 GPU 提交或费用，也没有训练或新增人工评审。当前仍无法证明质量—时间前沿改善。

## 原完整轨迹的 CPU 复核

[分析程序](../scripts/analyze_wc_full_output_trace_cpu.py)读取原完整回执的无损 gzip，先验证解压 SHA 与已审计摘要绑定；[分析结果](../reports/wc_full_output_r1_trace_cpu_20261003.json)已再次从原件重算匹配。

| 已曝光 CAL | 首次 S / 输出 SHA 改变 | 首次命名模型输入改变 | 首次 full/cache 决策改变 | deep 次数：官方 / 候选 |
|---|---:|---:|---:|---:|
| common | CFG call23 | call25 | 无 | 35 / 35 |
| human_199 | CFG call23 | call25 | call46 | 38 / 35 |

两场景仅 call1..22 的模型输出 SHA 相同，条件和采样网格保持一致。人物场景有9次 full/cache 决策差异。两场景 call71/72 均实际执行 dense，但模型输入与输出 SHA 已不同：清空缓存来源不等于恢复已经偏离的 latent 轨迹。读取的全部参考来源中最大有效 solver age 为9；这不是仅 S 来源的寿命，更不是安全复用上限。

这些证据给出变化发生的顺序，不能量化误差大小，也不能把最终人物保真差异归因于某一次 S、某个层或后续调度。当前原件没有对应的同状态反事实误差范数，也没有各诊断组件独立耗时，不能从总 wall 倒推出哈希、恢复和来源检查分别占了多少。视频帧分段和去噪步骤不是同一个坐标。

## 轻量生产接口已实现

[light_sampling.py](../src/wcomr/light_sampling.py)从同一个原生 `Inference.generate` 执行每臂完整输入准备、采样、decode、guardrail、写文件。每次重新运行真实 `_get_data_batch_input`；没有借用第一臂 prepared input。每臂在计时外恢复共同初始 RNG、网络 buffers，并验证共用 eval 和参数不变；这些共同设置成本仍属于未来整卡 GPU 总费用。

生产接口移除了逐前向全张量诊断哈希、五处完整状态复制/恢复以及 shadow 导出。保留轻量调用计数/trace、普通输出形状与文件检查；最终文件 SHA 和 RNG 签名在 pipeline wall 外记录。沿用既有 `SimpleRefreshAdapter`，保留实际条件内容签名、请求/模型/CFG/group/epoch 绑定、真实 D 与近似来源隔离、native window 对应关系、nonfinite 拒绝、dense 回退和核入口检查；必要账本与核成本仍在候选 wall 内。

主口径是完整 `Inference.generate` 前后同步 CUDA 的 `pipeline_wall_seconds`，包括每臂真实 prepare、完整36 solver/72 CFG、decode、guardrail 和写文件。prepare/sample/decode/guardrail/write 分段只记录**未独立同步的 host wall**，不能称为各阶段 CUDA 延迟，不能假定相加就是总 GPU 时间。来源验证或核本身可能同步；“只有边界同步”仅描述计时包装器。

接口要求两标签计数相等、有序序列，支持正向、反向和 ABBA；拒绝不平衡/集合顺序与已填充 phase 身份。计数检查包括原生70-call horizon、call70失效和最后两次 dense 暖启动，输出要求完整93帧。异常保留原计划分母、已完成第一臂、异常类型与当前 phase；挂钩、forward、buffers 和 decoder flags 必须清理。

## 实际 CPU 验证与失败记录

复用 [固定官方函数夹具](../tests/check_full_sampling.py)，新增可选外部 callback；默认历史控制行为保持。测试的全张量哈希、五处状态观察和最终 latent/decode witness 均由 [独立测试](../tests/check_light_sampling.py)外挂，生产计时核心不包含它们。这些观察会增加 CPU 测试耗时，因此下表不是速度结果。

| 回执 | 终态 | CPU wall | 覆盖 |
|---|---|---:|---|
| [r1](../reports/wc_light_sampling_cpu_r1_20261003.json) | PASS | 118.323秒 | 原有11控制 + 初版轻量9控制 |
| [r2](../reports/wc_light_sampling_cpu_r2_20261003.json) | FAILED | 47.655秒 | 新文本 guardrail 控制暴露测试异常捕获类型不匹配 |
| [r3](../reports/wc_light_sampling_cpu_r3_20261003.json) | PASS | 48.989秒 | 当前轻量15控制 |

r2 中官方 text guardrail 拒绝抛出通用 `Exception`，测试仅捕获 `ValueError`，使验证退出1。生产接口已有 `BaseException` 记录/清理路径；修复的是测试捕获，并加入官方 keep_going 两种模式。不把 r2 中未返回的中间控制追认为 PASS，不把该夹具失败作为方法负结果。新增次序测试时曾出现的本地缩进错误在 r2 部署前修正，没有 GPU 执行。

r3 的15项包含：flow OFF/ON 的 D/D 与 S 接线、不足历史回退、反向 D/D、ABBA 四生成、decode/write 失败、核 nonfinite、条件变化、文本拒绝与 keep_going 缺输出，以及两种 flow 的不平衡/无序序列拒绝。D/D、反向、ABBA、不足历史回退均通过原九项一致性；ABBA 实际调用 prepare 四次。S 的 toy 核确实改变最终轨迹、被后续 cache 读取，同时未进入 true-D history；候选 D/S 不要求输出哈希相同。失败控制保留第一臂、两输出分母并完成清理。

[本地独立源码与原件审计](../reports/wc_light_sampling_cpu_audit_20261003.json)确认当前21份 payload SHA 全匹配 r3，r1 的19份依赖/默认夹具源未变，固定官方五文件 SHA 相同，故11项旧回归仍对应当前默认实现；r1 不追认后来变化的轻量核心或轻量测试。审计还复算完整轨迹分析并通过 AST 检查。

三轮实际使用服务器已有 Torch2.7.1+cu128 环境，禁止 CUDA 初始化；原生 sampler/WC/UniPC/Inference 函数体固定，但网络、prepare、noise/conditioner、VAE 边界和 writer 是明确 toy。CPU S stand-in 不是 Sparge 核，93×16×16 mock 输出不是视频。这里证明接口、拒绝与清理控制，尚无真实 GPU D/D 字节等价、真实核、视频或性能接受证据。

## 当前预算与下一步骤

现场1791039297.6093833确认原六输出任务三 PID 消失、六 mp4 保留、compute apps 为空；账本与 r3 相同：累计 **6.733473505896205/12 GPUh、37 jobs**，余 **5.266526494103795 GPUh**，无新预付。本阶段 GPU 0h。原104点授权已使用一次，耗时1153.547615806秒，不能重新提交它来测新路径。

下一先将轻量接口接入独立真实部署入口，绑定模型/样本/核版本和 source、核查实际 prepare/mode/buffers/import/assets；明确输出分母、计时观察工作量、交替顺序、首次/热运行与完整成本。当前没有下一张 GPU 卡、runner 提交或新 reservation。正式选卡后仍要通过实际 CPU、source/assets/import/package 和 fresh UUID/VRAM/compute/全局锁/余额准入，并先做真实 D/D 完整输出控制。

保真风险保持：human_199 相对官方 WC 的 luma SSIM0.705、PSNR17.48dB；两开发 CAL 不构成 CONF。后续测量沿用0.1/0.98和6/23/27回退，允许各自官方 adaptive schedule；若要隔离反馈需另列解释性控制，不能在线提供官方未来轨迹。净部署收益、同版本原生完整/少步与调过 WC 的强基线、独立确认仍缺失。优先解决这些缺口，再决定缩小稀疏范围或推进 W3/RV；不先加学习器或训练。
