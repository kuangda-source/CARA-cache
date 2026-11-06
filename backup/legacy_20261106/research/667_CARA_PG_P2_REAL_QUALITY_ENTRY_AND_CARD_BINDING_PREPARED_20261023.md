# 667 — P2 原质量模型入口、资源包和整卡绑定准备

已接入固定五模型的真实评分工厂及原始视频评分接口，补齐物理策略去重、逻辑角色保留、P1/R4入口CPU/R2组合CPU联合重验。最终整卡预算继续等待P1完整接受和去重；无新GPU提交、预算预留或P1 stage/环境改动。

## 本轮交付

- `src/wcomr/policy_generator_r1/p2_quality_entry.py`：五维完整分母、原request/video SHA绑定、实际解码/抽帧证据、MUSIQ全部93帧及PTS、逐模型释放、原始评分先落盘再接受，失败保留未到达位置。
- `src/wcomr/policy_generator_r1/p2_card_binding.py`：按完整执行签名合并真正相同的角色；不同seed、phase、repeat、query、shadow保留独立路径。CARA指纹绑定原P1选择，预算不在本轮生成。
- 两个准备/评分CLI及独立四卡模型CPU控制器；控制器保留原角色CPU实现，1CPU/8GiB、无网络/无GPU、root只读。注册source与新controller source分开绑定。
- 28项评分/去重/原P1接续检查、6项控制器隔离与原件故障控制通过。回执 `reports/cara_PG_P2_quality_binding_local_controls_20261023.json` 与 `reports/cara_PG_P2_quality_controller_local_controls_20261023.json`。这些为声明的合成控制，没有实际加载模型。

## 资源核查与恢复

最初四卡只读盘点未找到五个固定权重，PyIQA/timm/easydict及若干间接依赖缺失。没有尝试改写正在供P1使用的环境。

本地已取得并校验五个原始权重，共 **2,195,545,639 bytes**。AMT首次curl TLS失败保留，后由Python下载取得完整文件并通过同一固定SHA；没有换模型。ViCLIP复用既有本地原文件。DINO缺失的源码按原SHA补齐，VBench固定commit与MUSIQ原源码身份保持。

完整本地源码/权重清单：`reports/cara_PG_P2_quality_original_packet_r1_20261023.json`。source `8cc2466f8fc8369e4c1d542d672f536764ccecbf`，257源码/配置文件、五模型、10个wheel。源码和权重缺项为0；依赖闭包尚须在独立overlay验证，10个wheel不能称为完整运行环境。

## 实际准入结果

`reports/cara_PG_P2_quality_fourcard_preflight_r1_20261023.json` 在实际2026-10-23 23:28:26检查：可用磁盘37,235,888,128 bytes（约34.7GiB），低于既有40GiB门槛；五模型未迁入新cache，独立依赖overlay尚未建立。新模型CPU未启动，五模型尚未实际在四卡验收；不把本地资源包或34项控制冒充运行结果。未降低准入线或改动P1。

接续见 `plans/cara_policy_generator_20261020/P2_QUALITY_AND_CARD_BINDING_R1_20261023.md`。空间允许后先资源迁入/独立依赖闭包→五模型实际CPU→合成93帧真实五维入口；P1完整接受后再冻结最终整卡、策略去重并计算预算。此前666的组合CPU接受继续有效，但不覆盖本轮新增质量入口。
