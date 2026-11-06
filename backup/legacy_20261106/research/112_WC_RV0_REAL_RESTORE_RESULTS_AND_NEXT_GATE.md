# W3真实恢复首卡终态：两场景四后缀通过，C/D因果验收仍待补齐

2026-10-04。上一目标轮只复核旧104，属于no progress；本轮完成独立执行器、实际CPU/部署及唯一真实GPU恢复诊断，属于progress。科学goal保持active，完整研究目标和[68反事实刷新价值设计](68_WC_COUNTERFACTUAL_REFRESH_VALUE_DESIGN.md)不缩为本次恢复控制。

## 已验证的结果

[完整汇总](../reports/wc_rv0_restore_r1_summary_20261004.json)、[原runner](../reports/wc_rv0_restore_r1_runner_20261004.json)、[独立终态审计](../reports/wc_rv0_restore_r1_terminal_20261004.json)：冻结GPU source `793beed32c0aa48573e356f9f5850b4fb35295b6` 的唯一 `wc-rv0-restore-r1` 退出0。两个曝光CAL各父36个UniPC更新/72次CFG，step22后各两条14更新/28CFG未干预后缀，四后缀逐输入、输出、deep调用、solver输出、最终latent及完整状态组件均与恢复后的父continuation相等；两次重复各自恢复父状态。

两个父pipeline各fresh prepare一次，生成完整93帧768×432/16fps视频。独立逐字节SHA与完整解码通过，common编码SHA `fa7f466534e7e7984136dfaa9fb47794dedf0c81444229527b9722142715c379`，human_199为 `4d0f0549dbabf04e7f217037c40f6a30f41cb240289162d6fb0fbec2dde982fb`，均复现原官方WC桥。scoped VAE decode策略在退出后恢复原采样backend flags。

这是实际模型、实际冻结 `Video2WorldCondition` 对象的进程内恢复证据，补齐110中Toy条件到真实条件的接口缺口。快照包含条件、WC、完整UniPC历史/网格、latent、RNG、buffers/modes，使用原live velocity closure，未重启独立生成器。对照仍为本次恢复后的live parent continuation及历史官方视频桥，本卡没有新增无观察器父phase。

| 场景 | 父完整pipeline含诊断 | 快照及验证 | A后缀含恢复 | B后缀含恢复 |
|---|---:|---:|---:|---:|
| common | 489.098秒 | 10.676秒 | 112.836秒 | 113.038秒 |
| human_199 | 510.128秒 | 10.881秒 | 120.208秒 | 117.669秒 |

两场景捕获前逻辑tensor副本均2,828,989,246 bytes，其中GPU副本2,828,989,098 bytes；所需两副本加4GiB为9,952,945,492 bytes，现场free分别40,412,774,400/34,463,154,176 bytes。6GiB逻辑cap与headroom门通过。全过程521行外部GPU monitor峰值**26032MiB**；PyTorch allocated/reserved/max统计和每场景saved storage另在原件中，不能合成未测的总峰值上界。快照/恢复/哈希和重复后缀是离线诊断成本，不作为在线调度的加速结果。

## 源码、费用和释放

[111执行与部署](111_WC_RV0_RESTORE_EXECUTION_CARD.md)保留51payload加配置共52项冻结阶段文件，真实R4 CPU197.042秒/35依赖、六官方源码、22范围费用/18回执拒绝控制、actual prepare/native-meta/资产/import/基础冻结类/双metadata及独立部署门。新GPU核心未在运行中改动，唯一run未重提；早期部分快照和CPU失败历史保留。

本次实际live条件类位于 `cosmos_predict2/_src/predict2/configs/video2world/defaults/conditioner.py`，当前文件SHA `d58f515074237843b707d67001751c0e022546061348728e6322faaaa22e837c`，[当前来源观察](../reports/wc_rv0_live_condition_source_20261004.json)记录冻结类AST。六源固定表含基础conditioner，**这个实际子类文件没有在本卡预冻结**；来源观察发生于提交后，不追认为预launch pin或loaded class byte证明。下一C/D卡须显式冻结其文件并核对实际import origin，复用前检查当前来源一致。

[supervisor原件](../reports/wc_rv0_restore_r1_supervisor_20261004.json)实计**1111.423472616秒（0.308728742393GPUh）**，含导入、加载、两父四后缀、失败/记录、退出与释放，低于3900秒。0 stop reason、exit0；3900秒预付已被实费替换，权威[账本](../reports/budget.json)累计**11.022315686839217/12GPUh、45jobs**，余**0.977684313161GPUh＝3519.663527秒**，无inflight。

原2794840/2794859/2794861均已消失，全局f1锁可获取；指定GPU回到24MiB、无compute worker，521行monitor只见本job进程。独立复核原source/assets、全部52文件、原回执SHA、两视频、实费及释放通过。终态CPU审计没有新GPU提交或费用，服务器账本status是结算阶段文字，以独立结果审计为准，不为字符串改写服务器账本。

## 尚缺的科学验收及下一步

当前GPU C/D动作、RV标签和Head训练均0。未干预A/B重复没有验收C/C、D/D、交换C/D或action router OFF，也没有最终有符号刷新收益、同预算调度、独立CONF、语义物理或新的质量保持加速证据。107的稀疏净收益未成立判断不变。两个曝光CAL不是独立泛化，已完成104单次授权保持消耗，不作为新执行许可。

下一先做CPU实际冻结Video2World类与既有单动作接口的联合控制，保留两个CFG槽位、完整14更新/28CFG后缀、C/C、D/D、交换顺序、OFF等价、保护/失败和父恢复全部要求；只冻结当前近似器和dense算子，不扩稀疏自由度。明确branch full-call预算单位、后缀策略、Native参考及评价损失：同状态C/D互距不等于有符号收益，原自适应后缀可能改变未来full次数，不能称等预算标签。

随后用本轮实际加载/快照/每后缀/父pipeline/显存及新增完整scope操作数量估价；不同动作导致的后续full/cache变化和新增参照/解码仍未测，不能把未干预后缀时间直接当所有C/D上界。旧4500秒草案加15秒准入余量需要4515秒，比当前余额多**995.336473秒**，原3900卡也不能重提。下一GPU卡当前未选择或预付，不能缩场景、后缀或删除控制以凑余额；先把完整scope与成本做成可审查结果，若仍超额再报告资源/设计决定。保持不新增人评、付费评分或训练。
