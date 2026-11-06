# N08原完整40：服务器生产CPU已单次启动

**R2完整结果已形成[547报告](547_WC_N07_R2_COMPLETE_RESULTS_FIDELITY_COST_SIMPLE_CONTROLS_AND_N08_NEXT_20261017.md)并推送GitHub；按用户要求，现接续原五角色N08重复测速，服务器CPU已运行，GPU尚未派发。**

## 实际部署身份

| 项目 | 原值 |
|---|---|
| source | `8bdebc340737599a6923c01a31a4734b04bc3f4b` |
| 独立stage | `.sync/wc-paper-n08-production-cpu-r1-20261017` |
| CPU PID／start_ticks | `1263883`／`550947856` |
| 实际启动 | 2026-10-17 13:22:55.046北京时间 |
| 原始配置 | `configs/wc_paper_N08_balanced_full40_production_r1_20261016.json` |
| registration SHA | `da6bd03453564eb09362c10c7f461d9fb013303ef3cb9d0accec264f3cf09688` |
| 完整payload／overlay | 1747／180 |
| 实际CPU命令 | 原九命令，8组控制＋Cosmos无权重真实入口 |
| 首次查收最早 | 2026-10-17 13:27:55.046北京时间，安排约13:28一次 |

[原单次启动回执](../reports/wc_paper_N08_full40_actual_production_CPU_R1_launch_20261017.json)保留完整overlay SHA与进程身份。stage从原已验N05 CPU基底独立复制，原基底、共享runtime、已结束R2与账本均未写入；CPU禁止CUDA/模型权重，0新GPU。CPU通过前不能将本卡写成测速已启动或结果已取得。

## 完整执行合同保持

[548完整卡](548_WC_N08_COMPLETE40_FROZEN_REPEAT_TIMING_SELECTED_AND_PRODUCTION_CPU_PREREG_20261017.md)：AV28/Human199、seed0、五角色固定Native35/WC_HALF/RA_DEFAULT/A_NO_P/TABLE_PHASE_H1，三平衡轮30正式＋10完整预热，一次加载、1440pairs/2880CFG/0teacher；35请求步、36实际更新、93帧。原method-freeze SHA不变，不依R2结果换对手或调参数。

完整报价及计费上限3.6275 GPUh，现最新已验池实结106.722650231/113、余6.277349769、预留0；CPU部署未产生GPU预留或实费。通过真实九命令与独立接受后，重新核对完整v2余额、UUID/显存/进程/锁及独占资源，再按用户严格小于12 GPUh自主规则唯一派发。N08真实启动后约2小时技术检查、4小时完整验收，绝对时刻由实际launch确定。

## CPU查收命令

```sh
.venv/bin/python scripts/capture_wc_paper_N08_production_cpu_r1.py \
  --launch-ref reports/wc_paper_N08_full40_actual_production_CPU_R1_launch_20261017.json \
  --output reports/wc_paper_N08_full40_actual_production_CPU_R1_collection_20261017_1328.json.gz
.venv/bin/python scripts/accept_wc_paper_N08_production_cpu_r1.py \
  --capture reports/wc_paper_N08_full40_actual_production_CPU_R1_collection_20261017_1328.json.gz \
  --output reports/wc_paper_N08_full40_actual_production_CPU_R1_independent_acceptance_20261017.json
```

若仍为原CPU在途，按剩余工作量另约一次后结束，不循环查收；失败或缺失保持，不能直接派GPU。若只是本地解析问题，只处理保存的原件，不因此再次SSH或重派原CPU。

## 本地缓存恢复的范围

首个本地入口在到达SSH前因iCloud卸载源码产生`inspect.getsource`错误，原失败保留。随后使用同一已推送Git源码导入工具，按实际依赖恢复153份本地源码、228个已提交Git对象及原7.4MB历史包的本地缓存；历史包SHA1已核对，源码、Git历史和数值算法字节未修改。

本地宽范围元数据备份下载已停止，仅停止本任务拥有的临时Git读取进程；其临时partial保留，服务器任务、CPU和任何科学实验均未停止。实际部署只使用原完整N08 payload，不能把本地缓存问题计作方法负结果。

F/B关闭，P/新W3增强后排，N09/N10未启动。CPU验收后继续N08，无需重复询问已明确授权的完整小于12 GPUh卡。
