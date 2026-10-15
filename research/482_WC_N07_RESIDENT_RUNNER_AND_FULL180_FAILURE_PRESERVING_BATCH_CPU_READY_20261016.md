# N07驻留运行入口与完整180批处理：代码和CPU调度控制准备完成

**最终共同测试已有实际运行脚本，按一次驻留Inference构造组织全部方法和输入；完整排程、失败保留和不同Native步数的记录接线已通过本地调度CPU控制。** 本轮没有部署、选择最终方法/输入或运行真实Cosmos；N05原卡及12:05查收保持。

## 1. 运行脚本如何工作

新增`scripts/run_wc_paper_N07_frozen_shared180_r1.py`，配合481的完整合同、480的原始输入绑定与475的共享执行器：

1. 只读取未来独立冻结配置和回执，不自行选择输入、工作点、GPU价格或生成授权。实际配置目前不存在。
2. 真实CPU入口将用原环境构造160份`InferenceArguments`并回读原参数，核对原生类/源码、普通guardrail与99份旧数值依赖；禁止CUDA/权重/下载。该入口本轮只语法编译，未在真实环境执行。
3. GPU入口必须绑定同一source/config/完整CPU、具体或standing许可、真实UUID租约和原v2任务预留；cap/origin保持原值。没有预留或>=12没有具体批准时不能进入模型阶段。
4. 代码安排一次`Inference(setup)`构造，在原A6000/2B/backend/28层/eval设置下驻留；每路径恢复原采样器、RNG与缓存起点，再调用已接受共享执行器。不启用新P/T1/F/B或部署profiling。
5. 全20完整warm保存各自实际步数的guided原件；Native18/26/35分别按19/27/36更新记录，不写死36。正式160路径关闭逐步复制和哈希，仍保留算法维护；final latent与视频在原计时边界外保存/审计。

原主计时继续覆盖文本编码、去噪和VAE；加载、warm、写盘/取证另列且全部计入卡的实际费用。单次正式计时不替代N08的重复clean速度结论。

## 2. 批处理与原分母

`run_registered_batch`只负责完整排程与记录，真实推理/原件归档由生产callback执行。全部位置按预登记顺序保存，不把拒绝/失败点从分母删除。

- TEXT_REJECTED记录0模型更新并继续后续位置。
- COMPLETE/VIDEO_REJECTED核对实际seed、步数、两分支次数、缓存释放、固定26D/readout掩膜与真实D/P来源规则。
- 技术失败保存原返回状态和错误后停止；`full_rows`保留原执行前缀，为后续未到达位置记NOT_REACHED，不自动补样或重派。
- 旧P0仍为H1合法动作；若出现PP，必须保持近似来源/非零出生误差，不能写入true D。

这补齐运行端代码；独立CPU终态审计/93帧评分与收集入口还需在最终配置后接入。没有把合成callback当真实视频或实际显存稳定性验证。

## 3. 本轮CPU证据

`tests/test_frozen_shared_batch_r1.py`四项：全180顺序/20warm/两seed/三Native请求域；拒绝保留且继续；技术失败停止并保留完整180；错warm步数/seed/固定读出拒绝。

`tests/test_frozen_shared_production_r1.py`原六合同控制一同通过。合计10 passed/4.63秒；CLI语法编译通过。全180callback为标明synthetic的标量假执行，没有采样、真实Tensor输出、模型初始化或实际权重加载；实际加载次数未测。

回执`reports/wc_paper_N07_batch_runner_CPU_controls_20261016.json`绑定当前源SHA。481的大卡记账扩展源码和原v2均未修改；原99数值依赖复用仍适用，不再重复952 Toy。

## 4. 最终启动前还需完成

N05/N06完整接受→开发工作点冻结→fresh身份排除→八来源确定性选择→实际原输入/完整scope→新独立stage的真实生产CPU→终态审计/评分/单次收集与完整费用→fresh v2/UUID及实际许可。N07原180模板不拆缩，>=12或余额不足提交具体整卡决定。

当前N07配置、实际模型CPU、最终GPU卡和费用都未选/未接受。原N05 source15d77ac、1078249/1078290/post1078250、生产stage和今天12:05一次验收不变，本轮0SSH/0GPUh/0预算写，不提前查看其科学partial。F/B关闭，P/T1后排，无新人评、训练或OMR。
