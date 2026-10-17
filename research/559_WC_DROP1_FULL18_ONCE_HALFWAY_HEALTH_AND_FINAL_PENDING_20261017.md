# 少一次D三臂：22:46一次半程技术检查

北京时间 **2026-10-17 22:46:38.829133**，按预定时点完成一次只读查收。原卡技术上仍在执行：**18总路径中14完成、1执行、3未到达**（总分母包括6条完整预热）。原supervisor、runner和CPU post三个句柄的PID／start_ticks／命令均与准入原件一致。

本次快照未见OOM、Traceback等登记错误。GPU0原UUID由原runner1515544占用，显存记录27,621 MiB，自身UUID锁仍持有，磁盘可用359,056,158,720字节。瞬时GPU利用率为0%，单次取样不用于推断持续利用率或任务停滞。

## 范围和时间保持

原source `e76b4f8b934bb07bf045e6083f36eddb4711640d`、config SHA `8c2a0d512f8ccc4f8a7a57a237949fcee56f4cb8dde9bfd94cd032369669b4ba`、registration SHA均通过本地原件独立比对。未改变原stage、参数、路径或进程，未重派。

本次仅技术状态，**未读取科学partial，未接受任何新LPIPS、速度或完整原件结果**。原完整验收仍为北京时间 **10月18日00:01**，届时收全部18分母、全部适用正式93帧、旧S26-C控制和实际费用。当前原计费预留2.25 GPUh仍是预留，不能当本卡实费。

| 22:46快照的预算项 | GPUh |
|---|---:|
| 同一累计cap | 226 |
| 原origin | 79.99637737158223 |
| 已实结 | 109.39479812385285 |
| N12完整在途预留 | 2.25 |
| 扣预留可准入 | 114.35520187614715 |

以上数值仅限本次快照。原历史账不变；本次0新GPU、0账本写。

## 原件和后续

- [一次技术原件](../reports/wc_drop1_full18_halfway_health_20261017_2246.json.gz)
- [本地独立技术接受](../reports/wc_drop1_full18_halfway_independent_technical_acceptance_20261017.json)
- [原整卡准入](555_WC_DROP1_FULL18_CPU_ACCEPTED_GPU_ADMISSION_AND_TWO_COLLECTIONS_20261017.md)

半程任务已完成，对应一次性自动化 `worldcache-26d` 已删除，避免重复查询。`worldcache-180` 的00:01完整验收保持。下一步先完成原卡验收与解释；N09本地接续已准备，N10真实质量评分仍待，当前不派发下一张GPU卡。F/B关闭，P／历史网络增强后置。
