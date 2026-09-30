# Next actions — 固定重放终态，先自动成像评价

1. [重放结果](24_W1_FIXED_REPLAY_RESULTS.md)：全部8轨迹技术通过，official14/scalar18检查全真、0fallback；候选7接受/robot VIDEO_REJECTED，官方8接受，失败保留原8分母。未得质量/干净效率收益，不重启原任务或加W2。
2. [终态审计](../reports/w1_replay_r1_audit.json)确认原全部PIDs退出/锁可用/GPU释放/source与9接受artifact hash匹配；[完整汇总](../reports/w1_replay_r1_summary.json)重新校验原reference/两门。累计3.599984882/4GPUh，余0.400015118h，无在途。
3. [自动成像卡](23_W1_IMAGING_EVALUATION.md)/[冻结协议](../manifests/w1_imaging_protocol.json)：完整原8分母/7可比对，MUSIQ全部93帧评价，600秒cap包含加载/失败/评价/flush，从原预算扣除。本地17CPU/真实Linux预处理对照通过、已有权重CPU load/forward通过；下一步推送/hash部署、LinuxCPU/预算/锁/GPU fresh准入，唯一outputs/w1-imaging-r1，启动前无GPU评分。
4. 成像终态核验所有PIDs/锁/GPU归属/source/checkpoint/输入视频/实际账本；完整覆盖才按场景等权汇总，拒绝保留，partial不声称完成。MUSIQ仅成像，较低帧间变化不判物理/语义，不能替代标准judge/整体质量/clean speed。
5. 原42条VQA问题已取回hash绑定；Qwen3-VL2B/8B缓存无权重，官方大judge/vllm等未就绪。保留资源缺口，后续提出自动语义/物理与clean配对预算方案，不为省事引入人评或把单维度当成功。
6. 代码/冻结输入/失败/结果/账本/总览/handoff同步私有GitHub；无重要问题自主推进，重大预算/训练/方向决策交用户。不新增budget/训练/付费服务。
