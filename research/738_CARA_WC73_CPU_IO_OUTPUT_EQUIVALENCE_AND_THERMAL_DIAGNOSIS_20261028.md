# 738｜WC73 CPU读取、已完成输出及Ada热环境核查

用户授权仅分析既有产物并排查高温，不重跑GPU。本轮原stage、配置、门槛及旧统计结论保持；独立CPU核验与只读硬件查询产生增量回执。

## CPU超时原因

原宿主直接调用的虚拟环境python是指向`/usr/local/bin/python`的符号链接，该目标仅存在于容器中，故宿主直接调用失败。这与随后CPU读取超时是两个不同问题。

读取超时已通过阶段记录及进程I/O定位：产物在`/dev/loop6`，其32GiB ext4镜像位于`/data20t`的旋转磁盘`/dev/sdc1`。检查时sdc利用率94.8–98.8%，loop读等待约0.6–0.7秒，吞吐有时仅52–748KiB/s，也出现3–4MiB/s；宿主CPU仍有61%空闲、24%等待I/O，内存可用约45GiB，采样无swap进出。CPU分析进程处于`D/wait_on_page_bit_common`，而CPU累计仅数秒。证据指向存储I/O等待，不是比较算法计算了180秒，也没有OOM证据。

上次脚本对5个约294.6MB档案先整文件SHA、再从原盘逐storage重读，合计约2.95GB逻辑读取；统一180秒且结束前不写进度，无法适应当前存储状态。修订后的独立审计只从原盘读一次至内存，核对原SHA后在内存解析dtype/shape/stride/storage并逐字节哈希；不导入torch或创建CUDA上下文。分阶段进度与逐文件回执保存在系统盘/tmp，分析进程限制两个CPU核并有最长30分钟超时。r1在精确PID/start ticks核对后停止，r2接替；这仅是CPU核验优化，不是生成重跑。

磁盘95%占用是背景情况，不能直接当作唯一原因；镜像40段、首个诊断档案3段，不支持把严重碎片认定为主因。现存内核磁盘错误指向另一块sdb，不应误报为WC73所在sdc损坏。已有SHA核验用于区分读取慢和内容损坏。

## 视频输出

使用原FFmpeg CPU解码及原几何/PTS协议，11条已完成视频均为93帧、432×768、16fps，完整检查1023帧，无裁剪、重采样或子采样。

首个AV28样本的Native OFF/ON、allD OFF/ON、Native ON/allD ON，RGB字节哈希及逐帧PTS完全一致。Native、allD、README的warm与各自诊断OFF视频也完全一致；这是补充终点检查，不能把warm冒充缺失的预注册README ON路径。

原12条诊断只完成5条，第二个样本未开始；原73条整卡与三臂门禁依旧未完成，未选参冻结、未进入B。

## Ada高温：已确定与未确定

原任务低功耗加载阶段已有61–64°C；进入高负载后功耗中位数285.16W，68个≥90%利用率的独立样本中56个温度≥88°C，SM中位数945MHz。最终监督查询达到≥90°C并按原规则停止；触发温度在持久化之前抛异常，因此日志最后一条89°C与热停并不矛盾。

只读现场检查显示功率上限300W与出厂默认一致，应用时钟设置与默认一致；当前该GPU在另一用户负载下约80°C、风扇56%、约131W、SM约2730MHz，热/功率限制事件位均未活动。未操作该用户任务。当前风扇确实运转，不支持断言风扇停转或人为锁低频；但当前不同负载不能代替昨晚的事件状态。

较高起始温度、接近额定功耗的持续计算与高温共现，支持散热余量不足为优先排查方向。原日志未记录风扇、进风温度、机箱风扇/BMC及限频原因位，所以尚不能区分机箱进风不足、热回流、积尘、风扇策略或板卡散热接触问题，不能把所有低频归因于热降频。现有hwmon仅有CPU/NIC温度，无机箱风扇遥测。

下一次执行前宜由服务器维护方核查进出风、相邻卡遮挡/热回流、机箱与GPU风扇及积尘，并在后续另行授权的任务记录风扇和完整限频原因位，先持久化触发采样再退出。本轮未改风扇、功率上限、时钟或90°C阈值，也未启动压测/模型生成。

证据：[I/O与热诊断](../reports/cara_wc73_CPU_IO_and_Ada_thermal_diagnosis_20261028.json)、[存储布局](../reports/cara_wc73_storage_layout_diagnosis_20261028.json)、[完整RGB检查](../reports/cara_wc73_completed_RGB_verified_20261028.json)、[RGB资源释放](../reports/cara_wc73_RGB_CPU_resource_release_20261028.json)。

## 张量与完整可配对子集结论

11个完成路径的保存张量档案SHA全部与原运行记录一致。5个诊断档案各含36个guided输出和最终潜变量，均little-endian；比较dtype、shape、stride、storage metadata及全部storage数值字节，不依赖浮点容差，也未重新执行模型。

三组预期等价对：Native OFF/ON、allD OFF/ON、Native ON/allD ON，36步guided输出、最终latent、输入/RNG、93帧RGB及PTS全部精确一致。Native/allD/README各自warm对诊断OFF的最终latent、RGB和PTS也精确一致。CARA和两个tau仅有warm，验证产物完整性，不构造不存在的正式等价参考。

因此可排除“在首个AV28已完成配对上，计时开关或强制全计算包装器改变数值输出”。不能扩展为缓存README完整OFF/ON已通过，也不能扩展到第二个CAL；原A门禁保持不完整。

CPU存储单次读取版本379.612秒墙钟、15.755秒CPU；视频解码70.405秒墙钟、16.111秒CPU（含子进程）；全部档案元数据和补充latent核验26.278秒墙钟、0.767秒CPU。三项成功核验共32.632秒实际CPU，部分并行故墙钟不相加作实际总时长。先前双读取版本约300.63秒后按精确句柄停止，其CPU未精确计量；只读诊断、SSH及本地整理亦未过程计量。所有本轮CPU句柄已退出，新增GPUh=0，原0.980652754 GPUh结算不变。

完整接受回执：[已完成子集输出等价](../reports/cara_wc73_completed_output_equivalence_acceptance_20261028.json)，包含逐证据SHA；[张量比较](../reports/cara_wc73_completed_tensor_verified_20261028.json)、[全部档案元数据](../reports/cara_wc73_completed_latent_metadata_20261028.json)。旧737中“张量尚未核实”保留为当时事实，本增量补齐该项，不回写旧原件。
