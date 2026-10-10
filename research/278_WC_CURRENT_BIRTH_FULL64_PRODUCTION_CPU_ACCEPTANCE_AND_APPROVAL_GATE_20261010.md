# 完整64生产CPU验收与具体执行确认

2026-10-10。完整64方法卡的实际服务器生产CPU已通过并独立验收。当前创建目标完整256、实测输入与实际生产入口均已完成；下一步可以进入已冻结完整64真实生成，须先获得本卡严格超过4GPUh的直接授权。

生产源dd449bb4fba6e24f3dac59ccdbf366afe6fb28bc，620载荷，配置SHA为1edd9ebe9ba91045f980e81fde5273cf03098012a9156bf72100d9be403e2ada。原监督4008483／子4008485均已退出0，实际CPU61.942259秒。独立回读核对原Git源码、嵌入driver、完整配置和参数绑定b56abae2f61638305041437214e23afce56f5715ed05b9aa78e8e36960695f44；预算前后SHA不变，GPU0、CUDA未初始化。

四原请求、16组实测参数、真实安装的原forward、guardrail资产／Blocklist、兼容接口身份与两种规则缺guardrail入口拒绝通过；32个具体范围／参数／请求变异全部拒绝。这里是安装环境与接口验证，没有初始化生成器、执行真实视频或评估P寿命。

待确认卡为**WC-CURRENT-BIRTH-CAPD-FULL64-R1-20261010-A**：两工作周期×四已有CAL seed0×八方法，共64完整路径；2304更新、4608CFG调用，最多64视频、64最终latent及2304 guided。方法为SOURCE_RA、DYNAMIC_NO_P、CPD、REF_CPD、A_CPD_OFF、A_CPD_W1_ONE_PHASE、A_CPD_BETA1_ONE_PHASE、DENSE_CONTROL。全部原RA／无P／OFF／完整Linear参考／dense控制保持，不删除没有P动作或失败的路径。

沿用768×432、93帧、16fps、请求35步而实际36更新／72CFG、四原seed0与固定条件。阶段A early1／late0.5、边界25；P只使用四层4／10／16／22、旋转50%部分MLP、maxP2，创建正floor与未来借用D漂移TRANSFER保持。没有新强度／阈值搜索、训练或额外教师。

完整GPU终态后执行全部原件CPU审计；只在新路径的输入、条件、求解器和保护前缀兼容时复用已接受四Native，全部可配对视频按既有离线CPU LPIPS协议评估93帧，未配对和失败保留分母。完整方法比较的重点是阶段修正与部分刷新的闭环交互、两来源规则、P位置／次数与实际总成本。旧32可作匹配质量参照；跨批记录时间不作clean速度比较，四曝光CAL不是独立确认或物理质量结论。

整卡保守预测**8.32817561558863GPUh**，计入既有新增48窗口。现场累计37.676066656027565／77.89524658965853，余40.21917993363096GPUh。当前未选新GPU、未预留预算、未提交新GPU；旧32卡批准已经执行完毕，不覆盖本卡。此次确认仅由用户“单次严格超过4GPUh才确认”的直接规则触发，不拆／缩矩阵规避。

原完整32结果仍为四CAL阶段W1／β1均改善、平均LPIPS相对WC下降10.7725%／11.1600%；旧负例保持。当前P整组只省约1.29342%是实测条件事实，新64将回答组合与缓存来源能否把单次更新能力转化为更好的完整生成；不能提前把CPU通过当收益。

证据：[生产CPU独立原件](../reports/wc_current_birth_full64_production_cpu_r1_terminal_20261010_capture.json)、[具体配置](../configs/wc_current_birth_full64_production_r1_20261010.json)、[完整卡登记](../manifests/wc_current_birth_full64_r1_preregistration_20261010.json)、[276完整256验收](276_WC_CURRENT_BIRTH_FULL256_CPU_ACCEPTANCE_20261010.md)、[257已有终点结果](257_WC_RA_PLUS_A_COMPLETE32_FIDELITY_AND_COST_RESULTS_20261010.md)。

组会飞书同步已独立回读通过：revision61→62，197顶层块只改进度段，其余196块保持。首次PUT网络EOF、随后一次fetch EOF均保存；回读确认首次没有提交，再对同一段进行一次重试并全量验证。只给CLI子进程设置传输参数，未改全局网络或更新CLI，没有发送消息。见[飞书同步原件](../reports/wc_current_birth_full64_production_cpu_pass_feishu_r3_20261010_verification.json)。
