# E1启动合同遗漏：原失败与R2修复

2026-10-11。当前active，继续完整8范围；这是打包／验证覆盖问题，不是显存假设或WorldCache方向负结果。

**R1第一臂加载121.563931秒后，因独立目录未包含 `manifests/wc_h0_eval_mode_contract_20261003.json` 退出。没有开始采样，没有新tensor或视频。** 原模式合同存在于不可变full64来源目录，SHA a990ad5c078519bc7f284139fbd3afb72b0492f60de7ebc1e327927d613fcabd。新398来源没有打包它；旧CPU覆盖guardrail-less入口，但没有触及只在模型加载后执行的读取。

[原终态及独立费用核对](../reports/wc_e1_diag8_gpu_r1_terminal_20261011_capture.json)：监督4048795／runner4048882／后CPU4048796及子4049534均退出消失，第一模型进程exit1、其他三进程未开始；原4臂／8计划槽保留、完整numeric0、文件0。后CPU成功完成的是全部缺失槽的审计，不能称方法或容量验证成功。

实际wall182.837132650秒、0.050788092403 GPUh全部计费；累计39.234595839949／77.895246589659、新48余38.660650749709、76历史提交，GPU24MiB／无compute、锁已释放。原目录、源、partial记录与失败均只读，不追认成功或在原目录补文件重投。

## 修复与下一张完整卡

R2使用独立card／run／目录，保留原四臂8路径、两请求seed0、KEEP_INTERVAL、所有八方法的原参数、35实际36更新／CFG／physical与workspace/prefix reserve、forecast2.044575084 GPUh。普通采样／controller／readout／额外CPU存储checkpoint体全部不变。

把原合同和已有native meta模式脚本作为显式required startup assets纳入payload；在加载前验证文件存在／hash／拓扑身份。实际CPU加入各文件缺失／改变四拒绝，并使用原类meta构造2059174912参数拓扑、1173模块与共享eval0训练状态；不加载权重、不运行forward/CUDA。受影响实际生产CPU与独立原件通过后fresh≤8自主启动完整8，不需重复请批，不删对照或缩scope。

E2待执行入口存在同类stage合同遗漏，原ready声明需补覆盖；当前缺具体>8批准，GPU0。先在本地dispatcher加required asset准入，再独立登记其打包／实际CPU修订；原76范围及9.869732459 forecast不变，不重复发同一问题，不新增训练或人评。

一次只读捕获初版错误地假设旧继承计划字节都等于启动HEAD，已保留失败原件和[捕获失败记录](../reports/wc_e1_diag8_gpu_r1_capture_protocol_r1_failure_20261011.json)；修订捕获比对启动时提交的完整静态配置及服务器每个staged SHA，selected只允许三个动态字段差异。该观察协议失败无GPU提交或额外费用，原GPU失败及所有历史字节保持。
