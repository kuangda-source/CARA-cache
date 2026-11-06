# W1 clean配对成本程序准备：完整原8×2×3，CPU通过，未提交GPU

2026-10-01；预算提议沿用[下一窗口方案](31_W1_NEXT_WINDOW_COST_AND_DECISION.md)。原4h账本未修改：已用3.6512467238638138h/余1255.511794秒，无在途；新增4GPUh/总cap8h尚待用户决定。CPU准备不视为预算批准或实机通过。

## 已实现与冻结

[协议](../manifests/w1_clean_timing_protocol.json)绑定旧固定replay、CAL8 reference和candidate原始receipt哈希，沿用同一seed0/采样时间网格、72CFG调用/70counter horizon、模型、offload、严格past-anchor参数与局部decode策略。50尝试顺序已冻结：首个原场景各臂1次预热，共2次单列计费且排除计时汇总；原8每臂3次，共48计时尝试。每轮4scene官方先/4scalar先，下一轮翻转，每轮场景顺序旋转3位；无按旧质量选择或替换场景。拒绝/技术失败保留，完整summary拒绝partial/reorder/少重复/少scene。

[scripts/run_w1_clean_timing.py](../scripts/run_w1_clean_timing.py)：一次resident model，真实inference.generate前后CUDA同步，end-to-end包含text guardrail、encode、denoise、相同decode policy、video guardrail与保存。计时内仅共用block计数、冻结controller/候选自身校准和局部decode flags；不注册逐call tensor hash、StageWitness.record、tokenizer identity hashing、shadow、profiler或tensor dump。候选算法自身finite/reduction/past-anchor开销保留计时，不能删掉当优化。

采样网格/trace/anchor/flags检查、accepted全93帧decode/时间戳/shape/finite/RGB与文件SHA、原始receipt保存都在generation计时之外，但仍计入supervisor GPU总wall。前两次预热必须在计时结束后比较全部93个decoded RGB hashes与各自旧官方/候选首场景，检查移除diagnostic observer没有改变输出；不一致立即TECH_BLOCKED，不继续48次或称已重现实机。这个真实GPU门仍未执行，CPU不代替它。

[src/wcomr/clean_timing.py](../src/wcomr/clean_timing.py)与[summarizer](../scripts/summarize_w1_clean_timing.py)只产出scene内3个原timing/中位数、逐repeat outcome/仅双方接受的时间比、所有原8拒绝计数；不插补拒绝、不给CI或quality/method接受结论。重复seed0 CAL不是48个独立质量样本、DEV/CONF或调优WC/原生少步F2曲线。

supervise_f1 --w1-clean-timing为单14400秒窗口/timeout14390秒、原global lock和GPU conflict/UUID准入/整墙钟失败计账；旧4h ledger或剩余额度不足完整14400秒时在输出/子任务/账本改动前拒绝，不自动扩额度。真实runner再次检查总cap至少8h且余额至少14400秒后才import torch/生成；独立validate-only只检查50attempt scope/旧raw依赖/source/input，CPU允许。

## CPU与当前远端状态

[本地48项](../reports/w1_clean_timing_local_cpu_20261001.json)、[Linux48项](../reports/w1_clean_timing_linux_cpu_20261001.json)同范围检查，不能相加为96：完整8scene/顺序平衡/预热排除、stopwatch两端同步/审计和保存排除、异常耗时保留、拒绝不插补、partial/nan/未来anchor/配置漂移/暖场RGB变化拒绝，以及真实fake-GPU单14400秒互斥预算监督/原4h拒绝/余额不足拒绝。复用原upstream CPU toy forward的replay/decoder政策测试，无模型/GPU。

Linux最终独立staging w1-clean-timing-cpu-r2-20261001：48pass/torch CUDA未初始化。实际新runner在真实Cosmos runtime目录--validate-only检查固定源码/采样网格/layout/旧raw/配置和全部50计划通过；实际新runner对复制的未批准4h账本拒绝，未import模型或forward。主项目账本前后SHA完全一致、旧实机source72c9e24各文件保持，原controls3PIDs不在、global锁可用、GPU1 24MiB/noapps；新代码只在CPUstaging，未覆盖运行目录。

## 接续点

程序已实现/CPU准备完毕；唯一新GPU窗口仍是提议。若用户选择新增最多4GPUh成本门，再记录该直接授权/版本化预算，commit/push/hash部署与最终CPU/旧终态/fresh GPU准入后唯一新outputs/w1-clean-timing-r1；14400秒包括加载/预热/诊断审计/失败/flush，超时partial不补凑。若用户选择先CPU替代资源核对，沿既有F2/L0/OMR兼容性计划，不引入训练/付费/人评或自动切主线。

原CAL8机制only/MUSIQ3升4降/VQA6平1misc降/robot拒绝/controls部分内容响应仍是当前科学证据。这里没有新生成、clean耗时或质量—时间收益。
