# P 工作参考五读出同状态完整 CPU 预登记

**下一诊断已接入完整采样和物理状态恢复。** 它比较官方 C、旧 D-reference scalar、新 P-reference scalar、旧 D-reference beta=1、新 P-reference beta=1，使五者面对同一个实际当前状态的完整 teacher；不让较好的候选提前改变后续轨迹。353 的两 flow 完整读出实现证据保留，本轮新的同状态执行／评分还未实际通过。

## 科学问题与控制

H-P-W1-WORKING-REFERENCE保持：beta仍来自真D，P不是零风险锚点，当前P工作probe/residual是prewarp坐标。本轮要先回答“换参考点能否减少当前guided误差，以及在哪种来源／年龄／阶段／flow中有效”，而非先以更改轨迹制造表观近似收益，也不以一个局部阈值否定部分刷新方向。

每个点从实际出生后当前latent、条件、求解器历史、物理缓存、D校准和所属控制状态开始。先做完整teacher并恢复；官方C、新P-scalar、旧D-unit、新P-unit分别计算并恢复；旧D-scalar最后计算并作为原方法继续采样。五次C都验证相同输入、完整D统计和当前source缓存；teacher不写部署锚点。完整head及probe均计费，没有合并E5省head。P/D出生后仍各强制四步C，这是离线诊断，不主张已具备在线可复用寿命。

D来源上，P-reference scalar应与旧D-scalar、P-reference unit应与旧D-unit逐元素相同，是两组强控制。P来源则记录所有五种误差、fallback及阶段alpha，不用只挑“最好的候选”报告。最终保持旧D-scalar轨迹，原完整OFF/ON父、两次自然suffix重复及它们与原父切片的控制均保留。

## 完整范围

两已曝光CAL AV28/Human，原seed0，原E4c事前窗口birth13/25/12/27，在flow OFF和ON中使用相同固定位置。位置源于旧ON轨迹；OFF自然第一动作可能不同，新版本如实记录且对照其自身原轨迹，不把OFF强制P出生叫作自然P选择、不按误差重选位置。

| 项目 | 每种flow | 两种flow合计 |
|---|---:|---:|
| 原完整父路径OFF/ON | 4 | 8 |
| 早／晚窗口 | 4 | 8 |
| 自然重复、P出生C4、D出生C4 suffix | 16 | 32 |
| age1/2/4同状态点 | 24 | 48 |
| 五读出C计算 | 120 | 240 |
| 同状态完整teacher | 24 | 48 |
| 全部父／suffix／额外候选／teacher pair | 344 | 688 |
| 两CFG调用 | 688 | 1376 |
| 全原张量文件／张量 | 44／580 | 88／1160 |

每个同状态点执行5次完整恢复（teacher后和前四候选后），另保留窗口及原采样器恢复。候选输出全部保存，原reader的父／自然repeat／基准C及teacher检查通过显式兼容视图复用；新增192张量/flow独立读取并重建所有五种FP32 CFG误差的FP64归约，D-source逐元素控制48/flow。整体420次直接比较、26合同拒绝、两种flow文件截断拒绝均纳入完整CPU范围。

新owner/readout/sampler/audit模块独立于旧E4c及在途E5。仅删去旧run_event对“自然首步必须P”的要求，改为记录实际首动作；所有自然分支与其原完整父的严格等价保持。候选始终恢复到原部署method/variant，非法候选或不完整恢复直接拒绝完整范围。

## 执行与边界

完整CPU卡 `WC-P-REFERENCE-SAME-STATE-COMPLETE-BOTH-FLOW-CPU-R1-20261011-A`，444冻结来源，复用原R6实际导入适配、WC/RF/Block/full UniPC和原生AdaLN LoRA/Wan FP32 checkpoint head。小权重、attention、prepare/unpatchify、decoder/writer仍为声明的Toy边界。所有新增代码语法通过；独立服务器CPU待。没有新GPU、训练、人工评审或账本写入。

下一真实整卡沿完整两flow/全部控制准备，须在本CPU和实际生产接线验收后绑定完整加载／计算／head／hash／复制／恢复／I/O费用。当前没有可准入GPUforecast，不能凭计算次数比例或旧2.5776h数字直接启动。单次完整≤8GPUh自主、严格>8具体确认，累计77.895246590上限不改；E2/E3原above8具体问题保持，不拆卡或重复询问。

原E5全24／eff2b71／456来源和原GPU4103103/4103190、自动终态CPU4103104继续；live5 Unix1791693188.389核对仍活、AV_R1两OFF完整36步、旧W1继续。完整终态仍待，不修改其方法或载荷。前已结算41.908688946GPUh，新48余35.986557644，当前E5预留不是已实耗；目标active。
