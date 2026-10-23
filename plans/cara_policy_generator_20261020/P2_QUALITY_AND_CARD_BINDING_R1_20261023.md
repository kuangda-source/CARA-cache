# P2 原质量模型入口与整卡绑定接续

## 已准备

- `p2_quality_entry.py` 使用历史固定 `OriginalMetricFactory`，依次加载 DINO、AMT-S、ViCLIP、RAFT-Things、MUSIQ-SPAQ；不自动下载、不替换权重、不合成质量总分。dynamic degree 保留描述性二值语义。
- 从完整生成 manifest 和实际 request/video 原件建立五维评分分母；93帧 MUSIQ 保留逐帧分数/PTS，其他指标保留原解码器及实际抽帧证据。日志先写完整位置，评分原输出先落盘再校验；失败保留原件与未到达位置。
- `p2_card_binding.py` 只合并同输入、seed、block、repeat/query、实际执行签名和参照一致的不同角色；保留原角色、查询账和逻辑路径映射，不跨重复计时或shadow合并。P1 CARA指纹改变即拒绝。输出物理manifest，但预算和派发字段保持未定。
- `prepare_cara_pg_p2_after_p1_r1.py` 现在同时独立重验原P1、R4 Native/历史CPU及R2组合CPU。新增必填 `--combination-capture` / `--combination-acceptance`；旧命令不能省略。
- 本地28项评分/绑定/接续检查、6项新CPU控制器隔离/原件检查通过。均不是实际五模型运行证据。

## 固定资源包

`reports/cara_PG_P2_quality_original_packet_r1_20261023.json` 绑定执行source `8cc2466f8fc8369e4c1d542d672f536764ccecbf`、257个源码/配置文件、五个模型共2,195,545,639 bytes、10个依赖wheel及各自SHA。

本地包：`.sync/cara-pg-p2-quality-original-packet-r1-20261023`。
权重位置见packet；ViCLIP复用原本地固定文件，其余在 `.sync/cara-pg-p2-quality-resources-r1-20261023`。五个权重及12个DINO原文件均按历史固定SHA验证，VBench固定 `fd18b3d055cb0fc6f066ca90fe2c3c8cbb698490`，MUSIQ源码SHA也按原件核验。失败下载原件保持，最终完整包没有权重/源码缺项。

**包完整不等于运行环境完整。** 所列wheel不是已解算完的依赖闭包；四卡还有PyIQA间接依赖缺项（例如openai-clip）。须在独立目录完成依赖闭包/导入核查，不能对P1共用venv做pip安装。PyIQA固定0.1.10、timm1.0.24、easydict1.13；其余依赖及ABI按实际新CPU原件记录，不偷偷替换科学模型源码。

## 四卡真实模型 CPU

控制器：`scripts/wc_four_card_cara_pg_p2_quality_cpu_r1.py`，只提供CPU preflight/deploy/capture/accept，无GPU入口。模型stage独立为 `cara-pg-p2-quality-CPU-*`，源码与控制器版本分开绑定。

最新准入原件 `reports/cara_PG_P2_quality_fourcard_preflight_r1_20261023.json`：五权重尚未迁入四卡独立cache、依赖overlay未建立，磁盘37,235,888,128 bytes（约34.7GiB），低于原40GiB门槛。**本轮未创建远端模型stage、未加载五模型、未提交CPU/GPU，P1 stage和环境未改。**

待磁盘满足实际资源迁入后仍≥40GiB、MemAvailable≥32GiB：

1. 核对本地packet及五权重SHA；迁入本人 `cache/cara-pg-p2-quality-r1/<ROLE>.pth`。先核容量，传输结束逐个复核SHA。不要清理P1或他人文件。
2. 在该cache的 `dependency-overlay` 内离线安装已锁定依赖，验证完整依赖闭包，保存 `dependency-overlay-manifest.json`（`base_environment_modified:false`、`files`为每个overlay文件相对路径→SHA）。不修改基础venv、固定上游源码或模型权重。记录真实导入环境后再准入。
3. 用已推送的控制器 `preflight --packet ... --output <唯一新回执>`。完整通过后单次 `deploy --packet ... --stage-name cara-pg-p2-quality-CPU-r1-20261023 --output <唯一launch>`。1CPU/8GiB、network none、root只读、GPU不可见。
4. 捕获原launch；UNKNOWN先恢复原stage/容器，不能重派。原五模型CPU bundle逐一实际加载原权重并做固定几何合成输入前向，保留五角色分母。容器退出0后 `accept --capture ... --output ...`，重新核原始字节/源码、容器隔离和五模型原件。
5. 再通过 `run_cara_pg_p2_quality_r1.py --declared-synthetic-CPU-probe` 对固定合成93帧视频运行真正五维视频入口；该入口需要上述真实模型原始capture/acceptance/registration/resources，拒绝把本地mock控制冒充模型CPU。

旧两卡N10 CPU仅确定原模型协议，不充本四卡新环境接受。旧R2组合CPU保持已接受，不重复派发；本次新质量入口与资源检查需另行接受。

## P1 接受后才绑定最终整卡和预算

1. 原P1完整终态、合法策略独立接受后，以R4入口CPU和R2组合CPU原件生成P2接续；不能从P1部分输出或诊断质量选策略。
2. 冻结少步Native等实测时间选择及完整输入身份、控制角色/查询协议；用 `prepare_cara_pg_p2_card_binding_r1.py` 独立重验P1/CPU并产生物理去重蓝图。该脚本不报价、不授权、不派发。当前质量readiness仍false，后续真实质量接受必须由最终stage独立绑定，不能手改ready字段。
3. 实际P2整卡runner/capture、原P1 OFF参照、原始历史分支、五维质量原件和完整请求时钟在最终manifest上连接；独立验收重建全部分母与别名。当前 `p2_combination_stage.validate` 继续关闭真实GPU准入，直至上述实际绑定完成。
4. **按P1结算和策略物理去重结果才确定完整矩阵与预算。** warm、完整CAL查询、Native计时、shadow额外D、五模型加载与评分、保存/监测/清理均进入整卡成本。保留原查询账；旧518路/78.5GPUh只是历史未去重规划上界，不能据此派发或拆卡。

本轮P1半程00:52、终态05:32不变，不新增重复自动化，不使用P1部分科学结果。
