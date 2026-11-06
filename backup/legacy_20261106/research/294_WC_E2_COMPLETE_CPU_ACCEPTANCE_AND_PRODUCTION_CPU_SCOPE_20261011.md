# E2完整CPU独立验收与实际生产CPU登记

2026-10-11。**新确认／计时入口已完成完整受影响CPU范围，独立重载张量和旧输出对照通过。** 它支持继续进行真实生产配置检查；真实模型的输出等价、质量和计时仍需要完整GPU卡。

## 完整CPU与独立原件证据

原source `5152d4b263296581a14ce1b7bcae6a0b322e3be8`、213冻结载荷保持；stage `.sync/wc-e2-confirmation-timing-cpu-r3-20261011`，监督4043674／子4043675均退出0且已消失。全wall **910.129098秒**；只有CPU，没有CUDA初始化、GPU提交或账本写入。

- flow OFF／ON各76条成功路径，共 **152路径、5472实际UniPC更新、10944正常CFG调用**。
- 独立重载 **3168 guided张量＋152 final latent**；八条代表路径与原已验收Toy sampler的全部36 guided及final逐位一致。32条AV28计时路径与各自AUDIT控制的动作、final和Toy writer字节相同。
- 20语义变异拒绝、两次实际末计时文件截断拒绝、两次末writer失败完整76位置保留，以及八次text／video拒绝控制通过。原设置及请求初始状态恢复，原件不改。
- 保留R1双probe计数观察失败、R2只完成flow OFF后在预期guardrail拒绝抛异常的历史；未删除或追认失败。

[实际终态与独立重载](../reports/wc_e2_confirmation_timing_cpu_r3_terminal_20261011_capture.json)。这里仍明确使用Toy权重、attention、Native类、16×16准备和93×432×768 Toy decode／JSON writer；不是2B模型、真实视频、LPIPS或clean延迟证据。

## 下一张实际生产CPU范围

卡身份 `WC-E2-PHASE-A-CONF40-TIMING32-PARITY4-R1-20261011-A`，保留原40确认＋32平衡计时＋额外四代表AUDIT等价检查，**76实际GPU路径／2736更新／5472CFG**。四新提示词、seed17／43、五版本、两个阶段A共同主比较与两CAL四轮顺序全部保持。

生产CPU从已验收E2原stage只读复制213来源，另冻结新生产contract／runner／CPU监督和本次CPU原件；实际十条完整请求为八确认输入与原AV28／AV51 seed0计时输入。只读验证原32生产依赖的完整源资产合同、真实八区间校准指纹与阈值、实际InferenceArguments、Native入口、guardrail资源／Blocklist、五个缺guardrail入口拒绝及13个方法／scope／费用合同变异拒绝。禁止CUDA、权重加载和下载，生产CPU不选GPU、不写费用账本。

CPU结果必须来自新的独立目录 `.sync/wc-e2-production-cpu-r1-20261011`，完整终态、原字节和源hash验收后才能成立。本文是事前登记，不能把syntax检查或启动状态说成实际生产CPU通过。

## 费用与接续

[完整76预测](../reports/wc_e2_full76_whole_cost_r1_20261011.json)仍为 **9.869732459 GPUh**，严格超过本轮8h自主范围。先完成生产CPU、实际GPU监督／评分／原件接线和可审查完整卡，再请具体批准；不拆72、减少重复或取消parity来绕过确认。旧32／64批准不移用到本卡。

累计实结 **39.183807748／77.895246590 GPUh**、75历史提交、新48窗口余额 **38.711438842**；本轮新GPU0。E1完整CPU独立验收保持，后续真实显存区分仍未执行；A确认不等待P科学成功。旧正负结果、拒绝与缺失保持，不新增人评门槛。
