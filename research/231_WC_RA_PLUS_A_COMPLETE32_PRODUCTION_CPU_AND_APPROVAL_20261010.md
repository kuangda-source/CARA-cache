# RA＋A完整32路径卡已完成生产CPU准备

本批已具备可以执行的真实闭环比较：让A读出进入自己的后续生成轨迹，在固定RA控制器下比较全局／一次阶段强度以及拟合β／固定β=1。四场景、七方法与四原生参考完整保留，终点保真和实际费用将一起报告。

## 完整卡与科学问题

卡：`WC-RA-PLUS-A-FULL-VIDEO-R1-20261010-A`，run：`wc-ra-plus-a-full-video-r1`。四个已曝光CAL原seed0：AV28、Human、misc、AV51；每个WC、JOINT_NATIVE、RA、W1_GLOBAL_1、BETA1_GLOBAL_1、W1_ONE_PHASE、BETA1_ONE_PHASE，另四普通匹配Native，共32完整路径。固定35请求／36UniPC-Karras更新、768×432／93帧／16fps、guidance7／8c−7u。阶段版只有既定step25边界，早α1、晚α0.5；不增阈值、边界或α搜索。真实prior与R2阈值保持。

这张卡回答三件事：联合控制下的浅深增量能否改善最终视频保真；一次阶段修订能否缓解晚期过修正；标量拟合是否确实优于强β=1控制。保留四CAL与跨seed prior迁移的开发属性。现有局部guided MSE W1改善27.76%／β1改善29.65%是方法开发依据，当前没有本卡候选视频结果。

完整最多1152solver／2304正常net、1152guided／32latent、28全93配对。A只读过去本分支实际D来源，无教师／额外deep；额外输出头与原头同时计费。原生拒绝不替换，不填零；评价用原FP32 Alex LPIPS与视频读取／离线资源源码。原正负视频、MUSIQ/VQA和RA R2反例保持。P0真实整组原任务继续，不要求A/P0单独先胜出才允许组合。

## 已完成的完整验证

完整原R3 source b1036ea实际1315.932865秒退出0；128实际路径、4608solver／9216net、2304guided／64latent重读、126tensor／128mock视频、32变异拒绝、两截断与两末写出故障验收全部通过。声明Toy原管线边界。Mac本地resolve造成的捕获KeyError原件保留；只读服务器alias复核后，原native字节不变，独立reaudit通过，未重跑CPU。

实际生产source **87bf992e3edcc8923a31777a900b91a6dfbcd91d**，283绑定载荷、监督3909404／子3909406退出0消失，**54.943355871秒**。四个真实请求、实际guardrail cache／Blocklist、模型forward原出处、完整比较导入、原实际表fingerprint及八区间R2阈值重建、全部27配置与请求变异拒绝通过。CUDA未初始化、GPU新增0、账本SHA前后保持。机器回执：`reports/wc_ra_plus_a_production_cpu_r1_terminal_20261010_capture.json`。

最终准备配置：`configs/wc_ra_plus_a_production_r1_20261010.json`，SHA `a7c3fb6c69a072cf49c60e0148be05b22650621cd7c2d639fe0643592e64f126`。登记：`manifests/wc_ra_plus_a_r1_preregistration_20261010.json`，SHA `7d208bb864fb4779f117a16d0fb3c0af9677cb45d89314b10f12c75b3eb48a1f`。完整范围与费用见[230](230_WC_RA_PLUS_A_COMPLETE_CARD_PREPARATION_20261010.md)和[方法计划](../plans/WORLD_CACHE_RA_PLUS_A_FULL_VIDEO_R1_20261010.md)。GPU未选定、未启动。

## 费用与当前待确认

完整经验预测 **5.147707517089633 GPUh**，计入原新增48 GPUh窗口。已结算33.192083029／77.895246590、窗口余44.703163561；P0在途实费另计，服务器预留不算已花费用。CPU准备预算快照是来源，生产CPU另保存实际前后账本，真正GPU启动仍检查fresh余额／无在途／共享锁／UUID／显存。

用户当前直接规则为完整单次≤4 GPUh自主、**严格>4 GPUh需具体确认**。完整卡、CPU和生产回执已准备后提出本张卡确认，当前回复待；不以累计预算视作已批、不拆卡或删除对照。旧6.704／16路径卡仍未批准，也不由本卡代替。goal active，原P0继续；本张卡确认后只加入原授权与选定CPU绑定，再fresh准入唯一提交、原全量终态及全帧评分。
