# 完整轨迹动作覆盖：三条原生WC轨迹都包含混合CFG动作

2026-10-09。**当前共同 CC／DD 接口对照仍有必要，但它不覆盖原生 WorldCache 的全部实际动作。** 全部三条已完成轨迹均出现 DC（条件分支完整刷新、无条件分支复用）；后续完整36步部署不能把这些位置静默改成共同刷新，然后仍称原生动作等价。

## 实际执行与完整证据

按[H-T59登记](../plans/WORLD_CACHE_FULL_TRAJECTORY_CFG_ACTION_ALIGNMENT_CPU_20261009.md)，先冻结已有 Human seed2／seed3、Common seed3 三卡的 capture／runner／CPU score／supervisor，共12文件；压缩SHA和既有capture内原字节SHA均绑定。只使用已经完整验收的旧卡，不读当前H-T58部分张量或评分。

R1 source `4d9e967` 在样本名元数据处 `KeyError: sample_names` 退出1；旧生产配置把请求存于 preregistration，而非该顶层字段。原stderr、空stdout、完整216对分母与失败回执保留，不追认为成功、科学负结果或方向被否定。R2只改读取规范的 `confirmation_request`／`same_existing_request`，原输入、范围及假设不变，预登记并提交推送后执行。

R2 source **81c5d5c083b3d171a24ce0c162d25c10b0569799**，实际标准库CPU timer **0.148897458秒**，完整 **6父／216 CFG对／432父net调用**通过。三卡原40对／120实际张量／20重复的旧全量CPU验收、两父输入／输出／deep／banks／solver／终点及视频parity均重新核对。当前没有再次加载模型、视频或原张量；“原张量曾完整验收”与“本轮CPU记录复核”分开报告。

[完整216行结果](../reports/wc_full_trajectory_cfg_actions_cpu_r2_20261009.json)保留每一步的两槽deep访问，实际0／26映射C／D，起止步均不排除。[独立重建](../reports/wc_full_trajectory_cfg_actions_cpu_r2_independent_audit_20261009.json)另从完整调用位置集合重建两槽动作、216行和所有计数，不依赖收集器的配对汇总。OFF／ON重复父全部保留，但不作为独立场景。

## 完整36步结果

每条轨迹的 OFF／ON 动作完全一致，下表去重展示，完整结果保留全部两父。

| 原轨迹 | CC | DC | CD | DD | 实际full／cache调用 | DC位置（solver更新） |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| Human seed2 | 18 | 1 | 0 | 17 | 35／37 | 28（call55／56） |
| Human seed3 | 18 | 1 | 0 | 17 | 35／37 | 27（call53／54） |
| Common seed3 | 16 | 2 | 0 | 18 | 38／34 | 23（call45／46）、33（call65／66） |

因此，完整六父有8个混合pair，对应三条曝光轨迹里的4个去重位置。108个去重轨迹内位置不是108个独立视频样本。本轮未出现CD，不能据此删掉实现或未来对照中的CD支持。

共同OR规则把旧mask的每个混合DC改为DD，算术上Human各多1个full、Common多2个full。这只是**固定旧mask的计数映射**；重新执行会改变缓存、latent、solver历史与未来自适应动作，因此不能把它报为新策略full总数、同预算或速度变化。

## 对下一步的影响

H-T58登记的是同S22固定CC／DD的原／成对接口等价、两完整原父非干扰及对应显存／成本，范围保持，不因本发现取消、扩大或改写在跑156载荷。Common原轨迹step23实际为DC，恰好说明“本轮两种共同动作能执行”与“完整原生动作能忠实回放”是不同要求。

下一低成本实现对照应支持全部CC／DC／CD／DD，并覆盖完整36步（包括保护区、70调用循环尾部与最后两CFG）。保留原CC／DD控制、观察开关、严格重复、冻结条件／RNG与完整恢复；完整原生mask回放和共同OR／AND策略是不同实验，不互相替代。现有接口仍未产生终点／未来成本标签，不能训练Head或称为新方法优势。

RA式联合风险、简单共同刷新和原生分支独立路由仍应作为后续比较对象；本轮未校准或执行RA，也不把混合DC本身等同为有害动作。是否有害要看同状态动作和后续真实生成结果。

## 原GPU与预算

当前原H-T58的3445779／3445791／3445780实际活，冻结source9f01274／156载荷不变，原OFF父已完整保存，ON父继续采样；完整16pair／48张量／两全93与绑定后CPU仍待。最新句柄与日志证据见 `reports/wc_real_paired_interface_r1_full_trajectory_alignment_live_20261009.json`；checkpoint不逐步刷新，不将未更新计数解释为停止。

本轮CPU无Torch／新GPU／预算写入。实际已结算底数29.027073215／50GPUh，第65在途used50仅原任务预留，不是已耗尽。当前GPU不复投，终态整卡实wall结算。goal active：上一轮是完整CPU／GPU派发进展，本轮是216对完整旧轨迹兼容性新证据＋特定原活句柄verified wait；暂无重要阻碍，不引入人评或训练，不改变主方向与权限。

## 下一实现已准备，尚未通过模型CPU或GPU

新增独立 `src/wcomr/cfg_paired_probe_mixed.py`，不改当前冻结156文件或原CC／DD执行器。它保留原生产preflight、双prefix、counter／RNG、保护区与失败poison，只扩展合法动作并按每槽C／D续算；原顺序参照支持相同四种动作。实际本地标准库编译、来源SHA与精确逆AST通过，Torch未加载。证明见 `reports/wc_paired_four_action_compiler_preparation_20261009.json`；**静态编译不等于任何模型或完整采样等价**。

[H-T60完整CPU准备](../plans/WORLD_CACHE_PAIRED_FOUR_ACTION_FULL_SAMPLER_CPU_20261009.md)明确下一保留三条全36步原mask，并加合法区四动作循环以覆盖CD；两flow／观察／重复，共32比较／64完整路径／2304 solver／4608 net，加全部旧68行与失败控制。完整fixture、实际生产来源与原H-T58真实结果需核对后，再准备新GPU完整费用；没有选择或执行新GPU。

飞书CLI已把完整轨迹的DC边界补入原最后一段，全回读 **revision21**，154块／21节／20表／4公式／49链接。其他153块逐块保持，替换文字／链接全相符，无warnings；完整读写与验证见 `reports/wc_group_meeting_feishu_full_mask_boundary_verification_20261009.json`。没有把CPU覆盖检查或编译准备追加为视频质量成果。
