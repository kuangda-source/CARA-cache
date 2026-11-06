# 原N07首卡完整失败验收归档，R2保持原计划

2026-10-17。**原R1完整180路径的终态原件已按原时间一次查收，全部失败分母、已完成视频及真实费用得到独立复核，原任务收尾完成。** 整卡仍是技术不完整；当前主线等待此前获批并独立运行的完整R2，不以旧卡partial替代最终共同测试。

## 完整分母与已保留资产

| 原注册位置 | 完成 | 文本拒绝 | 技术失败 | 未到达 | 总数 |
|---|---:|---:|---:|---:|---:|
| 完整预热 | 20 | 0 | 0 | 0 | 20 |
| 正式 | 20 | 8 | 1 | 131 | 160 |
| 合计 | **40** | **8** | **1** | **131** | **180** |

运行器实际记录49行；131个未到达位置由原完整注册矩阵保留，没有把49行当成完整180，也没有补样或替换拒绝。原退出码为GPU child=1、CPU post=0；CPU post能够保存失败原件并不代表GPU整卡完成。

原1725份payload SHA一致，40条可用warm／正式原模型记录通过审计，10组完整预热guided／终态／动作／历史／RGB等价控制通过。20个有效正式视频各93帧RGB及LPIPS记录通过，原审计失败列表为空；这20个视频来自**同一个AV提示词、seed17／43和十方法**，含两条Native35参考。它们是失败卡中完整保留的局部资产，不能替代八prompt最终共同测试；本轮不据此挑赢家、改冻结方法或宣称稳定clean加速。

原技术错误仍为零步文本拒绝后，固定策略入口要求实际读出满足完整36步mask；原记录的1技术失败保持，未事后改写成第9次文本拒绝。该问题已有单独R2边界修复和具体整卡批准，本轮不再改原stage或重启R1。

## 原件与独立接受

- 原source：`140d0a6af7d5be16d1b191ab3a8e68ffe83d0007`，run `wc-paper-n07-frozen-shared180-r1`。
- 原三个句柄1115797／1115898／1115798及其start_ticks均已不再存活。
- 本次一次查收时间：`2026-10-17T05:33:28.034299+08:00`，北京时间，晚于原05:26:04.252最早门。
- [一次完整capture](../reports/wc_paper_N07_frozen_shared180_R1_terminal_collection_20261017_0530.json.gz)保留原GPU／CPU终态、原件库存、全部180行、逐帧评分、分组统计及当前账本。
- [独立接受](../reports/wc_paper_N07_frozen_shared180_R1_terminal_independent_acceptance_20261017.json)重算完整分母、warm控制、原件身份、全部可用93帧记录及原分组统计；`terminal_receipt_audit_accepted=true`，**`scientific_full_scope_accepted=false`**。

旧卡原全费用为**2.697147250265504GPUh**，已在10月16日结算。本轮核对其独立bill、v2原job和原supervisor的账单SHA，不再次计费。当前快照仍为实结96.278971908／cap113，R2完整预留15.055555556，可新准入1.665472537；预留不是R2实际费用，origin及所有历史job保持。

## 同一GPU被后续任务接手时的本地接受修正

原[acceptor首次执行错误](../reports/wc_paper_N07_R1_original_terminal_acceptor_execution_20261017_0530.json)如实保留：它要求GPU0当前完全空闲。此时旧R1句柄均已退出、账单已SETTLED，但同一UUID已经由具体批准的R2接手；旧collector看到的compute PID1212599属于此前独立接受的R2准入。

新增[本地任务归属接受器](../src/wcomr/frozen_shared_reused_device_acceptance_r1.py)只替换这一设备空闲条件：要求原R1句柄退出、原job独立结算，且后续独立已批准准入、当前v2完整预留、source／launch／config／CPU／授权／supervisor身份及GPU compute PID全部对得上。未知PID、旧PID残留、原账单未结算、后续身份错误均拒绝。它不改变原capture的锁／GPU字段，也不把当前GPU说成空闲。

原acceptor文件SHA保持`b93600daff82f236ec99a377f6eb762a0d4df297266785f1f486ae87a4f63997`。单处替换逆向恢复字节及AST均一致，原完整180／93帧／分组统计／费用门全部继续执行。[13项本地CPU控制](../reports/wc_paper_N07_R1_reused_UUID_terminal_acceptance_local_CPU_20261017.json)通过；原capture、原数值源码、原服务器stage和账本均未写。

后续R2准入仅使用其已经保存的01:26准入回执及本次只读账本／PID归属，未读取R2的runner、视频、质量或其他科学partial。这是旧任务释放的核对，不是提前验收R2。

## 收尾与接续

原`worldcache-26d`已经暂停，[实际自动化回执](../reports/wc_paper_N07_R1_terminal_automation_pause_and_R2_preservation_20261017.json)确认R2的`worldcache-180`仍ACTIVE，**今天09:24半程、17:24完整验收**不改。旧R1归档本身不触发N08；必须等待完整R2适用原件接受，随后按原冻结角色和完整40路径做N08独占重复clean测速。

N10本机完整ViCLIP在01:54已经独立接受，资源自动化保持暂停；服务器接入、五模型实际CPU和正式质量评分仍待主线接续，重CPU避开N07／N08。本轮仅原R1一次只读SSH与本地离线复核，0新GPU／重派／服务器源码写／账本写。F/B关闭，不新增训练、人评或OMR。
