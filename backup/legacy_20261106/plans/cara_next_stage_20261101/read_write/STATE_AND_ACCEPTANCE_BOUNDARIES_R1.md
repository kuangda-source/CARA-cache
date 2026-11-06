# 首轮状态语义与验收边界

本页把[讨论稿](SOURCE_FRAMEWORK_20261101.md)落到现有执行器；不是完整模型反向或GPU资源接受记录。

|状态|当前实际来源|四格中的归属|首轮处理|
|---|---|---|---|
|当前latent|原sampler的`latents`|y，随read|在当前solver.step之后分开，不只替换velocity而遗留错误历史|
|UniPC预测历史|`model_outputs`、`last_sample`|y，随read|保留实际完整值；VJP不detach它们|
|UniPC离散状态|`timestep_list`、`lower_order_nums`、`this_order`、`_step_index`、`_begin_index`|y，随read|恢复真实状态；局部导数保持索引与阶数分支固定|
|CFG缓存|`WC_FIELDS`中的两个分支与全部工作状态|cache，随write|包括residual/probe窗口、previous input/internal/output、累积漂移、resume、counter和嵌入字段；C也有转移|
|读出器来源|原`PolicyOwner.readout.calibrators`的真实D anchors及工作计数|cache，随write|来源step及对应原sigma一起记录；不只移植特征值|
|执行器/owner|原selector/readout/executor的completed/history/last/健康状态|cache，随write|保留诊断状态来源，future仍执行相同硬计划；当前read标签由四格单独记录|
|模型buffer|原net.named_buffers|与对应原完整cache checkpoint一起恢复|参数及安装函数身份不变；生产中需复核可变buffer是否有额外语义|
|输入与随机态|两原条件、noise、Python/NumPy/Torch/请求generator|共享|C/D来自同一pre-write；若两动作的随机转移不一致，当前混合接口拒绝，不假装自然可比|

原WC residual/probe window在最初写入后可能保留三个物理槽；旧读出使用最近两项。不能从“两来源”反推snapshot只需要两个张量。D35附近还有原70-call cycle reset；本轮选第8更新，保持旧reset行为，后续导数实现另行覆盖该离散边界。

## 已实现与仍待验收

`cara_read_write_state_r1.py`直接调用原UniPC的step方程；没有Euler近似、identity Jacobian或历史stop-gradient。它只证明求解器这一组件。合成velocity/cache recurrence的方向有限差分只验证计算接口与符号，不测真实Cosmos误差。

`cara_read_write_suffix_r1.py`是独立的**no_grad机制实验组件**。它使用原PolicyOwner、原WC/RF与原后缀循环，在同一父状态支付一次C和一次D，并恢复四种完整后状态。每个后缀结束后恢复同一个父状态；失败保留异常，实例拒绝再次run。它不承担加载、资源准入、账本、解码/编码、评分或GPU终验，因此不能由本地通过直接宣布整卡可启动。

快照使用既有CPU-owned存储图，不先做GPU deepcopy。保存三份image的总CPU存储有显式上限。混合状态物化可能有额外GPU峰值；**48GB实测峰值与完整资源报价尚未接受**。不能把tiny CPU占用按比例宣布生产显存足够。

首个集成检查在原WC/RF/UniPC函数体和原28个Block类上执行；小权重、attention、patch embedding、head、条件输入和CPU依赖namespace是明确替身。Linux真实模块导入/注册、真实参数与完整pipeline保留独立验收。原始本地失败回执保留，不把环境接线失败说成方法失败。

## 近期完成顺序

1. 本地M0求解器VJP与M1四格组件，通过独立C/D参考和父路径恢复检查。
2. 两卡GPU隐藏的受影响Linux CPU验证；复用未变的原采样/存储/控制组件，不重新造整个评测系统。
3. 补齐真实模型状态清单、快照物化峰值/磁盘费用、唯一入口和8后缀完整GPU卡报价；参考原件逐一确认，不能只引用旧均值。
4. 先完成M1真实机制pilot。完整模型输入VJP/warp/LPIPS可并行准备，M1不为等待昂贵全轨迹反向而阻塞。
5. 若写入作用可辨识，推进同伴随read-only对full的M2；若微小但一致则做小型确认，不先扩大预算/模型矩阵。

本轮只在本地运行CPU；未访问四卡、未写账本、未新派GPU。后续按现行两卡限制、完整报价、原账本权限及GPUh阈值推进。
