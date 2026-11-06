# S/Q 受限 CPU 准备 R1

本轮仅使用已接受 B1 的离线资产。双卡 CPU：2 核、cpuset 4/5、8 GiB RAM 与 swap 合计上限、1800 秒、单输出文件 64 MiB、临时目录 2 GiB、nice 10、idle I/O、禁网、隐藏 GPU、旧输出只读。最大分配 1 vCPUh；实际 process CPU 与 wall 单列。无新 GPU、无 ledger/cap 写入。bulk 原件不传本机。

复用 B1 grouped CPU 的镜像/环境/source registration，独立新 stage `cara-sq-cpu-r1-20261028`；存在则只恢复。派发前两端恢复 scope 句柄并重新检查 CPU/RAM/磁盘/容器，日志留原件。新代码先 exact-path 提交同步，stage 绑定 immutable SHA。

S：对原两 FIT、Shared25-C 父轨迹的 12 状态计算 WC_C 的 FP64 C/U/K、直接 guided 恒等式、共同 teacher 分支能量归一化。实际 FP32 guided 舍入与 FP64 几何分列。未来聚合使用 prompt 等权、两个父轨迹各 1/2、统一 g=1；缺少 108 标签中的任何一项即拒绝生成全支持风险/计划。19D 一次交换共有保护 1..7/24/36，max-age=6 继承旧接口；数值历史支持由显式函数提供，纯结构候选不算生产支持。Uniform19 的真实网格和简单对照由主线冻结，此处只提供风险与合法交换接口。

Q：固定 Shared25-C、原 C、原缓存 dtype。每 token 通道 128 一组，FP32 absmax scale、ties-to-even、对称 [-7,7]/[-127,127]、零组 scale=1；INT4 低 nibble 在前、二补码、有符号 -8/-128 不使用。尾通道补零且计 payload。tensor header 64B，scale/payload 各按 64B 对齐；pair header 64B；窗口 alias descriptor 也按 64B 对齐。编码保存的是实际 bytes。I/M × {(8,8),(4,8),(8,4)} 同码率真实 bytes 必须相等；M 在 FP32 变换/回转后 cast 原 dtype，另记 transform roundtrip。

Q0 对 B1 十对独立真实锚点编码、解码并记录 raw 误差/CPU 时间；不按 raw teacher 误差选择方向。Q1 的 leave-one-prompt 全局方向选择器只接受实际 C post-RF 输出，拒绝 raw 评分及不等 bytes。小张量接线使用原 SHA 固定 C/warp/RF 与明确的 toy head，覆盖 flow OFF/ON、全部六 codec、输入/状态恢复；不是实际 Cosmos 权重重放。

源发现：WorldCache 的 `len(window)<=2: append` 会使持久窗口保留 3 项，之后仅滚动最后两项。实际 C 用后两项，但滞留首项和 probe 窗口仍占缓存。B1 的两锚点可重建 source-bound C 读出视图，不能完整恢复线上持久窗口/别名/solver 分母。不得把 corpus 压缩率称为总显存比例；原 raw 只作离线 teacher。当前不会安装 codec 到生产入口。

下一张 GPU 卡仍须完整受影响 CPU/范围/双端报价与授权。S 覆盖缺失才准备 A-SQ-FAST；Q25 已有局部 raw 足以 Q0，若要 Q1，可先报价复用这些 12 状态的同窗口真实 C 重放，不默认加 Q25 新采集；部署内存字段的新增采集须先写明确修订。
