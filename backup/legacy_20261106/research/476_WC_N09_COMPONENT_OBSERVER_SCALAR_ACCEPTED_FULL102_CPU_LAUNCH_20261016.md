# N09部署成本记录器：标量控制接受，完整102 CPU已派发

更新：2026-10-16，北京时间。本轮继续主线部署证据准备，不读取服务器N05科学进度。

**逐请求显存峰值与组件计时接口已经实现，六项标量CPU控制通过。** 新隔离CPU对照正在验证该记录器在全部17个已有执行配置中的数值与生命周期等价；实际GPU峰值、组件费用和最小部署标定费尚未测量。

## 实现范围

- 每请求绑定显式可见CUDA设备；模型驻留后同步并reset peak，结束后记录该请求的allocated/reserved/peak。CPU不可用字段保持null，不写零冒充显存结果。
- shallow/deep blocks、head、solver、VAE、输入准备、写盘、安装、实际policy入口、可用修正warp/转换和边界GC分别记录。输入准备为包含条件处理的整体，不冒充纯文本编码费用。
- CUDA事件在当前显式stream记录，只在请求边界同步、最后统一读取。嵌套区间为inclusive，不能相加冒充总时间或纯kernel费用；多stream未归属部分保留。
- 不复制/保存参数或返回张量，不改动作合法集与任何算法计算；动态控制器/读出恢复条目仅留弱引用，避免记录器自己阻止GC/owner释放。
- profiling结果单列，不进入N08 clean计时均值。本接口没有宣称已测同状态、双probe之后的C/A/P0/D动作价格，该项继续待实际边界接线与费用冻结。

## 已接受的标量控制

原样返回对象与恢复原方法；嵌套异常保持；短命owner可回收；静态namespace与动态弱引用限制；声明的fake CUDA两请求峰值reset/事件结束后读取；单次使用/显式设备。六项通过，`reports/wc_deployment_profile_scalar_CPU_controls_20261016.json`绑定完整源码SHA。fake CUDA用于校验记账接线，不是真实GPU测量。

## 原完整CPU任务

source `65f91ee431af9d208a3ab61fd5a35eda161dd200`，原PID10329，06:17:30.298712单次启动确认live；封存目录`.sync/wc-paper-deployment-profile-full102-local-cpu-r1-20261016/source`。

完整范围：两flow×17已有配置×原audit/profile audit/profile lean三模式，102路径/3516pairs/7032CFG；34组逐步guided对照与34组profile audit/lean终态/actions/Ahistory/sourcehistory/mock对照，68个profile，全部owner释放。仅第一个Toy请求、seed17，不选真实最终测试输入，不再次运行完整952验证。

预计1—3分钟，最早06:20:30.298712，**06:21一次本地查收**。原launch：`reports/wc_deployment_profile_full102_local_CPU_R1_launch_20261016.json`。到时运行新accept脚本捕获一次，再只离线重算完整矩阵、逐步SHA、68个标量profile区间与102 mock；原失败保留，未结束则另约一次。不连续监听。

所有Toy attention/weights/head/prepare/decode/writer与Native dense-WC stand-in边界保持。CPU通过不当作真实视频、CUDA费用或加速结果；GPU后续须绑定最终实现、完整scope、生产CPU和费用。没有扩大N05原66路径或预算。

## 当前主线

N05原source15d77ac、1078249/1078290/post1078250仍今天12:05一次查收，原stage不动，未SSH或看partial。N05/N06后冻结N07，再N08和N09/10；当前cap104.971363333与严格<12GPUh自主规则保持。F/B关闭，P/T1后排，无新人评、生成器训练或OMR。
