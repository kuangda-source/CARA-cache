# sensitivity8 流水线续卡补充预注册（已批准单次启动）

Run `cara-native-sensitivity8-pipeline-r2-20261104`。原r1失败费用及seq92结算保持，不重派旧run。
本卡仅完成原 `../PREREGISTRATION.md` 的Native轨迹和s(t)部分；同一八输入、seed0、C定义、14步位和s·Δv函数全部不变。
F17速度、绝对T_DD、LPIPS、六质量门及δ0.027/70排列/p≤0.05判据不变；16条clean只复用独立F17卡完整释放/唯一结算后的原CPU结果，不重复运行或评分，不以F17质量是否过门筛选s(t)。

复用原SENS_003–007五条完整Native记录，70份状态按尺寸和ZIP中央目录核查；无原文件SHA旁证。
一次SENS_003/t8的CPU载入验证了原嵌入digest；其它文件在实际消费时各校验一次嵌入digest，不能把结构核查称为全量内容哈希通过。
008截断，不复用其状态；human_034、misc_9699390-uhd_3840_2160_30fps、physics_017各重新记录一次。

先两个warm，然后按输入分组：复用/新记录→该输入14条single-C后缀。首个旧AV保留原Native桥、t8/t34不干预后缀、t8/t34完整single-C五控制。
每个新record的14条后缀全部成功后，删除其14份`state_before_*.pt`，再开始下一个record；失败时保留当时现场，不跳过或补样。
保留metrics、每步latent、14份guided、终态latent及MP4，每新输入约0.378GiB，按0.407GB上界核容。
五条复用记录所在旧256GiB卷全程只读，暂不释放；完整评分/原理重建后再保留小产物并处理旧卷，本卡不写旧卷。

只对CPU字节副本做一次finite+digest；读回在CPU重建后验证一次，再传到原设备，保持storage alias、UniPC、RNG与原控制。未修改GPU数值公式。
主方案122新请求=3record+112suffix+2warm+5控制；无控制117仅作报价对照，不是当前登记主方案。
新增64GiB私有输出容量、4GiB低水位、50GiB内存、90°C及600s退出余量不变。首次启动前提交并发布本卡源码；在独立stage完成Linux入口与fresh准入。
正式工程报价、测量及不确定范围在manifest。无监控、cron或自动后继工作。

2026-11-04，首次GPU执行前修订：用户批准「F17 非劣未过也照样上卡补跑，保留 5 条控制，约 10.37 GPUh，硬限 11.5 GPUh」。F17门结果按原样报告为FAIL、单侧非劣p=0.300，未改判；取消其作为本卡启动条件。仍保留全部五控制，正式中心>11.0或ledger可用<11.5不启动；50GiB内存、90°C、4GiB低水位及600s退出余量不变。
