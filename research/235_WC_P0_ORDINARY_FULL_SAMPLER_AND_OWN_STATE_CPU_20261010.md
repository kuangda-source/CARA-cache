# P0 进入普通完整采样与额外状态恢复（2026-10-10）

本轮把已验收的部分刷新核心接到真实冻结的普通 UniPC／guarded pipeline，令 P0 返回进入后续 latent 轨迹。推进三模块统一方法所需部署接线，不以本轮代替等待具体批准的 RA＋A 32 路径 GPU 卡。

## 方法与状态边界

继续使用真实 Block／GPT2FeedForward 类体、WC 与 RF 编译绑定。只修改 MLP 投影计算：选定层4/10/16/22，128-token块；P的实际两层 Linear 在 gather 后执行，inactive 投影继续使用过去来源，当前 attention/norm/gate 保持。D-only校准与P工作来源分开，P来源误差登记 `UNKNOWN_NOT_ZERO`，不得清零RA风险；尚未实现来源感知RA决策。

新增 SamplingOwner 与 DeploymentRoundtrip，把投影值／来源／更新时间、D-only校准全部 anchor 张量和参数、工作缓存来源与年龄／周期、机会次数／噪声与条件身份、成对执行历史与 last 状态纳入额外检查点。物理 net／solver／latent／RNG／buffers／mode 继续由原 CompleteStateRoundtrip 覆盖。额外张量和原物理张量一起受 copy budget 约束。只允许健康且未执行的成对边界恢复，不允许恢复任意失败并解除 poison，不是序列化整管线恢复。

普通四场景采样入口通过十处显式替换派生；逆变换 AST 必须恢复原完整 sampler/条件/guardrail/写出 body。新增实际 P0 owner、完整方法范围、额外状态 roundtrip 与 hook cleanup，其余普通流程保持。AST 等价是源码约束，实际执行仍需 CPU 验证。

## 预登记的完整 CPU 范围

四个声明 Toy 请求 AV28_CPU/Human_CPU/misc_CPU/AV51_CPU，各保留13条路径：SOURCE_D6、TRUE_D_REFERENCE、OFF、DENSE_CONTROL、随机／轮换两密度各自独立 full-GEMM 后 inactive 替换参照、全行 P 非 D 来源。两 flow 共104完整成功路径；两 flow 各完整重复52路径，在最后一个请求最后一条路径的 vector writer 注入失败。完整执行208路径／7488 UniPC 更新／14976普通net，成功104文件／3744 guided＋104 latent，共3848张量重读。故障仍保留全部52范围及实际全36步，不能删除失败路径。

CPU 步序列固定连续 P=9/10、15/16、21/22、27/28、33/34，D继续原D6与36保护步；覆盖连续部分更新、P来源继续C、35周期清空与36新D。这是覆盖已登记历史操作的集成夹具，不根据质量选择刷新位置，不主张新调度方法。原78历史CPU及默认26哈希回归证据保持。

声明小型CPU权重／attention／prepare／unpatchify／decode／mock writer；真实隐藏512 tokens，两密度实际256/384行。每路径在12/30/35/36保存物理与额外状态；CPU显式扰动工作来源、历史、校准 anchor 张量、投影值／年龄／来源和机会次数后恢复，并继续普通求解器。每个成功flow检查180次P来源C、100次连续P及所有实际 Linear 行数。独立32条部分策略全轨迹参照按旧 rtol1e-5／atol2e-6比较；OFF/dense对源、fullP对真实D必须直接相同。每flow七个不完整／来源污染变异拒绝和一次真实文件截断拒绝。

登记：`manifests/wc_p0_deployment_sampling_cpu_r1_preregistration_20261010.json`。服务器独立 `.sync/wc-p0-deployment-sampling-cpu-r1-20261010`，禁止CUDA／下载／真实权重加载／GPU提交／锁与账本写入，原CPU/GPU stage不改。当前只有本地五份新源码 AST 和完整派生逆 AST 通过，实际CPU尚未启动。原实现源匹配审计保留。

## 后续与权限

通过并独立重读后，新增显式语义P的A＋P0读出与来源感知选择，保持真实D校准和P风险边界。旧A按物理非skip登记D，不能直接串接P；原RA＋A283冻结载荷不修改。总窗口从29.895246590开始新增48，当前已结算34.372880296／77.895246590，窗口余43.522366294。完整单次≤4GPUh自主、严格>4需要具体批准；5.147707517GPUh完整RA＋A确认仍待，不拆卡，无非必要人工评审。

本轮 CPU 验证旨在保证实际部分输出、来源状态、恢复与完整采样正确衔接。CPU mock 文件不代表真实 Cosmos 视频，CPU耗时不是质量／真实加速，保留原局部保真改善与整组小幅省时结果。

## 实际执行已启动（尚非终态）

提交source **138fd69a779fe194d627f4198d77d38e885abbc2**／222载荷，独立CPU监督3915957／子3915958已真实启动。[原唯一启动回执](../reports/wc_p0_deployment_sampling_cpu_r1_launch_20261010.json)与[原句柄实查](../reports/wc_p0_deployment_sampling_cpu_r1_original_progress_20261010.json)保存；后者确认两句柄当时存活，flow OFF完成45/52、AV51 RANDOM050在跑。完整208路径、两flow和故障／重读验收仍待，不能将部分成功写成完整结果；同源stage不修改、不复投。预算SHA保持 d4c7c38fa253a10dbe4513b16ba0bd603718bfb1891feef41fb004e59958443b，无本轮GPU或预算写入。

显式A＋P0组合核心另见[236](236_WC_A_PLUS_P0_EXPLICIT_SEMANTIC_SOURCE_COMPOSITION_20261010.md)，只有AST准备，未使用本CPU在跑结果替代组合验证。

飞书revision47→48仅指定成本／下一步段落增补完整采样CPU已启动与组合准备，197块全文规范核对保留其余内容及目标粗体前缀；[同步回执](../reports/wc_p0_ordinary_sampler_progress_feishu_r2_20261010_verification.json)。首次读操作匹配整段不符在写前拒绝，原fetch保留；后续fresh局部替换通过，未重复写入。

## 原完整CPU退出0，独立验收接续

原source138fd69／222载荷回执实际CPU1600.450404870秒，监督与子进程退出0且两PID消失；完整result346404403字节、SHA f2073cf935a37b0a58f7f2b4ca18b93c138f7d07c3e2360b2cbf78f7de29f424，账本前后保持d4c7c38f。该回执报告完整范围通过，最终独立源／3848张量／32参照验收尚待。

原捕获与仅thread2的R2各因55秒观察窗口超时，分别保存original_capture_timeout与thread2_capture_timeout回执；不作为生成失败，不重跑原作业。新增只读R3对原捕获源码仅改审计线程2、非阻塞观察600秒与无损gzip level1，逆源码及AST保持其余完整校验；原222源和全部remote native不修改。调用以短exec/poll持续观察，观察窗口不构成GPU作业限时或新GPU批准。
