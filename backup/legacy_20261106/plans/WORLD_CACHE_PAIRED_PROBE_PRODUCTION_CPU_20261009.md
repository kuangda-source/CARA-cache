# H-T54：成对probe真实模块命名空间与观察入口CPU验证

2026-10-09，承接H-T50完整Toy CPU和H-T53标签对齐。H-T52 Common仍使用原95源／原三个句柄，完整范围不改；此卡只有独立CPU，不选择或执行新GPU，不使用当前Common未完成教师或评分。

## 先修复真实集成的两个问题

H-T50调用编译函数体，原采样器在`net.forward`上的日志包装不会执行，RF的Toy公用namespace也不能被默认当作实际模块namespace。新独立生产编译器使用实际导入的WC／RF各自全局对象，检查函数体原文件、原SHA和全部实际LOAD_GLOBAL对象绑定；不改上游源码。增加明确net输入／输出观察入口。生产executor要求net.forward和model.denoise是原方法绑定，拒绝属性包装，不能让观察记录被静默绕过。

## 完整CPU范围

现有生产venv、CUDA空／下载和Triton执行被拒绝，导入实际WC／RF模块及其全局对象；模型权重、attention、条件构造和采样父仍声明为Toy。原flow OFF／ON各22更新建立缓存、计数44，保留CC／DD×两重复×两flow＝8主比较、2初始化保护、原8失败控制与两个源契约行。

所有8主比较保留原FP32输出／guided、完整WC和buffer、输入条件／RNG／计数／浅深次数一致；另外原顺序与成对顺序明确观察均须记录每侧一个输入和输出，并按分支比较输入／输出摘要。成对有效路径事件顺序为beforeC→beforeU→afterC→afterU，原顺序beforeC→afterC→beforeU→afterU；不能要求中间缓存总状态或事件时序相同，更不能把差异删掉。

新增四类失败×两flow＝8拒绝：net.forward属性包装、model.denoise属性包装、观察入口在第二侧before抛错、第一侧after抛错。加原8类，共16失败控制，全都poison并拒绝继续、弃用整个CPU副本。观察失败不声称任意模型完整回滚。没有输出或记录的成功子集验收。

## 成本和结果边界

显式观察含哈希开销，CPU耗时不得换算2B速度。当前CPU只能验证实际命名空间及声明Toy上的观察／函数一致性，不能证明真实2B、显存或全36步一致性；实际成对接口和干净延迟需另用同动作、完整父／尾部以及观察开／关的对照。这里不拟合rho／传播先验、不运行RA控制或Head、不声称算法创新／质量／独立CONF。

代码／登记先提交推送，再独立CPU目录实际执行和原件核对。保留全部范围、失败、源码与预算字节；如果原Common在此期间正常结算，账本变化如实记录，CPU不写它、不把合法结算当CPU失败。真实GPU整卡的完整预测／CPU准入另准备，≤2GPUh自主、>2GPUh具体确认和累计50h保持。不扩大训练／稀疏／OMR／DRE／人评。

## R1失败保留与R2导入兼容

R1 source ce0cec4在原RF导入链的Qwen FlashAttention可用性断言停止，61.894640秒，新GPU0、CUDA未初始化，原件与全部范围保留。实际只读核对已安装2.6.3+cu128.torch27；Transformers辅助函数因CUDA不可用返回false，不是缺包，也尚未进入8个pair比较。

R2只复用此前已经审计的实际Video2World条件类CPU导入适配：在这个退出的CPU子进程里按已安装版本允许辅助模块导入，给未用构造默认值提供ordinal0；不改CUDA硬件可用性、不创建context、不加载权重，恢复原HF helper和current_device后才执行Toy测试。实际WC／RF命名空间绑定、8主／2初始化／16失败／2源行全保持；原R1目录、记录和失败不改。这是导入适配，不能声称CPU执行了FlashAttention或真实模型。
