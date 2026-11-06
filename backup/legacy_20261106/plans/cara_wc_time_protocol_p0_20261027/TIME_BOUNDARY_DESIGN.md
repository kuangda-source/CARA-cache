# 双时钟增量设计

对应[WorldCache论文附录0.B](https://arxiv.org/html/2603.22286v1)：去噪循环到decode完成。只对新运行采集，不估计旧数据。

1. 新模块按固定SHA抽取真实 `generate_samples_from_batch`，在唯一 `for _,t in enumerate(timesteps_iter)` 前调用 `synchronize(); perf_counter()`。
2. loop后仅记host时间，不插CUDA同步；它不能单独作为精确GPU去噪耗时。
3. 真实model.decode返回后同步同一设备所有CUDA流，再记perf_counter；连续差值才是T_DD。解码前后的正常调度间隙都算入，不拼接分段时间。
4. scope限定单请求，finally恢复原实例方法；不改solver、状态、RNG、guardrail及原T_request/T_generate边界。多循环/重复decode/逆序时钟拒绝；无完整decode时T_DD=null。
5. 正式路径只加两次边界同步。A/B诊断可额外捕获轨迹、hash和张量，但这12条不进入干净延迟均值。实际同步必须绑定所选GPU UUID/device；不能默认同步错误卡。

每请求接受件需绑定prompt/seed、checkpoint/source/config/sigma SHA、初噪声与条件hash、36solver/72CFG、70horizon与reset、双支action/D计数、三个时间字段、load/warm状态、guardrail、编码前RGB和视频hash、dtype/backend/offload/resident、GPU UUID/driver/CUDA、热环境。原guard拒绝也必须写终态，T_request依旧实际测量。

当前完成的是可插拔计时适配与真实源小张量验证；尚未接成七角色完整生产监督器、writer/guardrail/全部失败路径组合接受链。这一缺口在派发前必须补齐，不能称已完成端到端生产准入。
