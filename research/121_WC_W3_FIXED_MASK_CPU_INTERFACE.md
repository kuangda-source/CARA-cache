# W3 固定配额位置交换：CPU 接口接续

2026-10-04；当前 ACTUAL_SERVER_CPU_PASS / REAL_SWAP_GPU_PENDING；新 GPU 0。

## 已完成的改动

新增独立 `rv0_fixed_plan.py` / `rv0_fixed_mask.py`，复用原官方 forward 的已冻结决策 hook 与完整状态恢复，不修改 OneAction、原8父/24后缀/18输出草案或其历史验收身份。新接口限定 step22 后的44→72调用窗口，固定其余行动、仅交换同CFG的两处 C/D。完整次数分别在条件/无条件槽位核对；所有分支各自演化 latent、缓存和完整 UniPC 历史。

缓存必须有已支付 probe、过去同CFG真实 full 历史、有限数值及合法年龄。calls69..72保留自然保护动作，若与父mask冲突，该次干预停止为不可行；不 override 保护、不增加D后继续称配额匹配。报告区分两处计划改动与由于后续状态变化产生的自然决策 override 数；固定父mask是离线诊断，不是在线策略、相同秒数或单状态 Head 标签。

[本地原件](../reports/wc_w3_fixed_plan_local_cpu_r1_20261004.json)完成18项无效plan拒绝、不可变计划、两CFG静态配额及120四个真实父mask校验。四个新文件语法通过，37份旧CPU依赖SHA保持。[新CPU清单](../manifests/wc_w3_fixed_mask_cpu_r1_20261004.json)保留创建时的pending状态和冻结42文件；后续真实结果以本报告及下述原件为准，不改旧身份。

## 实际服务器 CPU 结果

[实际CPU原件](../reports/wc_w3_fixed_mask_cpu_r1_20261004.json) / [独立审计](../reports/wc_w3_fixed_mask_cpu_r1_audit_20261004.json)：source `8895c0e4822cef15a89fdcda517218aa1aac718b`、独立`.sync/wc-w3-fixed-mask-cpu-r1-20261004`，Torch2.7.1+cu128实际执行，exit0，CPU wall **120.407008秒**；CUDA初始化被禁止且未发生。没有下载/加载真实模型权重，没有GPU提交或生成视频。

两个Toy场景×flow OFF/ON共4组，每组固定原mask两次、两个同CFG交换分别两次，合计 **24条完整后缀**，每条14次原UniPC更新/28CFG。Pinned sampler/WC/整个冻结Video2World类AST保持；Toy fixture自己的交换是45→47/46→48，原/交换完整配额都为[19,19]。这与120真实父候选47→49/48→50/61→63/46→48不同：前者验收接口，后者尚待真实状态合法性和收益，不能混作同一批结果。

| 检查 | 实际结果 |
|---|---|
| 原官方与router OFF +恢复分支 | CPU夹具内全72输入/输出、缓存、solver、终态/RNG/mock产物严格相等 |
| 固定原mask | 28次后缀输入/输出/缓存/deep与原父continuation相等 |
| 两CFG分别交换 | 实际mask/deep仅两位置改变；每槽位完整配额相同；状态各自演化 |
| 正反顺序重复 | 三种安排各自的全后缀轨迹、最终latent和状态组件相等 |
| 同输入动作控制 | 首交换处以前（含该次输入）完全相等，C为0个deep，D为3个Toy deep |
| calls69..72 | 自然C/C/D/D保持，无保护override；故意冲突明确拒绝 |
| 失败恢复 | 历史不足、eval变化、前缀账本变化、非有限cache、来源过期、保护冲突，每组6次，共24次TECH_BLOCKED全部恢复 |
| 条件 | 真实冻结类AST、两条件的类/身份和值保留；原有冻结恢复控制按相同SHA复用 |

独立使用服务器原生cat/sha256sum复读 **54项**：42阶段文件、7官方源、原件/两日志、旧CPU原件和权威预算。原件SHA `a8da6bfac7f7940ec41b6d621f04bcad8fad51611640e5a7869dc2be3e2a8df6` 匹配；本地从返回raw branches重算全部24 mask/deep、两CFG配额、首动作同输入、重复轨迹/状态与24失败恢复。官方/OFF完整pipeline等价是SHA绑定测试中实际执行的断言，独立审计不声称重新运行那一断言。

实际模型权重、GPU、视频质量及交换收益均未由这个Toy/CPU接口验证。当前13h预算仍used11.022315686839217、45jobs、无inflight，余7119.663527秒，预算前后原字节及SHA不变。完整旧8/24/18草案/source/科学分母未改，不重跑旧96/48后缀回归；新接口相关的完整控制已运行一次。

## 接续顺序

固定mask必要CPU接口已验收。下一具体化最小真实自适应C/D与最多四组同配额交换的执行身份、严格参考桥及完整费用；报告两种干预的不同科学含义，不把自适应首动作收益或双位置联合收益当预算Head单步标签。保留W1新两例全帧保真正结果；初批W3仍固定官方近似器/dense，未来有空间才单独登记W1×W3的2×2。CPU阶段不扩成当前GPU提交，无新增Head/LoRA/训练/人评。
