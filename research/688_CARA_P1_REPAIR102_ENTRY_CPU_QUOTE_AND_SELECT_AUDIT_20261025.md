# 新P1生产入口、CPU与完整报价准备

实际观察时间：2026-10-25T02:22:04.386873+08:00。执行源码 `ec87b4b127748056db55a287324ee304cb419d96`。112实验原stage未改，1926注册文件逐一SHA核对相等；未读取112部分科学输出。

## 已完成

- 新入口接上先前完整验收的计时模型依赖。每输入先独立PG全D再采集最多7目标，块完成后评分；bootstrap和全部额外参照计费。
- 三强基线S26_C/S26_A_PHASE/SHARED26_C保持原布局与α；边界控制按冻结时间规则在S24/S25中选，图的A严格遵守原阶段α。
- 首批4之后只有一次最多4的恢复/细化；全超时也可降低D寻求可行性，无第9查询、不改预算、不换SELECT。3固定强基线单独披露，不能称全部信息查询只有8。
- 远端独立1CPU/4GiB、CUDA隐藏的生产入口CPU退出0，独立接受已保存。真实18个采样数值路径/六请求/guardrail/93帧codec与FD控制通过；新102注册上界实际执行100条声明式CPU端点、56组模拟完整评分，未触达位置保留；另有实际固定LPIPS全93帧和独立自适应重放。10项边界测试通过，重放篡改、同位置重派被拒绝。CPU使用声明式112通过fixture，不是当前112结果。

## SELECT核查

本地3461文档、远端501元数据文件，读取错误0、两个冻结SELECT远端执行命中0。首次核查把已接受原P1终态中的select_members列表列为未分类；核对该接受的完整SHA与10个SELECT位置均UNUSED、无任何对应请求/分数/张量后，增加仅此原件的严格元数据分类。四项反例测试阻止修改原件、执行SELECT或新增请求被误豁免。R1阻塞原件保留。准备时通过不替代启动前≤30分钟及首次SELECT前的再查。

## 完整报价与尚未通过的门

102位置、58×93帧评分、3672pairs/7344CFG、单load。未知候选按已接受旧104最慢PG全D完整请求收费，warm/搜索/评分占卡/保存/释放全部计入，无去重抵扣。预计12.638056GPUh、建议上限14GPUh；这是未批准的新报价，预约与GPU提交均0。累计226GPUh、部署257.7712338712067秒、0.8freshNative不变，112的11.9不挪用。

本轮接受的是生产入口及自适应采集/评分/决策重放；**新102命名空间的监督、捕获、独占/精确账单、独立终态组合尚未接受**。旧64或112生命周期CPU不能直接替代。完整112计时门、新102整卡组合CPU和14GPUh专项批准全部具备后，才做fresh资源/账本/曝光/磁盘与空闲硬独占准入。终态自动化已补充此限制，不会看到112通过就误派。

计划：[P1_REPAIR102_PRODUCTION_AND_QUOTE_R1_20261025.md](../plans/cara_policy_generator_20261020/P1_REPAIR102_PRODUCTION_AND_QUOTE_R1_20261025.md)。

原件：

- [cara_PG_P1_repair102_CPU_terminal_complete_r1_20261025.json](../reports/cara_PG_P1_repair102_CPU_terminal_complete_r1_20261025.json)
- [cara_PG_P1_repair102_CPU_accepted_r1_20261025.json](../reports/cara_PG_P1_repair102_CPU_accepted_r1_20261025.json)
- [cara_PG_P1_repair102_SELECT_exposure_preparation_r2_20261025.json](../reports/cara_PG_P1_repair102_SELECT_exposure_preparation_r2_20261025.json)
- [cara_PG_P1_repair102_whole_quote_r1_20261025.json](../manifests/cara_PG_P1_repair102_whole_quote_r1_20261025.json)
