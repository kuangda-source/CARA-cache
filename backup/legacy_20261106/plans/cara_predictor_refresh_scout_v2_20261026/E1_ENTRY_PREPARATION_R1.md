# E1入口准备 R1：同状态读出与CPU证据边界

2026-10-26。继承V2.2；原登记和DEV128保持不变。本轮为下一阶段实现准备，不授予GPU执行。

## 已实现

独立模块 `src/wcomr/scout_readout_v22.py` 不安装sampler hook、不派发、不更新锚点。WC-C复用已接受的源码精确skip编译；A复用原beta1及最终输出混合。FULL/R4/DCTA产生prewarp residual后走同一warp/head/unpatchify/RF，并保留每个组件的未混合输出。DCTA采用已审计Wan读出的[1,2]裁剪，零/非有限分母显式unsupported，不暗加epsilon；这些异常仍占原登记分母。

**此次明确common-adapter输出身份**：主比较中所有非C候选同用alpha(t<25)=1、其余0.5，在RF分支输出之后相对C混合。DCTA主比较因此是“Wan DCTA component + CARA common phase adapter”，不是完整DiCache，也不是未经混合的官方读出；未混合的两个分支输出另存用于转换路径诊断。不得比较完后在raw与phase间择优。原A调度未变。

只接受当前Shared25-C父fingerprint、12状态中的合法步及其最近两真D身份、正h/H、相同请求/模型/CFG分支。候选输入私有拷贝；known WC cache、scheduler、buffers、module modes与Python/NumPy/Torch RNG回滚。拷贝前检查显式logical-copy cap；该cap不代表设备峰值。没有保证未知自定义字段/任意网络突变可回滚，权重版本突变直接失败。

固定局部gradient实现：实际BCTHW guided velocity，H/W前向差分，仅合法边，总元素数加权FP64平方和；能量比使用1e-12、常量teacher单独标记，不构成质量门。没有FFT、在线特征或额外网络。

## 本次CPU接受的范围

[最终本地CPU回执](../../reports/cara_scout_readout_CPU_v22_r3_20261026.json)：11项测试。六个预定步、flow OFF/ON下A与旧入口逐项相等；条件帧RF处理、R4-long短龄回退、DCTA裁剪/缺支持、非有限与训练模式拒绝、预算前置、正反序一致、失败回滚均通过。使用实际固定WC/RF源码和实际warp函数，但head/特征是明确的小张量fixture。

R1九项/R2十项回执保留作开发历史，最终source绑定以R3为准。**不是**真实权重、Shared25-C完整自由运行采集、冻结请求类全入口、双服务器或整卡CPU接受。不能将11个测试等同于上份清单C01–C11全部完成。

下一步需把当前状态的o/p/embedding/condition及两锚点接到真实Shared25-C owner，补充严格sigma hook映射、P0 dense/P1 native replay/P2 conversion与父轨迹ON/OFF完整控制。必须保存实际branch p/r/solver/RNG；1624不能替代。适配器两个分支隔离、拒绝/缺失分母、原始账单/退出与存储故障还需真实组合验收。

## 双端和费用准备

[资源草案](../../manifests/cara_scout_E1_resource_draft_v22_20261026.json)明确区分逻辑候选与实际head调用：当前每状态C执行一对head，其余五角色各执行C+proposal两对，共11对；12状态为132对/264次head，尚不含teacher和额外控制。R4-long的短龄同值不能随意删除登记位置；若工程去重，物理调用/别名费用另冻结。

以示例hidden `1×24×27×48×2048 FP32`计，每份243MiB。两输入按锚点p/r仅存一次、每个目标保存o/p/teacher hidden，隐藏特征就约26.58GiB，未含guided输出、solver/condition、日志。64GiB输出卷仅为待验证规划，没有创建。不得再用“多存一份约242MiB”当整卡存储或峰值显存上限。

两条Shared25-C父请求在旧A6000记录中合计约494秒；加两条父轨迹无干扰控制约987秒。这只是父请求历史参照，模型加载、teacher、候选、拷贝/哈希/落盘、预热、清理全未计入，**不能据此给完整GPUh报价**。双端forecast与hard_limit暂为null，原约1GPUh只作目标。四卡默认/两卡备用、累计226、部署min(257.7712338712067,.8freshNative)、旧16.5责任和DEV128预约保持不变。

## E0补充已完成

旧四个CAL Native35视频从已接受CAL66原件只读取回，共3.25MB，逐SHA一致；仅小文件读取，未启动远端模型/评分，未读DEV128。原S25-C/A八视频复用。固定一次[1,2,1]/4可分离轻模糊，在任何新诊断输出前写入脚本；所有角色裁同一像素边界，未按prompt拟合模糊强度。

见[完整诊断](../../reports/cara_CAL66_native_gradient_fixed_blur_20261026.json)：12视频1116帧，本地CPU约4.7秒、峰值约211MiB。四输入A的Native-relative梯度MSE较C降低24.23%–36.34%；固定blur-C也降低3.41%–27.32%，A在其中3/4输入低于blur-C。能量下降和误差下降可以同时发生；既不能据此证明“质量更好”，也不能断言“A只是模糊”。未重新评分blur-C的MUSIQ/LPIPS，原质量门及原结果保持。该诊断不改变E1状态/候选/阈值，不能替代自由运行终点确认。
