# 829 — M1入口、完整评分CPU、私有卷与冻结源码准备完成

本轮将读写价值框架推进到完整M1的执行准备。科学问题是：一次刷新改变当前读出与缓存状态时，分别如何影响最终视频？这为下一步价值规则与read-only消融提供可解释的机制起点。

## 完成的证据

- [入口Linux接受](../reports/cara_read_write_entry_Linux_CPU_accepted_r1_20261101.json)：原容器exited/0，实际工作186.095秒；67项入口/临时账本/完整工件/评分/恢复控制、28条加载模型tiny请求和8对93帧真实Alex/PIQ评分通过。另一个损坏合成夹具保留8分母、1完成行。所有媒体为显式合成CPU样本，没有读旧实验视频或生成模型权重。
- 原启动传输超时后，仅capture恢复原容器；注册SHA、真实源码/参数类与原退出证明闭合，未重派。CPU记录的短Git ref已解析为`b930df4b04a0924d8bea0af32c0f7aaf8c33a5c8`。
- [组合CPU准备](../reports/cara_read_write_whole_CPU_accepted_r1_20261101.json)：复用828已接受的不变数值组件和原guardian/supervisor/单一账单源码。M1新绑定及实际八对评分路径单独接受；真实GPU生命周期未在本CPU卡中伪造为已执行。
- [私有卷接受](../reports/cara_read_write_storage_accepted_r1_20261101.json)：16GiB全分配ext4、48MiB跨盘预留journal，1MiB持久写入/回读SHA正确。原PID/start ticks已退出，输出为空、journal全零。
- [源码安装](../reports/cara_read_write_source_preparation_r1_20261101.json)：1307份原注册文件及runtime完整核对，唯一M1 GPU stage安装完成，注册SHA `2def9cdcb04c20b96977c6f82ad728cebf42e67907048a650238d2ba9f9bbd5e`。服务器确认无GPU authority、intent、launch和容器。

实际镜像位于数据盘，home保存独立journal。创建后数据盘约788GiB可用；先前home约62GiB观察不能用来判断数据盘是否能分配64GiB。16GiB是本卡14输出范围与余量设计，不以删旧结果换空间。

## 固定完整M1

两个旧FIT、seed0、第8更新；八个四格科学输出、四独立等价控制、两新Native。每科学请求执行原完整guarded pipeline，并支付同父C/D后选择读与写，原求解器自然维护全部UniPC历史。完整14请求/504更新/512paired/1024CFG，没有部分分数挑位置。

[完整执行卡](../plans/cara_next_stage_20261101/read_write/M1_FULL14_EXECUTION_REVIEW_R3.md)与[最终准备报价](../plans/cara_next_stage_20261101/read_write/M1_FULL14_WHOLE_QUOTE_R3.json)：预计1.6047625015GPUh、硬1.95GPUh；包含600秒未实测快照开销估计和600秒停止释放余量。时间只作诊断，所有额外当前C/D均计入。

## 尚待及后续

原小于2GPUh自主规则有效。用户现已回复“允许本卡原账本读取、预约与结算”，原四卡实验维护限制保持。唯一launch为`7949388215944eb98c7f64f21e8e1dd1`。原账本cap226、旧16.5责任、可用15.4601GPUh已读取核验；新卡尚未预约或派发。新卡的live资产、设备/独占/内存/磁盘与中央余额仍须在派发时通过fresh门。

唯一下一GPU只在两卡原A6000执行。实际启动后按actual start安排半程/终验；原GPU正常或失败终态都唯一结算全段实耗。完整14成功且释放/结算后，才跑原一次四等价控制与八对评分。最后报告逐输入、等权均值与93帧read/write/interaction曲线；M1不以合成CPU结果建立方法收益，不自动下一GPU。

保持A32/B36/S/Q/搜索/E1原接受、赢家、旧CAL范围及WC/RA FIT UNMATCHED；最终16/备用16未访问。原61科学行、54术语条目不新增结果。
