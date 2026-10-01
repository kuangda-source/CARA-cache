# WC-S1：动态导入验收与180秒真实内核门

日期：2026-10-01。状态：CPU_DYNAMIC_IMPORT_R2_PASS；后续真实GPU内核已完成，见[59结果](59_WC_S1_REAL_KERNEL_RESULTS.md)，下文保留事前冻结范围。不是模型、成本profile或质量收益。

## 动态导入与纠错

[CPU probe](../scripts/probe_wc_sparge_import.py)对隔离8文件package逐SHA后，用实际Cosmos Python3.10/Torch2.7.1+cu128导入两扩展与utils，并核对实际module origins/byte SHA和no-PV callable。隐藏GPU、禁止枚举和初始化，加载当前runtime的dense attention源码，不构造模型或执行CUDA/Triton。

R1因同一拒绝函数被赋给多个CUDA API，Torch Dynamo产生duplicate-object rules冲突，TECH_BLOCKED/7.916334秒；CUDA未初始化、PID退出。[原失败回执](../reports/wc_s1_import_r1_20261001.json)和远端原probe文件保留。R2每个API使用独立guard identity，实际导入通过/3.119766秒，Torch ABI=true，两个.so origins/SHA与已编译artifact一致，绑定签名为8个Tensor+3个int+1个float，PV threshold不在参数中。[通过回执](../reports/wc_s1_import_r2_20261001.json)。这确认该环境的动态加载/接口，不证明运行kernel或另一环境ABI。

当前dense来源SHA `9879fc59c62b4b5a958ebaf8588da1402ee48ddfe7df1979ad986d8a56a34d91`。CP1底层attention在Ampere通过Torch SDPA优先Flash backend；GPU门会记录实际aten dispatch，不能只凭源码叫作Flash实测。

## 事前固定的最小GPU范围

[冻结配置](../configs/wc_s1_kernel.json)与[runner](../scripts/run_wc_s1_kernel.py)准备：B1/H16/D128、BF16、N256和N31104、seed0；每个形状dense及no-PV full/约50%/约25%三种QK保留率，1warmup/5repeat。Q/K用随机高斯并做每头RMS归一化，V为随机高斯。31104由真实hidden与checkpoint/config推导，**不是直接捕获的实际模型QKV**。固定cyclic-band mask只测试真实块跳过的硬件和误差行为，不当作合格质量路由。

首轮计时包括validation/finite、NHD-HND packing、quant、LUT、output flatten和同步；同时保存同步wall/CUDA events全部repeat、finite/dtype/shape、相对dense RMSE和包含诊断的peak allocated memory。CPU dispatch profiler单独运行，不把profiler时间当clean时间。full-mask relative RMSE<=0.05是此次预登记技术筛查，不是视频质量容差；两种稀疏率全部保留，即使误差很大也不能删除。

[专用supervisor](../scripts/supervise_wc_s1_kernel.py)复用原`.sync/f1.lock`，fresh GPU UUID/sm86/VRAM<=1024MiB/无compute PID准入，运行中外部冲突仅停止本任务。最多180秒（child170秒+5秒kill余量），在原4GPUh余额内预扣180秒、记录in-flight reservation，终态按含导入/失败/释放墙钟结算退款，禁止扩大到8h或有reservation时重提交。[CPU预算门测试](../tests/test_wc_s1_kernel_budget.py)2项通过，覆盖原余额接受、耗尽/扩大scope/扩大ledger/inflight拒绝。预约状态不是实耗。

余额1255.511794秒足够这一有限技术门，不授权原新4GPUh/clean50。完整准备同步/hash部署/actual validate-only及fresh准入之后才唯一新GPU身份。当前未提交，不用CPU检查宣称真实kernel。

下一：按上述范围实际执行与独立终态审计，比较full-mask量化误差和含路由净时间。固定synthetic mask的误差不用于否定或接受视频方法；full/kernel技术通过后还需真实QKV hook、WC剩余成本profile、数据驱动mask与公平四臂。仍无默认人评/训练/付费评分。
