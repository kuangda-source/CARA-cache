# N10已接入R2全部正式位置，本地ViCLIP实体字节恢复

2026-10-17。等待N12三臂卡期间，完成了**真实R2输入到自动质量评价的元数据接续**，并恢复了被iCloud卸载的ViCLIP本地实体文件。本轮没有提前查服务器、启动GPU或加载质量模型；N12原source/句柄、22:46半程与10月18日00:01验收不变。

## 1. 实际完成的输入接续

复用原`automatic_quality_inputs_r1.prepare`和原metadata CLI，读取[已接受R2原180位置](../reports/wc_paper_N07_refusal_repair180_R2_terminal_collection_20261017_1250.json.gz)及其canonical独立接受。R2的1750份原注册已含固定测量协议SHA `9755122b22349d9cd5b1cfe43460e73044360e240d941df11d6ca4150b817734`；该协议早于生成，维度/抽帧/静态适用规则不改。本轮不用旧失败R1的20视频子集，也没有重新生成视频。

[全量输入包](../reports/wc_paper_N10_R2_accepted160_full960_input_preparation_20261017.json.gz)保留八提示词×双seed×十方法的**160正式生成位置、六维960指标位置**，生成六份独立metadata文件。

| 原位置状态 | 数量 | 在自动质量矩阵中的处理 |
|---|---:|---|
| 真实完整接受视频 | 129 | 五个有适用模型维度，共645个待评分位置 |
| 文本拒绝 | 20 | 保留原生成状态，不补视频或填零 |
| 视频拒绝 | 11 | 同上；两种拒绝合计155个视频不可用指标位置 |
| 静态闪烁适用范围 | 160位置均不适用 | 原输入无预登记静态标注，全部保留N/A，不从生成结果事后标静态 |
| 全部指标分母 | **960** | 645待评分＋155视频不可用＋160不适用 |

五模型为DINO、AMT-S、ViCLIP、RAFT-Things、MUSIQ-SPAQ；维度分别为主体一致性、运动平滑、整体文本视频一致性、活动程度和MUSIQ_LONGER512。活动程度不当成单调质量，六维不合成一个加权总分。测量使用原协议的各维抽帧规则，不把ViCLIP的8帧输入称作93帧语义评价或完整官方VBench。

自动质量是逐视频评价，**没有沿用LPIPS的匹配Native可用性过滤**。因此原129接受视频都进入合适维度的待评分范围，而不是只保留有原生参考的126条。配对方法比较仍须两seed完整的共同提示词队列，不能填缺失参考或混用队列。

## 2. 独立核对与禁止误用的边界

[独立原件核对v2](../reports/wc_paper_N10_R2_actual160_metadata_independent_acceptance_v2_20261017.json)另读原R2与协议，逐960位置核原case、方法、seed、完整提示词SHA、视频SHA、原生成状态、逐维抽帧及六metadata文件SHA；拒绝与N/A均从原件推导。原接受视频的93帧RGB审计身份照原绑定，不重读视频或加载模型。

[真实960正例和8负例](../reports/wc_paper_N10_R2_actual960_metadata_negative_controls_v2_20261017.json)通过，覆盖缺指标、改提示词/抽帧、缩方法、事后静态标注、换原source、把拒绝视频补造以及把规划身份冒充可生产身份。负例重新计算fingerprint后仍被拒绝，避免只测校验和失配。

[评分器声明](../manifests/wc_paper_N10_R2_accepted160_expected_scorer_declaration_20261017.json)只绑定预期固定源/五权重，明确`production_eligible=false`、真实模型CPU证明为空。**本轮新质量分数仍为0。** 五模型实际CPU接受后须重新绑定正式评分器身份和完整输入包，不把当前预期身份直接升级为已测身份。

当前N10矩阵评价原N07冻结十方法，不含正在运行的N12三臂新配置。如果N12产生新候选，其独立输入确认与对应质量评价另作完整设计，不把原十方法视频重命名成新方法结果。

## 3. 本地权重恢复：解决后续传输的实际阻碍

原R4目标文件在本轮初查时逻辑大小仍1710545812字节，物理blocks为0，是本地iCloud占位文件。[定向恢复请求](../reports/wc_paper_N10_existing_R4_targeted_materialization_request_20261017.json)只要求恢复这一个现有文件，没有删除/替换原件、重新下载另一版本或改代理。

[随后一次本地查收](../reports/wc_paper_N10_existing_R4_local_materialization_one_collection_20261017.json)确认实体已恢复，独立全文件SHA为：

`7a4d6ad6eac6632db3693f4b97f9f8f6445b65b1e139a6fc6686150522238c56`

与原固定官方revision、原R4完整接受一致。再用原relay的`accepted_local_resource`核对原capture、source、目标路径、完整大小/SHA，记录[原relay本地入口接受](../reports/wc_paper_N10_restored_R4_original_relay_input_acceptance_20261017.json)。这是本机资源恢复，服务器和模型运行状态仍待接续。

## 4. 接下来的必要工作

1. 完成原N12三臂的半程/终态查收并先解释三比较；本轮不提前读取其科学partial。
2. 在GPU测量结束后，沿原独立SCP relay接入这份同SHA文件，核服务器完整SHA；原失败/partial保持。
3. 原完整五模型实际CPU构造、依赖、FP32/eval/无梯度及真实前向接口接受，保持五模型全分母。
4. 用真实CPU/资源证明重新绑定N10正式评分器和原160/960输入，补整卡全成本、实际生产CPU、部署/终态独立接受。全部实际评分GPUh计入同一cap226，严格少于12自主、达到12具体整卡确认，不拆卡；准备不是实测费用。

本轮0新GPU、0SSH/SCP、0模型加载、0评分、0服务器账本写；N12原2.25GPUh预留与全部预算历史不改。F/B关闭，未引入人工评审、生成器训练或OMR。
