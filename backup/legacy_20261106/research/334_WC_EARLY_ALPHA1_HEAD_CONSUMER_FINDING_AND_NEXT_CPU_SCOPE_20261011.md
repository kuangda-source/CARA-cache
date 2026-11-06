# 早期α=1输出head：已有调用中的具体省算机会（2026-10-11）

**发现了可以直接开发的成本优化入口：阶段W1／β=1在四个已曝光CAL视频中，分别有108／112次分支调用已由修正输出完全接管，但原输出head仍被计算。** 这是原完整32卡中的实际调用统计，不是预测视频加速，也不是新方法结果。当前E4c在跑、E2／E3冻结方法均不变。

只读脚本`audit_wc_early_head_consumers_r1.py`绑定原32卡独立验收、runner原件bytes／SHA、6份本地消费者源码，以及服务器固定WC／MinimalV4DiT源码。重新读取全部16条A路径／576更新，按每一步实际action／alpha／branch_status／extra_heads计数，原4场景全部保留，没有按正例挑路径。输出`reports/wc_early_head_consumer_source_audit_r1_20261011.json`。

| 方法，均4条完整旧路径 | 原始head调用 | 额外候选head调用 | α=1且候选已存在的分支数 |
|---|---:|---:|---:|
| W1_GLOBAL_1 | 288 | 176 | 176 |
| BETA1_GLOBAL_1 | 288 | 180 | 180 |
| W1_ONE_PHASE | 288 | 174 | **108** |
| BETA1_ONE_PHASE | 288 | 178 | **112** |

阶段版对应原全部head调用中的108/(288+174)=23.38%、112/(288+178)=24.03%潜在可省调用。**比例仅指head调用，不是整个pipeline、GPU时间或可兑现加速。** 各分支fallback仍必须保留原head；晚期α=.5仍同时需要原／修正输出。

## 源码证据与需要处理的状态

叶子`GuidedW1Readout.output`和`PartialDeployment.output`只记录一次输出完成标志，不读取head数值；中间组合仅转发。α=1的共享输出融合返回proposed，原数值仍经过有限性／坐标校验。RA／source选择先在双浅层probe后作出，完整C动作提交不由head数值拟合真D。

固定WC源码最后仍将原head的unpatchify结果clone到`previous_output[branch]`。对当前主runtime所有`previous_output`引用重新搜索：只有初始化、赋值、重置和长度检查；Flow Warp读取`previous_input`、`previous_internal_states`与残差，没有读取该输出数值。不能因此称该字段“不存在”：完整物理快照／hash合同仍包含它，额外运行时consumer／hooks也不能仅靠AST假定不存在。

因此不能仅删掉原head并继续声称完整旧状态相同。下一版本要明确该字段在当前模型／方法／源码内是否只有记录作用，在自身安装版本内继续完整捕获和严格恢复，跨版本显式报告该字段值的差异；真D、P来源、条件、solver、RNG和保护步不放松。原实际输出的有限性检查要由返回的合法候选输出承接，fallback保持原样；异常、非finite、额外hooks／有副作用head不能悄悄接受。

## 下一低成本区分：H-EARLY-HEAD-ELISION

按已有E5“确认消费者后删冗余head”任务预登记，不扩展GPU矩阵。先在独立CPU版本覆盖现有阶段W1和β=1、两flow、两CFG；早期CC且实际候选存在才走快速分支，DD／PP、晚期α=.5、OFF及无候选fallback继续原路径。每个版本各自的完整状态恢复仍须严格相同；跨版本比较输出／动作／真D／solver／RNG与条件，并显式检查、保留记录字段差异。

固定原native FinalLayer源码，并在实际被安装的head上检查eval、buffer与hooks；静态没有self赋值不是动态无副作用的证明。CPU验证必须覆盖两分支候选不对称、fallback、晚期融合、源读取和完整checkpoint恢复，拒绝stateful head／参数或条件变更／nonfinite。优先复用现有纯输出转换／物理恢复测试，受影响函数和新状态合同才重验。

CPU通过后再冻结少量完整真实等价与费用卡，按整卡scope／cost／≤8权限准入；旧Native／视频质量参照只在输入／输出严格等价时引用，实际速度须同边界重新测。改动不回写E2、E3或正在跑的E4c，不把旧结果追认为新实现结果，也不增加训练或人工评审。

当前这轮新增GPU0，reader没有写账本。E4c仍由4075406／4075494原句柄运行，实际P/D age原件陆续写入，原4父／4事件／16suffix／24点保持。只有取得原作业终态与独立24点审计后才报告来源年龄结论。
