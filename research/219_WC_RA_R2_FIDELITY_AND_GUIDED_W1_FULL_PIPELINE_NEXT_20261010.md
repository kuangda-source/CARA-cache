# RA R2 完整保真结果与 guided-W1 完整采样接续（2026-10-10）

两个真实视频场景中，RA 阈值从 0.141488470197544 改为 0.070744235098772 后，平均 LPIPS 从 0.3577226890671638 降为 0.31962599677424275，改善约 **10.65%**；完整分支调用各从24增至28。它仍比同批官方 WorldCache 的平均0.2894042802433814高约 **10.44%**。这说明联合控制的质量—计算工作点可以调整，当前两版仍未在这些场景保持官方缓存的保真水平。共同刷新对照的数值与完整输出在两轮重复出现，为后续 guided-W1 与联合控制组合提供具体参考。

| 场景 | WC LPIPS | 共同刷新 LPIPS | RA R1 LPIPS | RA R2 LPIPS | RA R2较R1降低 | R2 full：WC／共同／RA |
|---|---:|---:|---:|---:|---:|---|
| Common seed3 | 0.3092885101 | 0.2937068974 | 0.3830050281 | 0.3378004211 | 11.80% | 38／36／28 |
| Human seed3 | 0.2695200504 | 0.2681484806 | 0.3324403500 | 0.3014515725 | 9.32% | 35／36／28 |

共同刷新相对WC保真改善5.04%／0.51%；逐帧Common93正、Human79正14负。R2 RA相对同批WC失真增加9.22%／11.85%，两场景均93帧退化。保留原R1、R2所有场景、帧、对照和失败，不把当前配置结果扩大为方向否定，也不继续无界搜阈值。

R2完整8路径、8接受视频、288 guided、8 latent、36次更新／72 CFG调用每路径及最初7次DD与匹配Native等价已验收；[完整原件审计](../reports/wc_ra_comparison_r2_terminal_20261010_capture_and_independent_audit.json)与[六配对全93帧评分](../reports/wc_ra_comparison_score_cpu_r2_terminal_20261010_capture_and_independent_audit.json)绑定实际原视频、metric资产与源。GPU全wall2303.391228111461秒＝0.6398308966976281GPUh，raw CPU38.271010秒、评分CPU100.051717秒，原GPU／后CPU／评分均退出0且原PID消失、锁释放。两方法场景仍是曝光开发数据，LPIPS是对匹配原生输出的保真，不能替代物理／语义确认。带诊断流程R2 RA为224.04／221.79秒，WC为267.90／249.79秒；哈希、保存、同步、顺序与CPU并发费用保留，不宣称clean稳定加速。

[跨轮完整核对](../reports/wc_ra_r1_r2_complete_working_point_and_control_comparison_20261010.json)中，WC／共同刷新／Native共六个不变对照的所有36 guided摘要、最终latent、完整解码RGB、初始noise输入、动作／计数、RNG／backend均相同；16项配置检查通过。但所有跨轮条件整体摘要仍不同，严格全状态检查保留false。进一步只读核对prepared输入记录全部相同，WC／共同的checkpoint1216组件只有solver._internal_dict摘要不同；旧记录未保存逐条件字段或原始dict，原因尚未定位。不能把结果相同改称所有条件严格相同，也不依据旧报告猜测原因。下一批预先记录条件逐字段、实际mask及完整raw／numerical求解器配置；此差异不是同批配对结果作废或额外GPU重跑的理由。

[采集核心R4](../reports/wc_mf_a_collection_core_cpu_r4_terminal_20261010_capture.json)实际服务器CPU5.056530秒退出0，source2b6e51a／64载荷和原件独立绑定通过。flow OFF／ON各采集OFF／ON完整36步输出、最终latent、动作／counter／RNG／buffer相同，五文件40分支张量实际保存重读；末登记起点写出失败和poison控制保留。它验证的是原WC／RF全文接口的小型受控权重，不是Cosmos CAL或视频收益；R1缺依赖、R2缺namespace、R3直接夹具horizon错误三次技术失败原件不改。

[完整实际采样实现](../src/wcomr/cfg_guided_w1_sampling.py)接入同源NativePolicy、原RF条件处理、UniPC/Karras及普通安全视频管线，保留AV28／Human／misc／AV51四CAL场景、seed0、35请求／36更新、guidance7、93帧。每场景固定D6完整父路由采集OFF／ON各一次，共8父／8完整视频槽／8起点12与30／64分支速度。原样复用、β=1、原标量W1和从当前paid probe继续deep的teacher在同状态产生真实post-RF速度；teacher只评分、不能写部署缓存或校准D锚点。共享α只在{0,.5,1}按场景等权／并列小α选择，之后接BASE-R闭环和部分MLP候选，不要求A先独立稳定获胜。

[完整CPU登记](../manifests/wc_mf_a_collection_sampling_cpu_r1_preregistration_20261010.json)与[检查器](../tests/check_cfg_guided_w1_sampling_cpu.py)先执行flow OFF与ON各完整8父，以及ON最后父写出失败的完整8父，共24全采样路径／864 solver／1728正常net；两成功批实际重读576 guided、16 latent、128分支，另检查缺场景／缺起点／teacher污染／路由／条件字段、两真实文件截断与最后写出恢复。CPU使用Toy权重／attention／prepare／decode／mock writer，实际执行新batch与已安装WC／RF／condition／完整sampler，禁CUDA／下载／GPU锁／账本写入。当前源码与登记已实现、本地AST通过，真实CPU尚待，不冒充真实CAL。

下一顺序：冻结并推送当前源 → 唯一完整CPU验证和原件回收 → 真实源／资产／配置、完整成本 → fresh资源／锁／账本 → 完整8路径GPU校准。该GPU卡尚未冻结、选定或提交，不缩拆范围；预计整卡≤4GPUh在授权内自主，超过4形成具体整卡确认。

本轮 settled32.674095026904／77.89524658965853，新增48窗口余45.22115156275453GPUh，70历史提交、无R2登记在途。窗口起点29.895246589658527保持；[单次执行约定](../plans/WORLD_CACHE_EXECUTION_POLICY_20261010.md)为完整≤4自主、>4具体确认。无非必要人评，goal active，旧16路6.704055834GPUh卡保持未批准。下面入口的旧进度均按其原日期保留为历史。
