# E2：全72路径输入冻结与E1实际CPU接续

2026-10-11。上一轮将本轮完整单作业自主门槛调整为≤8 GPUh；本轮实际完成确认输入的曝光核对、冻结和独立重建。**40条确认＋32条计时范围保持；尚未完成计时实现、整卡forecast或提交新GPU。** 原32四CAL终点保真和原64逐路径回收结果保持，不把输入冻结当作新科学结果。

## 已完成的输入工作

[选样协议](../manifests/wc_e2_input_selection_protocol_r1_20261011.json)和[只读选样入口](../scripts/prepare_wc_e2_confirmation_inputs_r1.py)在commit c738dfa登记并同步后才执行。固定类别、SHA256排序盐与seed，不读取结果进行选样；排除完整CAL24、工程样本、登记曝光身份及其参考／词面组。实际扫描418份本地configs／manifests、服务器58份outputs实验receipt，未出现读失败，排除28个组成员。

| 固定类别 | 新提示词ID | seed |
|---|---|---|
| av | av_cbf12e70-0268-42c2-bd91-c76d42a86102 | 17、43 |
| human | human_233 | 17、43 |
| misc | misc_4258999-uhd_3840_2160_25fps | 17、43 |
| robot | robot_022 | 17、43 |

四个可选池分别为113／294／89／169组，按每类别相同哈希排序取首个代表。每个新请求仅修改原种子、name与num_steps=35；原prompt、负prompt、guidance7、93帧、432×768保持。先seed17全块、再seed43全块，各含四提示词×五版本；Native拒绝、路径失败和缺失不补零、不换样、不取消第二seed。

[完整72输入清单](../manifests/wc_e2_confirmation_full72_inputs_r1_20261011.json)和[实际请求](../configs/wc_e2_confirmation_requests_r1_20261011.jsonl)已绑定原vendor文件／prompt hash、选样报告与40＋32全部位置。两个共同主候选仍为W1_ONE_PHASE、BETA1_ONE_PHASE，各自对RA单独比较；另保留Native与WC。最大32个确认视频配对、2592主范围solver更新／5184CFG调用。

计时仍为已有AV28／AV51、seed0、四方法各四轮，原计划的平衡四顺序保持。每方法恰好占每位置一次，12种有向相邻顺序均覆盖；全部32条计时位置保留，不把确认路径当clean计时，不挑最短轮次。

[实际曝光记录](../reports/wc_e2_confirmation_input_exposure_r1_20261011.json)保留418份本地文件与58份服务器原件hash、全部命中位置；[独立重建入口](../scripts/audit_wc_e2_frozen_inputs_r1.py)未导入选样器，重新建立排除组／哈希排名、从四份vendor文件重读原请求，核对两个seed、全部72位置与两主比较，[重建结果](../reports/wc_e2_frozen_inputs_independent_audit_r1_20261011.json)通过。

曝光清楚的范围是本次登记及当前WorldCache服务器输出。参考clip和词面组分离不证明原始录制／session或所有语义近重复独立；不宣称跨平台完全未曝光。确认数据只用于冻结方法的一次确认，调参后转为DEV，不在同数据上重复声称独立确认。

## 当前实际运行与下一实现

[现场CPU／预算记录](../reports/wc_e2_input_freeze_and_e1_live_20261011.json)：E1监督4040126／子4040127均实际存活，已写84个Toy tensor文件，无完整result，365载荷registration保持原SHA。没有改在跑源或重新启动；CPU实施证据不能当真实GPU修复或Cosmos质量。

源码阅读确认A readout的signature()目前仅取对象／张量版本／形状等元数据，并非张量内容hash，继续保持该保护。需要从新计时区间移出的纯取证主要在外层sampler：每步guided的CPU复制／内容hash、solver-return hash、研究checkpoint和components；A校准、probe、额外head、来源维护、RNG／buffer隔离与控制器继续计入在线成本，不删除原head或更改alpha／融合顺序。

下一建立受来源约束的完整确认与计时实现，先跑受影响CPU等价／故障控制，再核代表真实路径动作和输出；额外GPU等价路径如需要，必须事前列出并计入同张完整卡，不能挤掉40／32。整卡forecast绑定真实成本、全部取证／加载／重复／诊断／失败／清理，≤8直接推进，严格>8再具体请批。当前不冒称已冻结forecast、已CPU验收或新GPU开始。

累计账本39.183807747546176／77.89524658965853 GPUh，75历史提交，新48窗口剩38.71143884211235；SHA与前轮相同，本轮新增GPU0。无需新增人评、VLM或训练门槛；继续[当前E0—E5设计](../plans/WORLD_CACHE_A_CONFIRMATION_AND_P_RECOVERY_20261011.md)。
