# N07-R2：按最新指令立即查收，GPU与账单接受，CPU剩余评分待收

**已立即验收生成与财务部分。原完整180位置全部处理，无技术失败；完整科学验收还差CPU评分和终态回执，下一次改为北京时间12:50，不再等17:24。**

## 1. 当前实际发现

2026-10-17 **12:38:12北京时间**的原件快照确认：

| 范围 | 原始结果 |
|---|---:|
| 20完整预热 | 20完成 |
| 160正式位置 | 129完成／20文本拒绝／11视频拒绝 |
| 技术失败／未到达 | 0／0 |
| 1750源文件身份 | 全部一致 |
| 原件审计失败 | 当前0 |
| 十方法完整预热等价控制 | 10/10 PASS |
| 可配对的正式93帧视频 | 126 |
| 已完成93帧LPIPS评分 | 120/126 |
| 剩余兼容评分 | 6视频 |
| 接受但缺匹配Native35的视频 | 3，保留缺失 |

原GPU supervisor/runner已结束，child退出0，自身UUID锁与GPU释放。CPU post仍为原PID1212465/start546632437，尚无`post-CPU-exit.json`；当前`CPU-final-results.json`状态仍是`N07_SHARED180_CPU_AUDIT_RUNNING`。此时不能把已保存的部分评分均值作为冻结共同测试结果发布。

129条正式视频和20条预热合计149完成；不能误记为149条正式视频。31条正式拒绝均保留，不换样或补生成；3条参考缺失也不填零。

## 2. 实际费用已经独立核对

原账单、supervisor、v2对应job与完整池加法一致：

- 本卡实际 **10.443678323 GPUh**，低于已批准完整上限15.055555556 GPUh。
- 累计实际 **106.722650231/113 GPUh**，预留0，余额 **6.277349769 GPUh**。
- 原origin79.99637737158223保持，未重置窗口、重记费用或写服务器账本。

GPU与财务接受不代替最终CPU审计和分组统计接受。后续N08完整40的3.6275 GPUh报价仍只是计划，实际生产CPU与fresh准入未完成前不启动。

## 3. 提前查收的执行边界

用户最新直接指令：**“gpu 生成完了那就直接验收呗”**。它覆盖原本地17:24等待条件；原launch、source、config、全部180分母、93帧及统计规则保持。

新增本地只读入口`collect_wc_N07_R2_user_authorized_early_terminal_20261017.py`仅对原collector和acceptor各一处ETA guard作显式授权覆盖。直接人类原话、原launch/CPU/已验证GPU结束健康回执及其SHA绑定，真实时间照实保存；未伪造原ETA、修改服务器stage、重新派发或增加GPU。五项本地授权正反控制与原接受器可逆源码/AST校验通过。

首次SSH传输因本任务FRPC连接关闭而保存UNKNOWN回执；本地日志记录同一visitor自动重连。连接恢复后仅一次读取原任务原件，未重启隧道、服务器任务或原CPU。两次原始回执均保留。

## 4. 剩余工作与下一次查收

当前CPU累计2800.989秒，126条兼容视频已完成120条，余6条加最终提示词分组统计。按当前剩余工作量保守估计，改在 **2026-10-17 12:50北京时间**查收一次；替换原17:24自动化，不持续监听。

下一次使用同一绑定入口与新的输出文件：

```sh
.venv/bin/python scripts/collect_wc_N07_R2_user_authorized_early_terminal_20261017.py \
  --output reports/wc_paper_N07_refusal_repair180_R2_terminal_collection_20261017_1250.json.gz \
  --acceptance-output reports/wc_paper_N07_refusal_repair180_R2_terminal_independent_acceptance_20261017_1250.json
```

必须等原CPU退出、所有适用原件/93帧/参考身份/双seed先聚合再prompt等权统计独立复算通过，才接受带登记拒绝和缺失的可用共同队列。完整160全部成功的标记仍按实际保留false；合法拒绝子集不被误判为方法失败。若CPU仍活跃，按新原件重估一次并结束，不循环查收。

N07每格一次耗时不是N08重复clean测速；此轮不发布R2方法优劣、物理质量或稳定加速结论。F/B保持关闭。

## 原件入口

- [最新人类时点覆盖](../reports/wc_paper_N07_R2_immediate_terminal_direct_human_authority_20261017.json)
- [首次连接失败原件](../reports/wc_paper_N07_refusal_repair180_R2_early_terminal_collection_20261017_1241.json.gz)
- [恢复后的完整原件快照](../reports/wc_paper_N07_refusal_repair180_R2_recovered_terminal_collection_20261017.json.gz)
- [独立接受器：原CPU仍活跃](../reports/wc_paper_N07_refusal_repair180_R2_recovered_terminal_independent_acceptance_20261017.json)
- [GPU财务接受与剩余工作量](../reports/wc_paper_N07_R2_immediate_GPU_finance_and_CPU_remaining_acceptance_20261017.json)

本轮0新GPU、0服务器源码/锁/账本写入；保留全部旧结果与原17:24历史记录。
