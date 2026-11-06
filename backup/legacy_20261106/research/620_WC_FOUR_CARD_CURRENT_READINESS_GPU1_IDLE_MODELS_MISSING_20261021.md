# 四卡当前运行条件：GPU1空闲，模型和新机验证仍待完成

2026年10月21日12:00:46北京时间仅一次只读复查。四卡可继续准备，尚不能直接派发BANK24或完整1624采集卡。

| 条件 | 当前证据 |
| --- | --- |
| GPU | GPU1为23MiB、0%且无compute进程；其余三卡有任务。未预留GPU1。 |
| 数据盘 | 本人工作区所在数据盘可用415.260GiB。 |
| 已装环境 | env-r3存在；实际METADATA为Torch2.7.1+cu128、TorchVision0.22.1+cu128、cosmos-oss/cosmos-cuda1.4.0、decord0.6.0。 |
| 组件验证 | 已保存的29项依赖/请求/CPU编解码组件接受保持。完整推理和新机生产CPU尚未接受。 |
| 模型 | 本人准备的工作区HF缓存和本人默认HF hub均无模型目录；未扫描他人目录，不宣称全服务器无模型。 |
| 代码 | 当前工作区project仍为c9a2f95b；后续在独立新stage应用已发布GitHub增量，原部署和原件保留。 |
| 预算 | 此project无gpu-budget-v2.json；新机共同权威账本/逐UUID准入尚未接通。没有据旧余额准入。 |

当前最先需要准备完整固定模型资产及SHA。完整推理此前在Cosmos-Guardrail1固定revision缺失处停止；本地代理能够访问元数据，但此前实际文件下载返回401/GatedRepo。此次未重复认证探测、下载权重或加载模型。可用来源仍是已获权限的下载，或原双卡恢复后复制已授权的固定缓存并核对SHA，认证文件不转运。

模型完成后需要独立验证实际CUDA/驱动与扩展兼容、在新stage完成这两个scope各自的真实生产CPU、核对新硬件完整报价和共同账本/锁，再按原BANK24→完整1624顺序进入实际准入。旧两卡CPU通过和具体整卡12GPUh批准均保留身份；本次没有迁移或派发原实验。

两卡worldcache-bank24原12:37恢复检查保持。此次只读复查没有新增GPU、CUDA初始化、权重加载、训练或账本写入，也不创建四卡周期巡检。

原件：

- [12:00实际只读捕获](../reports/wc_four_card_human_current_readiness_20261021_120045.json)
- [当前运行条件核对](../reports/wc_four_card_current_readiness_assessment_20261021_1200.json)
- [已接受依赖组件](../reports/wc_four_card_dependency_repair_components_independent_acceptance_20261021.json)
