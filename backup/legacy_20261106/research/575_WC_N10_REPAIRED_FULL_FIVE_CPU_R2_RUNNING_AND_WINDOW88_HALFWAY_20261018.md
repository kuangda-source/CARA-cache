# 修复后的完整五模型CPU R2已运行，88数值CPU半程无错误线索

2026-10-18。**N10已完成限定修复并重新启动完整五模型真实CPU；连续修正88路径的半程检查也已完成。** 原R1全部错误与原N12视频结果保留，新评分和A3终点仍为空。

## N10修复R2实际身份

[58项本地修复](574_WC_N10_ACTUAL_CPU_METADATA_AND_LOCAL_GIT_VERSION_REPAIRS_20261018.md)后，[完整五模型R2](../reports/wc_paper_N10_full_five_model_CPU_R2_launch_20261018.json)以新source `fb89a755118257b520446e2e029f6231bc7ad191`、独立stage `.sync/wc-N10-models-cpu-r2-20261018`单次派发，244payload；原PID **1688791**／start_ticks **555576034**，注册SHA `28dbb0633aa763de1c998eb974fed978c0fda28841de62422a6b6af59ccd8b67`。

实际启动 **02:14:16.819221**。最早半程02:21:46.819221，安排 **02:22**；完整最早02:29:16.819221，安排 **02:30**，各一次。`worldcache-n10-cpu`／`worldcache-n10-cpu-2`已创建。原R1已终态，不重复派发或改写其接受结果。

仍完整执行DINO／AMT_S／RAFT_THINGS／ViCLIP／MUSIQ_SPAQ，保持原五权重、官方216源／DINO12源、BPE、原预处理、CPU FP32/eval与两线程。修复只使验收描述对应实际DINO宽高比、规范AMT源码路径，并允许GitPython精确本地只读版本查询；其他联网与下载继续拒绝。失败加载记录和保护调用栈保留。全部五项独立接受后才能接正式评分身份和整卡报价。

## 连续修正88：半程已收，完整02:20不变

[02:14原半程](../reports/wc_drop1_window88_actual_CPU_R1_midpoint_20261018_0214.json.gz)及[独立技术接受](../reports/wc_drop1_window88_actual_CPU_R1_midpoint_independent_20261018.json)确认原source57b4c19、PID1685865和注册匹配；原进程已消失，数值和worker结果文件均存在，技术错误线索为空。

半程没有读取数值结果或完整日志，**还不能宣布88通过**。原02:20一次完整查收／离线独立接受保持，`worldcache-88cpu`半程自动化已删除，`worldcache-88cpu-2`最终保留。完整64新＋24原控制、三命令及全部源／runtime身份不缩。真实完整24生产、旧端点／预热控制、整卡报价和GPU仍待。

## 执行边界

两项CPU任务各自source和独立stage绑定，N10修复没有改正在验收的88原stage或数值源码。没有本项目GPU卡或预留；N09因为外部两GPU满显存尚未准入，完整40和真实CPU通过证据保持，GPU测速仍优先且不并发重CPU。

同一累计cap226、最近实结110.869061155／预留0余115.130938845，origin与所有历史费用不变，新增GPUh=0。严格<12整卡自主、半程／预计结束各一次查收规则不变，F/B关闭，无训练、人评、付费VLM或OMR。
