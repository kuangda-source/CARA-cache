# 完整输出首卡：先官方/D 等价，再两个 WC/S 闭环配对

2026-10-03。独立 card `WC-FULL-OUTPUT-R1-20261003-A`，唯一 run `wc-full-output-r1`。依据累计12GPUh授权与持续自主实验 goal 选定，不复用已消耗的104点/H0/H1单次窗口。承接[82 CPU接线](82_WC_COMPLETE_SAMPLING_AND_REFRESH_CPU.md)。当前为实现/成本/实际部署准备；是否启动以本卡的 launch/现场回执为准，文档选定不等于GPU运行。

## 冻结范围与顺序

1. `common_sense_6487f37f-ef57-49ca-afdc-d898922b5191` 做完整 D/D 控制：官方无刷新适配器 baseline，随后安装 dense-only 来源适配器并在13/21/33/35/36进程内恢复。严格九项原生状态/输入/输出/trace/grid/condition门和最终sampler/decode/guardrail/write文件/RNG相等后才能进入S。
2. common和`human_199`各做官方WC、WC+S两个完整路径，seed0，共四输出。每对共享一次官方prepared batch与其RNG转移；D/D控制与随后common配对重新准备输入，因此前一个控制视频不复用为后一个对照。共六phase/六输出的计划分母保持，不替换失败样本或在该卡内重提。
3. Cosmos-Predict2.5-2B、原setup/输入、93帧/432×768、guidance7、35请求/36实际UniPC更新/72CFG、原WC horizon70保持。call70清空；最后两call计数0/1完整暖启动。明确shared eval和decoder_policy(True)共同使用，guardrail完整保留。两场景已曝光，只作开发诊断。
4. 只有官方已经决定刷新、paid probe、retention阶段、同CFG两次过去真D时允许S；probe2以及层6/23/27保持D，deep其余self-attention用现有sm86 routed/no-PV sim0.1/cdf0.98。MLP/cross/QKV/RoPE/head、Gamma/flow/OSI/官方判据保持。真实QKV为B1/N31104/H16/D128/BF16。S产物只进入标记为approximate的native forecast window，不能进入true-dense历史；绝对call/epoch/request/model/CFG/condition/group隔离。

原生九門只比较原来模型/求解器/RNG以及新增buffer/mode盘点；额外来源sidecar的五处签名单独存档，避免官方路径天然没有sidecar导致伪等价失败。恢复仍校验完整native+sidecar，不能遗漏来源状态。D/S记录真实改变的latent、输出、官方自适应trace、来源事件与kernel选择比例；不要求D/S哈希相等，不读取dense teacher或错误决定动作，不固定baseline刷新位置。

## CPU、实际加载与拒绝协议

先在实际Torch2.7.1+cu128中禁止CUDA，验证完整D/D、D/S恢复/来源与失败分母，新增同一生产函数的六输出组合（flow OFF/ON）及候选解码失败，另测固定scope/成本/预算拒绝控制。真实官方prepare/metadata、source/import/资产、现有package八文件SHA和meta原网络1173模块/shared eval/buffer inventory随后再验。stand-in 不代表CUDA/权重/VAE/视频；前一轮r5 source不能接受本轮修改。

每个phase必须普通返回并产生非空预期mp4。text/video guardrail拒绝不保存输出，不绕过；首个技术异常或缺少预期输出停止本卡，已有phase和六输出计划分母保留，未执行者记为未执行。DD不通过则不进入任何S，不自动第二卡。GPU中记录实际parameter对象/版本、真实named buffers/modes、hook和forward清理；不是独立序列化的整管线重启。

## 成本和准入

[完整成本包络](../reports/wc_full_output_r1_cost_20261003.json)：六次36更新各18秒规划、六套decode/guardrail/write各75秒、加载114秒、startup50秒、首次kernel/额外来源维护150秒，raw4752秒；20%余量为5702.4秒，另结算30秒，共5732.4秒。它是保守预测，不是耗时或显存保证；完整六输出不能塞回旧1800秒。最多一次6000秒全cost、5970秒child、kill-after5秒，累计12GPUh账本预留后按实际全wall（含失败/释放/flush）结算。

当前已用6.055044055960606/12h、36jobs，余5.944955944039394h；最大预付1.666667h后仍有余额。提交前须冻结source/payload并同步GitHub，实际全CPU/source/assets/import/package通过；重新核对指定sm86 GPU的VRAM/compute、全局f1锁、无inflight、磁盘≥15GB与账本余额。保持单昂贵任务，不停止他人进程。

此处逐步hash、checkpoint深拷贝、condition/finite/路由同步与prepared replay均影响wall及两臂工作量。全wall计费，但不作净E2E加速比较。若产物和闭环成立，随后再单独做真实两臂完整准备、冷/热口径/顺序/重复明确的轻量时间卡；不能拿当前debug两phase wall相除声称方法更快。

## 完成后的自动证据

先核对六文件路径/原件SHA、全93帧decode、432×768/fps16/finite/帧完整性、source、九门和provenance。D/S需要实际S调用、fallback无S、同CFG过去来源、call70来源失效、缓存命中使用标记近似等证据；仅加载或exit0不算闭环通过。

再报告每对RGB MSE/PSNR/SSIM、首末时间段保真、逐帧差分的运动能量/时序差分及相对变化。提前明确这些是描述性保真与运动代理，无语义/物理接受阈值；不将低RGB误差、像素运动或视频更静止称为质量提升。结构门失败不丢分母。当前不引入人评/付费评分/训练，也不把两个开发场景当CONF；方法接受仍缺调优WC、少步Native与独立数据的公平曲线。

## 实现阶段CPU记录

[初步实际CPU](../reports/wc_full_output_cpu_r1_20261003.json)229.492秒通过。生产函数原生50组件与sidecar五个checkpoint分开；无adapter→dense adapter严格九门/最终pipeline成立，flow OFF/ON各六phase432CFG/两个候选配对通过，候选decode失败保留DD及六输出分母。完整服务器部署阶段需将最终config/payload/资产/import绑定到新冻结source后再验，当前记录不是GPU准入。

实际部署准备r1/source34f2d86在CPU加载test_prepared_input时缺少打包依赖mid_parity_scope，未进入控制/模型/GPU。原stage与[失败回执](../reports/wc_full_output_r1_deployment_failure_20261003.json)保留；仅补齐纯Python依赖，在新deploy2 stage重新冻结验证。此为准备失败，非稀疏方法或视频结果；唯一GPU run尚未提交。

## 实际部署门终态

[deploy2回执](../reports/wc_full_output_r1_deployment_20261003.json)绑定冻结source`b3ed6b084b5e7bad5a242bd9a934a0d502e1ef6c`：完整CPU11/19/3、官方prepare与metadata、原网络meta/shared-eval/buffer inventory以及全部source/assets/import/package通过，无CUDA/权重模型执行，账本未变，现场全局锁可用、数据盘564GB余量。原缺依赖准备失败保留，唯一GPU run尚未提交；提交仍需再次现场准入。

S使用现有QK量化/选择与稀疏执行，S−D包括backend量化和稀疏效应；本视频卡不是纯稀疏因果分解。此前matched-full局部对照保留，不据该卡独占归因。
