> 最新接续：r3因连接IncompleteRead退出1/三PIDs退出/CPU锁释放，2890MiB保留；新r4/source39993d1已live，partial3280MiB/未完整，同cache/官方hash/cap3600CPU-only，见[观察](../reports/w1_judge_assets_r4_live_observation.json)。VQA runner/900s supervisor/原raw汇总已实现，本地25与Linux25/全部15真实输入CPU通过，未load/forward/GPU评分。见[runner卡](27_W1_VQA_RUNNER_PREPARATION.md)；下文为原始输入准备阶段与历史r3启动记录，不据旧live判断当前。

# W1自动开发VQA：资源恢复与输入协议

2026-10-01；INPUTS_PARSER_CPU_PREPARED_PENDING_COMPLETE_MODEL_ASSETS_AND_GPU_RUNNER。语义/物理小模型评价尚未运行，不等于论文235B或最终Joint/独立确认。

当前路线继续WorldCache质量证据补全，暂不加W2。固定scalar重放8轨迹技术通过/7接受1robot拒绝，MUSIQ3升4降/mean delta+0.004254295，没有闭环整体质量或clean speed正结果。GPU累计3.612360697322422/4h、余0.387639302677578h，无GPU在途。

## 资源恢复记录

- CPU r1/sourced0faa4b：服务器直接Hub元数据请求失败，exit1，261.483689秒；父/子/downloader全退出、source hash一致、GPU账本不变。没有权重下载。[审计](../reports/w1_judge_assets_r1_audit.json)。
- CPU r2/sourceb5a6a49：使用任务专用SSH loopback转发本机已有代理；固定版本元数据HTTP200，真实权重文件有进度。最终1190.036513秒后timeout exit124，全部PIDs退出/CPU lock释放，保留786432000字节（750MiB）。downloader文件仍RUNNING是被timeout后的旧状态，不能当进程在跑。[审计](../reports/w1_judge_assets_r2_audit.json)/[supervisor](../reports/w1_judge_assets_r2_supervisor.json)。未主动取消该任务。专用代理在其终态后请求停止，不影响共享FRPC或系统代理。
- 匿名公共镜像元数据0.347秒返回同一revision；8MiB range probe为HTTP206/总大小4255140312，5.489秒完成，SHA256 prefix与既有部分文件完全一致。只是运输路径对照，不是完整模型验证。[metadata](../reports/w1_judge_alternate_route_probe_20261001.json)/[range](../reports/w1_judge_mirror_range_probe_20261001.json)。
- 下一r3使用[CPU resume manifest](../manifests/w1_development_judge_assets_resume.json)，相同10文件/revision/官方Git/LFS哈希与项目cache；匿名镜像，只因测得吞吐不足将CPU-only cap由1200改为3600秒，原4GPUh额度不变。下载器不使用认证token，不把认证请求交给镜像。不修改旧协议/旧运行。当前r3已唯一启动/source202e21d，Linux4CPU/source hash通过，supervisor2481616/timeout2481618/downloader2481619 live，partial850MiB未完整；[启动](../reports/w1_judge_assets_r3_launch_20261001.json)/[观察](../reports/w1_judge_assets_r3_live_observation.json)。继续同handles不改在跑CPU文件/重复提交；最终须用[官方完整性manifest](../manifests/w1_development_judge_integrity.json)逐文件验证，prefix匹配不能代替完整digest。

## 原8场景/原题/相同输入

[开发VQA协议](../manifests/w1_development_vqa_protocol.json)绑定完整WC/candidate回执、原8顺序、42原VQA题文件hash和模型revision。WC42题，接受候选39题，robot3题保留拒绝且不伪造答案。32YES/10NO；固定全YES基线32/42仅作judge偏置诊断，不当视频质量或提示输入。各scene的题相关，按scene等权，不把问题或帧当独立样本。

提示严格与固定PAI `evaluation_prompt.py` 的原single-question模板相同；每次只问一道原题，不拼题、改题、把ground-truth答案/UID/方法名放入模型prompt。方法标签只在回执，参考/候选先后由scene SHA256奇偶固定。

保持官方requested fps2/max_pixels768×28²。真实Linux CPU预检确认qwen-vl-utils实际在本规格取10帧（floor到偶数），索引0/10/20/31/41/51/61/72/82/92，原93帧/16fps，视频tensor10×3×448×768，patch16；显式传递fps/indices/source frame metadata并禁止processor二次采帧。采样而非全视频像素输入，不能宣称全动态物理检验。[CPU输入回执](../reports/w1_vqa_processor_cpu_20261001.json)只加载AutoConfig/Processor与处理一段真实WC视频，未加载模型权重/未forward/未评分，CUDA未初始化。

## 解析与汇总

`src/wcomr/development_vqa.py` 严格识别整段YES/NO（允许末尾标点），解释文本/YES与NO同时出现/空答均标INVALID_OUTPUT，保留raw，不通过substring猜答案或重问凑分。不把invalid悄悄当NO/错误或删题；每scene保留原题完整覆盖，point accuracy只有全部有效时给出，否则给correct/n到(correct+invalid)/n确定性上下界。这是未知答案边界，不是统计置信区间。拒绝候选仍保留原8场景分母，没有可比score不填0/不插补。

本地7项CPU检查通过（两个CPU transport/cap variants、integrity、prompt/parse/unknown/denominator），[回执](../reports/w1_vqa_local_cpu_20261001.json)。`development_vqa_input.py` API真实CPU兼容检查通过。Linux parser checks与GPU runner/完整load/评分尚未做。

下一拟单GPU batch900秒，从原余额中划拨，一次model load/all原8/single原题，greedy/BF16/SDPA/max_new_tokens1024/seed0，包含hash/load/失败/评分/flush。未实测成本，不保证900秒完整结束。必须先权重完整性、离线兼容、runner/source/LinuxCPU、新预算/锁/GPU admission全部核验；不能仅因partialCPU或processor通过提交。未知技术错立即停止，parse invalid保留继续完整原题。完整小judge结果也只作开发代理，仍缺标准judge/干净重复计时与未调参确认，不加W2或叫方法通过。
