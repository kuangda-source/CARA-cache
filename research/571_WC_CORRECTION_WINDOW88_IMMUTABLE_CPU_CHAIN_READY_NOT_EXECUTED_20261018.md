# 连续修正完整88数值CPU执行链准备完成

2026-10-18。**下一轮区分实验已有可执行的独立CPU链：固定第21步删除D，检验后续22／23继续修正的增量。** 当前适配器／完整88入口已准备、本地12项已通过，服务器真实88尚未执行，也没有新视频结果。

原[完整24四臂](../plans/WC_DROP1_CORRECTION_WINDOW_FULL24_20261018.md)和[静态范围](../manifests/wc_drop1_correction_window_full24_static_scope_20261018.json)保持：16正式＋8warm、864pairs；25D三种读出C／A1／A3及原26D对照。不会同时搜索删除位置、alpha或beta。

## 准备的执行和验收

- [CPU派发器](../scripts/wc_drop1_window88_cpu_r1.py)只复制原N12不可变source `e76b4f8` 注册payload，基准注册SHA `2532bde9cc5ba858ac3018f3bbe82e88be2e459b8e5e985734c78659f42bc134`；向新的CPU-only stage增加已提交新文件，禁止覆盖任何继承的数值源码。
- 第一命令完整执行两flow×四CAL×四方法×audit／lean的64条路径和24条原三臂audit控制，共88×36更新。随后执行8项新合同／格式及4项原回归。GPU和权重加载禁止、运行时SHA、真实导入源码、所有者回收、C/A不写真D等保护沿用原模板。
- [一次查收和离线验收器](../scripts/capture_wc_drop1_window88_cpu_r1.py)绑定原PID/start、source／注册／全部payload／运行时；完整88、两flow各44、四输入四方法、真实配额及原36guided等价缺一不可。全部三命令通过才接受数值CPU。失败和原日志保存，不自动重派。
- [本地源与时间门槛](../reports/wc_drop1_window88_source_and_collection_gates_local_20261018.json)检查远程脚本AST、两个边界及五种不合规输入；无SSH、模型、数值88或GPU执行。它补充原[12项适配器控制](../reports/wc_drop1_correction_window24_adapter_full88_entry_local_CPU_r2_20261018.json)，不替代真实数值检查。

## 顺序与剩余

[执行顺序补充](../plans/WC_DROP1_WINDOW88_CPU_RESOURCE_WAIT_ORDER_20261018.md)已在实际运行前登记：原N09未准入、0GPU在途时，N10原完整CPU终态查收后可以先执行完整88数值CPU。原完整40的实际GPU测量仍优先于新的24卡，不并发重CPU影响测量。

数值CPU预计8–12分钟，仅用于安排一次6分钟技术半程及不早于12分钟的完整查收。当前仍未派发；实际source和时刻必须来自下一份launch，不借本文件宣称在途。

完整24真实生产入口、旧12端点／四预热控制、完整报价和GPU准入尚待。88通过也不能冒充生产CPU或终点收益，A3质量／时间保持空。N12原三臂已接受结果不改。累计cap226及全部历史费用不变，新增GPUh=0；F/B关闭，无训练／人评／OMR。
