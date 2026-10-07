# W3-B R2：固定执行尾段的核心与生产准备（2026-10-07）

继续 WorldCache。新R2保留原四对、两个场景和完整配额/对照，区分“实际执行动作”与“未执行的原生建议”；原R1配置失败完整保留，见[145](145_WC_W3_PLACEMENT_R1_FAILURE_AND_TAIL_ALIGNMENT.md)。本报告是技术准备与CPU证据，真实R2收益尚未测量。

## 受影响核心的实际CPU证据

独立服务器stage `.sync/wc-w3-placement-tail-core-cpu-r1-20261007`，source `92aad082649c14962f881fd2b39d92866e954110`，CPU supervisor3035292、child3035293，运行258.317280秒，exit1。失败发生在全部控制序列返回后：复制旧测试时保留了汇总“7案例”，新增建议差异案例后实际是8。这是汇总断言错误，原始回执/日志/8组轨迹和费用性质保留，不将exit1改写为正常退出。

只修正未来测试的7→8计数，四份实际核心源码不改。基于冻结原件作独立纯CPU审计0.307658秒，未重复模型fixture执行。3组成功场景（flow off、flow on、flow on+故意建议不同）合计6父/48后缀/30 mock输出；12次第70原生建议与计划不同，实际动作仍等于冻结父掩码；原R1决定谓词会拒绝这些差异。5类writer、guardrail、前缀、缓存历史、计划改动故障仍拒绝并恢复父状态，后两类保存了恢复前pending事件。独立60次原始记录破坏拒绝通过。

140份旧stage源、149份本次源和9份上游原生源码SHA核验一致；服务器账本与原R1 GPU回执前后不变，两个CPU句柄已退出。CPU使用固定原生方法体与Toy网络/条件/输出，30个mock不是真实视频，不证明真实四对的缓存合法性、终点质量或GPU速度。原失败日志和轨迹并未因修正计数被覆盖。

- [原CPU回执](../reports/wc_w3_placement_tail_core_cpu_r1_supervisor_native_20261007.json)
- [8组原始CPU轨迹](../reports/wc_w3_placement_tail_core_cpu_r1_attempts_native_20261007.json.gz)
- [原失败日志](../reports/wc_w3_placement_tail_core_cpu_r1_log_native_20261007.txt)
- [原件回传绑定](../reports/wc_w3_placement_tail_core_cpu_r1_native_capture_20261007.json)
- [独立原始轨迹审计](../reports/wc_w3_placement_tail_core_cpu_r1_raw_audit_20261007.json)及[代码](../scripts/audit_wc_w3_placement_tail_core_raw_cpu.py)

## 完整新卡与成本

候选 `WC-W3-PLACEMENT-TAIL-ALIGNED-R2-20261007-A`，新run `wc-w3-placement-tail-aligned-r2`。完整2父/16后缀/10视频/4交换、六全93帧损失不变；Common18/17、Human20/18每CFG配额与47/49、48/50、61/63、46/48原位置不变。第69/70执行冻结动作并记录建议差异，原缓存合法性/年龄/有限性、初始化/70末reset和71/72完整保护保留，无配额修补或新点替换。

独立生产入口、监督、终态、评分代码已准备；保留139份未受影响源，新增闭包共168份文件。旧原生视频读取、LPIPS资源和signed评分代码/通过证据复用，不重跑无关组件。预算与新授权合同本地CPU通过，服务器实际生产CPU待验；配置仍GPU未选、authority空，新例外未批准，新GPU未提交。

完整成本沿用真实两父C/D估算，并将新增完整后缀代理更新为R1观测较大的349.396313秒；不把失败早停费用当完整卡成本，不通过缩小对照压到2h内。名义 **7765.129250秒=2.156980347GPUh**，规划 **9348.155099秒=2.596709750GPUh**，均是诊断代理而非硬期限或部署速度。累计仍14.356340357/24h，剩余9.643659643h；整卡规划与清理余量可容纳。

原R1的>2h一次授权已消耗。完成受影响实际生产CPU、源/配置闭包与资源快照后，仅就完整新R2提出一次>2h例外；在答复前不提交GPU。旧逐卡秒数截止取消，累计24h、资源隔离与实费结算保持，不扩训练、稀疏搜索或人工评审。

- [R2事前设计](../plans/WORLD_CACHE_PLACEMENT_TAIL_ALIGNMENT_20261007.md)
- [新配置草稿](../configs/wc_w3_placement_tail_v2_production_r1_draft_20261007.json)
- [完整费用估价](../reports/wc_w3_placement_tail_v2_complete_cost_20261007.json)
- [实际生产CPU闭包](../manifests/wc_w3_placement_tail_v2_production_cpu_r1_20261007.json)
