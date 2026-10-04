# W3 固定配额位置交换：CPU 接口接续

2026-10-04；当前 LOCAL_STDLIB_PASS / SERVER_TORCH_PENDING；新 GPU 0。

## 已完成的改动

新增独立 `rv0_fixed_plan.py` / `rv0_fixed_mask.py`，复用原官方 forward 的已冻结决策 hook 与完整状态恢复，不修改 OneAction、原8父/24后缀/18输出草案或其历史验收身份。新接口限定 step22 后的44→72调用窗口，固定其余行动、仅交换同CFG的两处 C/D。完整次数分别在条件/无条件槽位核对；所有分支各自演化 latent、缓存和完整 UniPC 历史。

缓存必须有已支付 probe、过去同CFG真实 full 历史、有限数值及合法年龄。calls69..72保留自然保护动作，若与父mask冲突，该次干预停止为不可行；不 override 保护、不增加D后继续称配额匹配。报告区分两处计划改动与由于后续状态变化产生的自然决策 override 数；固定父mask是离线诊断，不是在线策略、相同秒数或单状态 Head 标签。

[本地原件](../reports/wc_w3_fixed_plan_local_cpu_r1_20261004.json)完成18项无效plan拒绝、不可变计划、两CFG静态配额及120四个真实父mask校验。四个新文件语法通过，37份旧CPU依赖SHA保持。[新CPU清单](../manifests/wc_w3_fixed_mask_cpu_r1_20261004.json)绑定来源；服务器Torch完整续推尚未运行，不作实际状态合法性或方法结果。

## 待验收的组合控制

拟复用 pinned sampler/WC/完整冻结Video2World类AST的已有CPU夹具；两个Toy场景×flow OFF/ON。每组固定原mask与两CFG各一个交换，按正反顺序重复；要求原生观察器OFF/固定原mask完整72输入输出/cache/solver/RNG/最终产物一致，交换仅两动作且每槽位完整配额匹配。缺少自身历史、模式变化、前缀账本漂移、非有限缓存、过期来源及保护动作冲突须拒绝并恢复父状态，保留失败原件。

实际模型权重、GPU、视频质量及交换收益均未由这个Toy/CPU接口验证。当前13h预算仍used11.022315686839217、45jobs、无inflight，余7119.663527秒；CPU验证不改账本。下一真实生成卡仍需全部费用估价与既定资源/来源门，无新增Head/LoRA/训练/人评。
