# W1 自身轨迹三场景诊断：直接批准与唯一执行

2026-10-06；当前为批准绑定和提交准备，尚未声称真实teacher观测或收益。

## 已批准的范围

用户直接回复“允许”，[来源绑定](../manifests/wc_w1_own_state_human_scope_source_20261006.json)关联当前turn `01a1110c-010f-75c3-816f-f4d5f71834d2` 与原独立范围问题。[批准原件](../manifests/wc_w1_own_state_gpu_authorization_20261006.json)只批准 `WC-W1-OWN-STATE-SHADOW-R1-20261006-A`：misc、AV51、AV28/seed0，原mask/scalar与calls45/46/67/68，三完整shadow ON视频、12同状态teacher观测；teacher只评分，不写部署。最大1800总/1770child/kill5，最大0.5GPUh计入原累计24h，旧费用不重置。

这是最近提报的[具体卡](../plans/WORLD_CACHE_OWN_STATE_DIAGNOSTIC_CARD_20261006.md)的范围答复；此前旧blocked解除，goal恢复active。W3-B9600完整卡没有因此自动批准，不重复其旧问题。CPU通过、全局预算余额和自动goal接续不再作为此卡批准的替代理由；本卡已获得直接批准。

## 冻结来源与必要准入

[通过生产CPU的R3](../research/140_WC_W1_OWN_STATE_PRODUCTION_CARD_AND_CPU.md)七步exit0/14.969秒、181payload/sourcef68bac4和720原件审计保留，核心13文件不改、不重跑。新[selected配置](../configs/wc_w1_own_state_approved_selected_20261006.json)仅增加UUID、直接批准及原CPU原件绑定；[新独立stage清单](../manifests/wc_w1_own_state_execution_20261006.json)共182文件，生产源与原CPU字节一致。

服务器原项目 `/home/gaokuangda/data/gkd/worldcache_omr`，新stage `.sync/wc-w1-own-state-gpu-r1-20261006`，唯一run `outputs/wc-w1-own-state-shadow-r1`。预备资源回读：原R3 receipt SHA匹配、181文件保持；根账本13.504302792/24h、48jobs无inflight；新run不存在。目标A6000 UUID `GPU-cebf7119-cf03-23b9-e192-cd196332b704` 初读24MiB/no compute process，数据盘557877370880空闲字节，另一GPU不用于本卡。这是预备状态，非最终GPU准入或实际运行。

下一selected-only CPU来源/原件/资产门，然后supervisor final fresh UUID/VRAM/compute process、f1共享锁、数据盘和整卡预算准入；排他submission marker、原supervisor/timeout/runner句柄和日志。未知transport结局只能查原stage/handle，不重提。1800秒统一预付，真实全wall按实费结算，失败、导入/加载、hash/teacher/解码/flush和释放均计费。

## 结果与验收边界

本卡必须通过每场景旧W1 OFF的全部72输出、cache/校准、trace、pipeline/decoder/video/93RGB身份桥，才能将对应同状态teacher观测解释为有效诊断并复用旧终点LPIPS。保留负值/零值/缺失；不要求三个场景全改善。CPU MockWriter和小网络不是实际视频、真实28层teacher或新质量结果。

实际GPU终态后先费用/三原句柄/f1锁/释放/源审计，再全93帧原件身份核对和三场景signed局部汇总。当前旧W1七场景4改善/3退化和平均LPIPS0.4388%保持；本轮真实视频、teacher、速度/质量结果尚未产生。后续结果将按原件补充本报告。
