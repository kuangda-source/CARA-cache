# 806 — 端点完整工件与跨运行评分清单CPU接受

完整释放后的工件身份门和跨运行评分清单组件通过两卡25项CPU控制（15项元数据控制、两种完整物理范围、八项真实视频错误控制），随后11项独立接受控制通过。实际PyAV读取完整32及去重25的新合成视频、每组四份合成旧Native参考，共65份视频/6,045帧；九项RGB控制每组全部通过。保留两侧原scope，十二份旧指标对象原样引用；本轮未计算新指标、未读原实验视频、未派GPU或访问中央账本。

## 原CPU终态

源码`d52f4422d296d8b5673c9543c16bbb9f3d393834`，stage为`/data20t/gaokuangda/worldcache_workspace/.sync/cara-S-endpoint-artifact-CPU-a6000-r1-20261031`，原容器名为stage名加`-cpu`，注册SHA为`17a543adf08c8665237b17b93088a49f51f15d3dc35162ebb9ac5e5fd5d5bb29`。20:02:15启动、20:02:22正常退出，ExitCode=0、Pid=0、无OOM；worker实测6.446669102秒。CPU26、1核、4GiB、零额外swap、network none、只读根文件系统、无GPU设备的边界经原capture及独立接受器核对。

所有媒体均新建CPU合成视频。实际编码使用libx264，实际解码为完整93帧、16fps、16×16 RGB24及精确有理数PTS；16×16只在显式CPU模式接受，生产固定93×432×768。成功完整范围的6,045帧计数不包含夹具构造和失败检查额外读取。生命周期/原指标身份为明确的CPU夹具，财务检查使用真实临时账本I/O；tensor仅用合成字节验证路径/大小/SHA，实际数值生成保持803的独立接受。没有将此处合成旧身份或指标视为真实历史视频再验收。

## 生产组件行为

入口首先重建原费用、唯一结算、进程/资源释放和完整集合检查，之后才读原评分对象、工件或帧。核对注册的proposal、原B36完整评分和读者源码SHA，以及新卡原model、precision、协议、card和budget binding。原四份Native及十二份复用指标按既有proposal逐行摘要绑定，原视频/参数文件重新验SHA；复用指标对象不改写scope、数值、曲线或来源。

新32或合法去重25的每个位置均核对固定输出路径、视频/tensor大小和SHA、完整保存参数及原参考的conditioning/default参数摘要。逐帧检查93帧、RGB24几何、16fps、精确PTS与原Native一致，完整RGB哈希前后核验视频字节。八项fresh Native/F19-A1对原RGB，加一项fresh Native warm对ALLD的控制必须全部通过。

通过后输出24个逻辑质量位置：十二份原指标对象加十二个新逻辑位置。预算策略与两个新SU策略都不相同时评分十二对；预算策略完全等于新SU策略时保留24逻辑位置，物理生成25条、只评分八个唯一新对，同一pair被别名引用且不算独立样本。历史Uniform相同不能代替本批预算角色的新计时。跨运行校验明确保持旧参考scope与新候选scope分别绑定，仍要求member、seed、host、GPU UUID、model、precision和完整比较输入相同。

真实媒体错误控制覆盖92帧、94帧、尺寸错误、15fps、文件SHA错误、fresh replay RGB变化、ALLD RGB变化及PTS偏移。后三项先更新合成producer的工件摘要，再由真实解码/身份门拒绝，避免仅靠旧SHA不匹配通过测试。15项元数据控制另覆盖完整分母、释放前禁止读取、视频/tensor/参数变化、默认参数变化、旧scope改写、旧指标进入新评分、原指标变化及CPU夹具进入生产。独立接受器11项控制覆盖原退出、源码、资源、两种范围、93帧、九控制、失败分母与合成范围。

## 剩余边界

此组件没有生成评分执行授权；返回清单明确`scoring_dispatch_allowed=false`、`metrics_computed=0`。下一步是绑定受限CPU评分环境/原Alex权重和源码、新跨运行评分CLI、仅一次评分句柄、完整新对接受及24位置汇总，保持原Fidelity-v2的93帧曲线/92相邻帧、PSNR infinity和零梯度状态。随后完成新端点一次派发/runner和全链CPU、原预算实际冻结mask的受影响验证、最终源与整卡报价。

新端点超过4GPUh的批准及其中央账本交易权限仍待单独取得。原单次14GPUh卡及23:16半程、次日06:01终验、06:45:04硬截止保持；本轮未重新观测原GPU状态或读取部分科学分数。

[原完整CPU接受](../reports/cara_s_endpoint_artifact_CPU_accepted_r1_20261031.json) · [原CPU终态](../reports/cara_s_endpoint_artifact_CPU_capture_r1_20261031.json) · [独立接受控制](../reports/cara_s_endpoint_artifact_acceptance_checks_r1_20261031.json) · [工件读者](../src/wcomr/cara_s_endpoint_artifacts_r1.py) · [跨运行身份校验](../src/wcomr/cara_s_endpoint_scoring_manifest_r1.py)
