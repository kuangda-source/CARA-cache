# Next actions — 输入对照终态，下一预算/范围决定

1. controls-r1/source72c9e24原8/126全有效，repeat0/42变、blank14/42、cyclic14/42；全PIDs退出/锁/GPU释放/模型输入raw/hash/本地重算通过。[结果](30_W1_VQA_INPUT_CONTROLS_RESULTS.md)/[审计](../reports/w1_vqa_controls_r1_audit.json)。只证重复稳定/内容响应，不证明物理准确，不再重复控制或调prompt。
2. 实际累计3.6512467238638138/4GPUh，余1255.511794秒，无在途；不扩额或提交新生成。原VQA6平1misc降、MUSIQ3升4降/robot拒绝/CAL8机制信号保持，无质量—时间收益。
3. [成本与重要决策卡](31_W1_NEXT_WINDOW_COST_AND_DECISION.md)：原8两臂旧诊断3141.247秒，并非clean下界；现余额不足以稳妥完整计时。提议新4GPUh原8×两臂×3repeat clean成本门，或先CPU准备替代资源，待用户选择；不以好子集代替原8/冒充F2或DEV。
4. [计时程序准备](32_W1_CLEAN_TIMING_CPU_PREPARATION.md)已完成：原8/50协议runner实现/本地Linux48 CPU与真实validate-only/旧4h拒绝通过，新代码仅staging、主ledger与runtime未变。若批准新窗口，再记录授权/版本化额度、source同步/hash部署/最终CPU/fresh预算锁和GPU准入后唯一新身份。48计时尝试/2预热/失败/flush都计费，partial不完整结论。未批准则只读/CPU资源工作，不据弱proxy切OMR/W2。
5. 若成本门通过也需更强质量证据/新明确机制，不能仅速度/当前CAL稳定认方法接受；后续调优WC/原生少步曲线、DEV/CONF仍需设计与独立资源。无非必要人评/付费/训练，meaningful代码/回执/docs同步GitHub。

6. [L0部分资源验收](33_L0_WAN_LONGLIVE_OMR_RESOURCE_AUDIT.md)：Wan5B11文件完整hash/两套LoRA header结构与16CPU通过，非完整adapter或真实融合/GPU。下一可独立CPU下载锁定2适配器1.802GiB/逐SHA、真实融合新输出和隔离环境/任务接口验收；OMR公开入口仍BLOCKED。保持主线，不自动转L1/训练/扩额。

7. L0 CPU获取r1因连接中断exit1/1218.181533秒终态，原3PIDs退出/CPU锁释放/账本不变；仅关闭本任务owned临时转发。CFG4文件完整官方hash、真实600tensor finite/300pair alpha-r通过，独立核验PIDs2495417/2495418退出；few-step保留167772160字节（160MiB），非完整payload。两配方分片CPU融合程序已实现，本地/Linux22同范围检查通过，尚未真实Wan5B融合/模型任务load/GPU。下一同固定release/cache/3600秒的新r2续传，不重启旧identity或改共享路线。

8. [真实CFG验收/完整融合准备](34_L0_CPU_FUSION_PREPARATION_AND_CFG_PAYLOAD.md)：two-recipe runner/协议/本地Linux22已齐，full5B fusion尚未执行。r2完整release后先逐全SHA/finite，再新CPU identity/bounded3600/hash-deploy/32GiB+80GiB准入，全825×2融合及原条件权重/序列化检查；后续隔离任务环境/接口。无新GPU或重要预算答案。

9. L0 CPU r2/source965a502已实际启动且3PIDs2496080/2496081/2496082均/proc核实live，独立CPU锁持有、3600秒上限、source/协议hash一致、CUDA空/账本不变。复用CFG全部已验收4文件，few-step由160MiB续到188743680字节（180MiB），仍非完整/hash验收/融合。r1原连接失败及160MiB保留不改。 继续同r2 handles/owned转发至终态；前述r2准备项已实际启动，以最新launch/live为准。

10. L0 r2因第二次HTTP流中断exit1/583.253381秒终态；3PIDs2496080/2496081/2496082已退出/CPU锁释放、原source/协议核验和GPU账本不变，owned r2转发在完整审计后关闭。few-step保留555745280字节（530MiB），CFG4文件继续官方hash PASS。新16MiB range/retry/rollback/fullSHA获取程序和完整融合监督已实现，本地/Linux39同范围CPU通过；还未r3提交/完整5B融合。 [range恢复与接口门](35_L0_RANGE_RECOVERY_AND_INTERFACE_GATE.md)：下一r3小段续传，完整/finite后真实有界全模型融合，再共同native管线任务/noise/条件与单分支验收；不将CPU scheduler或spy计数当GPU。r2旧live已被终态覆盖。

11. L0 CPU range-r3/sourcebd8253d已唯一实际启动，3PIDs2498231/2498232/2498233都/proc verified live，CPU获取锁持有、CUDA空/source协议hash一致/账本未变。官方精确206/64KiB旧prefix边界preflight通过；已完成2个16MiB chunk、重试0次，已fsync字节589299712（562MiB），另有在途文件长度602931200（575MiB）。未完整1289824400/整SHA验收或两模型融合。复用原530MiB，不改r2失败或扩大GPU预算。 当前r3已启动，前述准备项是历史步骤；继续同handles和owned forward，不再跑旧r2观察/settle。
