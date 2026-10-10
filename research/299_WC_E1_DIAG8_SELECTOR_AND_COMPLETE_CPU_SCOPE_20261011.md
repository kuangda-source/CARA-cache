# E1固定8路径选择适配与受影响CPU范围

2026-10-11。沿用[298冷启动/短前序预登记](298_WC_E1_COLD_PREFIX_MEMORY_DIAG8_PREREGISTRATION_20261011.md)。两个存储实现、四模型进程、8实际GPU路径及2.044575084 GPUh完整forecast保持。当前新增选择与观察源码，未声称实际GPU通过。

## 适配边界

复用原完整guarded UniPC pipeline、真实current-birth owner/控制/读出与CPU-owned存储。独立适配仅将原四请求/八方法循环替换为已经登记的每arm一请求一方法或两请求三方法；用逆向原字节和AST检查限制变更位置。保护首七/最后步骤、四physical checkpoint、额外owner roundtrip、条件、solver/RNG、原完整MLP行工作与语义检查保持。

参考verifier只调整计划路径/请求/方法计数，保持working-age与current-birth语义检查，未用虚构或复制行填充原32范围。每arm以固定名称/方法/次序检查，不接受任意减少请求。原365 CPU载荷只读复制，新模块和入口独立绑定。

物理gate前、额外snapshot之前/恢复释放之后只保存标量库存及CUDA内存元数据；不在observer中保存owner或Tensor引用，不改RNG/部署/算术，不插入empty_cache。该实现需要实际CPU执行核对，不凭syntax推断数值等价。

## 新CPU完整范围

flow OFF/ON均执行全部四arm/八路径，共16成功CPU路径；两prefix arm另做最后目标writer失败，两flow共12尝试路径/四故障，合计1008完整更新/2016CFG。重新读取成功路径576 guided/16 final；72状态变异、12arm变异和8实际文件截断拒绝；计划336观察事件。

每条完整路径与末writer失败都核对四physical/额外state恢复、模块/buffer/参数和钩子清理。原/新存储的36 guided、solver返回、动作、final、条件、RNG与视频mock哈希逐项核对；冷启动/短前序目标也作同等核对。

CPU继续使用已验收的Toy权重/attention/prepare/JSON视频writer与固定真实UniPC/WC/RF源码。四arm在同一Toy测试模型上运行并恢复初始状态，不能把该CPU事实称作真实四模型冷启动或GPU容量修复。真实GPU卡仍须四独立子进程和完整计费。

## 接续

先将原365与新源/登记复制到新CPU目录，执行上述完整受影响范围，再从原PID/日志/向量原件独立复核；失败保留整范围及原源，不改在跑stage。通过后完成实际生产输入/资产验证、唯一GPU监督和完整原件审计；本轮单次≤8权限保持，不能复用原64卡授权做静默重投。E2完整76的具体>8批准仍待，研究目标保持active，不因一张卡等待而停止E1准备。
