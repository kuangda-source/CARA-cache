# MF-00 完整真实接口结果与费用（2026-10-10）

**必要的完整接口控制已经通过，可以进入校准RA及A/B/C方法开发。** Common/Human seed3各原始WC与成对native政策一条完整路径，共4条36步路径、144个guided输出、4个终点latent、4个完整93帧视频。两场景的完整guided与latent直接逐张量相同，动作、层访问、counter、全部五检查点与1216状态组件、条件和RNG一致。编码视频及完整解码RGB逐字节一致；没有用只比较文件哈希代替实际张量重读和全帧解码。

卡`WC-MF00-INTERFACE-R2-20261010-A`冻结source92b2d1a／177载荷。原监督3659246、runner3660184、后CPU3659247及其子3696333均退出0消失，锁释放，目标A6000末核27MiB／无compute应用。只读终态捕获保存全部原件、哈希和路径别名绑定，并独立重建完整分母。见[完整验收](../reports/wc_mf00_interface_r2_terminal_20261010_capture_and_independent_audit.json)。原R1监督失败和费用仍保留，未覆盖、未算成通过。

Common两路径均38full／34cache，Human两路径均35full／37cache。每条实际36solver／72net，request35步与WC70调用周期的尾部保持原政策。4个原始FP32完整路径文件共重读144guided和4latent，两场景的视频均为93×432×768×3。原始张量文件各自的序列化字节可不同，验收依据实际tensor内容直接相等；四视频的编码及RGB则同场景完全相同。

完整GPU wall1531.208646848秒，实费**0.425335735GPUh**，后CPU实际21.879140秒且CUDA未初始化。累计实费**30.529593763／77.895246590GPUh**，窗口剩余**47.365652826GPUh**，67次历史GPU提交、无登记在途GPU。以[服务器原字节账本](../reports/budget.json)为准；CPU只读捕获没有费用重置或新增GPU提交。

本卡是已曝光两个场景的实现控制，为进一步研究联合决策提供可靠执行入口。它不是旧16路／6.704GPUh卡的验收，不验证新RA调度、独立泛化、终点保真改善或干净速度。记录中的原始／成对pipeline wall分别为Common407.174／262.867秒、Human249.988／326.434秒，带诊断与顺序效应，不用于宣称新接口加速。

下一按[粗校准设计](../plans/WORLD_CACHE_RA_COARSE_CALIBRATION_R1_20261010.md)推进实际共享锚点轨迹的CC/DD及完整dense后缀，生成有观测依据的Cosmos RA表，再做完整BASE-R和A/B组合视频。[205校准核心](205_WC_RA_COARSE_CALIBRATION_CORE_IMPLEMENTATION_20261010.md)保留首CPU指纹错误与独立R2重试；不是方向或方法失败。完整单次≤4GPUh自主，超过4GPUh才具体确认；48GPUh窗口保持，不增加非必要人评。
