# N07整卡合同与已批准大卡准入：CPU准备完成

**最终共同测试的整卡范围、原输入、工作点、CPU证据与预算授权现在有统一绑定接口；既有数值执行证据可复用，不需要再跑整套Toy矩阵。** 本轮完成12项CPU控制与99份既有执行依赖SHA核对，没有选择最终测试卡或改动服务器。

## 1. 复用现有数值执行证据

从`frozen_shared_execution_r1.py`递归追踪本地Python依赖，实际核对99份文件，与475完整952 CPU原结果绑定的源SHA全部一致。新输入/质量/记账辅助代码没有改动这些数值依赖。runtime派生的WC/RF与原模型源仍由真实生产验证单独按SHA核对。

原件：`reports/wc_paper_N07_numeric99_dependencies_reuse_CPU_20261016.json`。这里是明确的源码依赖复用检查，不是第二次952采样、真实模型接受或速度/质量结果。若实际执行依赖发生变化，该接口会拒绝沿用旧证据，后续只补受影响数值验证。

## 2. 新增整卡生产合同

`src/wcomr/frozen_shared_production_r1.py`准备以下接口：

- 绑定474的确定性选择、480的原始字节/参数、全16案例/十方法/160正式＋20完整warm/180位置；保留前密C/A、Native参考与选定WC/RA，既有A/H1版本冻结。
- 逐一构造160个实际参数字典；只有真实Cosmos `InferenceArguments`回读保持原参数后，未来生产CPU才可接受。本轮相关单测使用声明的假参数类，不冒充实际Cosmos。
- 整卡费用和原预算窗口必须明确；CPU可以先准备一张>=12卡以便交付具体审查，不能为了旧小卡接口而删方法/拆分。
- 正式启动绑定同一source、config SHA、完整CPU回执、输入fingerprint、UUID、launch ID、全部scope与整体费用；严格<12沿用既有自主规则，>=12必须具体整卡批准。
- 旧N05物理检查仅用来复用未改的checkpoint、参数、runtime及旧控制原件，不转用旧卡的执行许可或四CAL科学范围。

当前尚无真实N07配置，运行脚本/实际生产CPU、最终方法/输入/价格均待N05后冻结。新增模块是生产校验与输入构造核心，不宣称完整运行入口已执行或GPU可立即启动。

## 3. 修正未来大卡的记账能力缺口

实际源码发现：现有`BudgetPool.reserve`固定拒绝任何`billed_limit_GPUh>=12`。这适用于自主小卡，但在用户具体批准一张更大整卡后仍会拒绝准入。

新增独立`ApprovedCardBudgetPool.reserve_specific_whole_card`处理这种已获具体批准的大卡。原`gpu_budget_pool_v2.py`未改，当前服务器N05源码、池文件和reservation均不触碰。

新入口读取绑定SHA的具体批准文件，逐项匹配整卡source/config/CPU/输入/范围、UUID、launch ID与预测/计费上限；standing under12规则不能授权大卡。仍使用同一v2短事务、逐UUID约束与加法结算；全额预留，余额不足拒绝，原cap/origin不能由批准文件重置。最终actual按原v2一次结算，原任务记录保持。

这只是技术能力准备。本轮没有真实大卡批准、授权文件、预算修改或资源预留。临时测试中使用的13/14GPUh和cap100等均为标明synthetic的假账本数值，不是科研预算或未来N07报价。

## 4. CPU控制

`tests/test_frozen_shared_production_r1.py`六项：180完整范围与>=12准备；范围/费用/算法变更拒绝；160参数回读与错seed；嵌套本地依赖追踪；完整source/UUID/CPU/launch权限绑定；12边界需要具体整卡回复。

`tests/test_gpu_budget_approved_card_v2.py`六项：整额预留与实费一次结算；standing许可拒绝大卡；错价格/source/scope拒绝；重复/忙UUID拒绝；真实余额/原预算窗口不能绕过；原under12 reserve保持。

合计12 passed/1.63秒，见`reports/wc_paper_N07_contract_and_approved_pool_CPU_controls_20261016.json`。全部账本/GPU/批准均为临时合成对象；没有调用服务器、nvidia-smi或任何真实GPU操作。

## 5. 后续执行顺序保持

先今天12:05一次接受原N05完整66/source15d77ac/1078249/1078290/post1078250，当前未SSH或读partial。N05/N06后冻结方法→fresh身份排除→八来源确定性选择→原字节/参数绑定→完整运行入口与真实生产CPU→整卡费用/fresh v2/UUID，再按实际完整预算决定自主或询问。

原180模板未选卡，费用未知保持null，原cap104.971363333与既有窗口不变。N08重复clean、N09实际成本、N10真实质量跟随最终实现；F/B关闭，P/T1后排，无新人评、训练或OMR。
