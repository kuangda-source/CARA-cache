# 最小有限CAL开发预注册

四个旧CAL顺序由CAL66绑定：AV28、human199、misc、AV51；精确name/prompt/seed/config在矩阵中，seed0、guidance7、432×768×93。只使用旧曝光CAL，原最终16不参与选择。CARA固定Shared25-C。

A阶段26条：6warm → 12数值A/B诊断 → 两CAL各Native/CARA锚点及tau .04/.06，共8条clean路径。释放并结算GPU后，CPU对4候选视频逐93帧Alex(to本阶段Native)评分。两候选必须都在两CAL完整有效；否则NO_SELECTION，不补选有利子集。

选择规则：两prompt均满足abs(T_DD_tau/T_DD_CARA−1)≤5%的候选优先，选mean Alex低者；无匹配者选最大逐prompt相对时间失配最小者，标UNMATCHED，再以mean Alex、小tau破同分。不得按结果扩大网格。冻结记录包含选中参数、全部候选、时间/质量、数据与source SHA；未入选视频和费用保留。没有线性插值出的虚假工作点。

B阶段47条：新加载7warm → 4CAL×7角色28条 → 前两CAL×6角色反序时间复测12条。Native/allD/README/PaperPort/Tuned/RA/CARA均同批；角色首轮顺序在相邻CAL交替正反，复测固定反序。原校准输出不复用进正式表，避免将不同驻留/热轮次当同批时间。B不再调tau，即使时间匹配不佳也如实保留。其他两CAL只评价冻结参数。

时间重复先在prompt内聚合，再四prompt等权；不把两轮当n翻倍。所有4CAL首轮都有实测时间，不能将前两CAL复测时间填给后两CAL。allD是身份控制，不作为加速优势。

本轮只是开发描述，不对4旧CAL作独立最终确认主张。最终16的原身份和角色合同保持；冻结后另列全费用与执行申请，不能按最终结果重调WC/CARA或挑seed。额外19D、Euler35、第二模型不在73条中。
