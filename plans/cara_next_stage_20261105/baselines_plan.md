# Same-budget external baselines — plan only

目标：与冻结R18C在相同Cosmos/CAL35协议、seed0、93帧下接近T_DD≈130s；最终在confirm10的同10输入上用同seed Native36计算配对Alex及实测T_DD。Native仅在确认卡确实完成、原件hash绑定且协议相同后复用，不重跑参考。当前仅工程计划/量级估算，**不是正式报价，无GPU授权、预留或启动**。

仓库检查：在 `src/` 和 `reports/` 全文搜索LeMiCa/TeaCache/MagCache没有命中可复用实现/已验结果。WC和RA已有 `src/wcomr/clean_speed20_r1.py`、`paper_baseline_grid_r1.py`、`cfg_ra_joint_{control,execution}.py` 及 `wc_time_protocol_p0.py` 的执行/时钟路径。RA复用的是仓库SOURCE_RA，后续应核对所要对照的论文版本，不能仅凭名字声称等同第三方官方实现。

|baseline|复用与既有证据|预计工程工作（人日）|同10输入GPUh量级（非正式报价）|
|---|---|---:|---:|
|WorldCache|现成WC/compile_wc_adapter、CAL35 WC_T006；保留官方0.06为原样锚，若需130s另登记独立时间校准配置|0.5–1：新卡接线、旧输入时间校准及CPU一致性|1.2–1.6|
|RA|现成SOURCE_RA/JointCDController和RA_T1；需核对算法身份，接入统一T_DD|1–2：精度/CFG语义核对及时间匹配|1.2–1.7|
|LeMiCa|无本地已验实现；需选定官方revision、Cosmos端口、重置/CFG/全compute-off控制|3–5：端口及CPU功能验证|1.4–2.0|
|TeaCache|无本地已验实现；需固定官方revision和Cosmos残差/时刻接口，再做同请求时钟|2–4：端口及CPU功能验证|1.4–2.0|
|MagCache|无本地已验实现；需固定官方revision，明确是否需要额外校准及其成本|3–5：端口、校准协议及CPU验证|1.4–2.0；若另需校准数据须另列|

量级依据：130s T_DD对应CAL35完整请求约192.6s；10正式+2warm约1.04GPUh（×1.1+1200s）。另计旧暴露输入上至多6个时间pilot，18请求同假设约1.39GPUh；适配未实测者保留更宽工程范围，不能把此数字当已批准整卡上限。上述人日是开发估计，不计GPUh；实际端口/校准开销必须在未来正式卡中全额核价。

时间校准只用旧暴露O1/N1（不使用这10个未暴露prompt的LPIPS调参），预先限定2输入×3个时间设置，按T_DD距130s选一次，冻结后在十输入上完整评价。若不存在匹配点，原样报UNMATCHED，不把相同刷新次数代替相同时延。保持原官方配置为可追溯锚；对时间匹配变体清楚标注配置及校准成本。

证据：[A32冻结](../cara_next_stage_20261028/mainline/r2/A32_FROZEN_BASELINES.json) 的WC_T006/RA_T1针对旧Native/1.5目标均为UNMATCHED，不能迁移成130s匹配；[CAL35结果](../../reports/cara_f19_speed190_complete_r1_20261103/complete_analysis.json) 已含WC；[旧N05量级](../../reports/wc_paper_N05_core66_observed_tradeoff_20261016_1205.json) 只作历史工程背景。各baseline最终需独立冻结算法身份、范围、正式报价、Linux CPU证明及用户go-ahead；本计划不派发。
