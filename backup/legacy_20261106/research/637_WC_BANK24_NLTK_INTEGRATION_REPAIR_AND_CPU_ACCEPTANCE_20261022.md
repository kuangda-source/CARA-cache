# 四卡 BANK24 NLTK 接入修复与实际 CPU 验证（2026-10-22）

用户要求先修接入。已在四卡服务器部署固定资源与新入口实现，实际 Cosmos Blocklist 的六条冻结提示词检查通过。本次没有派发新的 GPU 实验。

## 原任务实际终态

15:46 的 BANK24 原运行 `e6c04f54-dac1-476d-9c53-3bc4ff6fc253` 已于 2026-10-22T15:51:34+08:00 退出。原 runner 为 `SCOUT_TECHNICAL_STOP_COMPLETE_SCOPE_RETAINED`，首次 warmup 在 `nltk.word_tokenize` 处失败，未得到新视频或质量结果。原 first-row RUNNING 是保留的异常现场，不能解释为任务仍活。实费 0.075736525161 GPUh（272.651491 秒），原账单及 post 失败全范围原件保留。此前 636 的“运行中”描述仅对应 15:48 的历史观察。

根因为 NLTK 3.10.3 的路径安全检查：HF snapshot 内的 `punkt_tab/english/collocations.tab` 是指向同一模型库 `blobs` 的软链接，解引用后超出了 NLTK 数据根目录，触发 `PermissionError: Security Violation [pathsec.open]`。

## 已部署修复

代码已先发布为 `a53fcf79b6dd23a1fe61dcee00accf6b61901da1`，再部署到 `/data20t/gaokuangda/worldcache_workspace/bootstrap/wc-fourcard-nltk-resource-fix-r1-20261022`。

- 以 Guardrail revision `d6d4bfa899a71454a700907664f3e88f503950cf` 为准，冻结 75 个文件、25,793,544 字节的完整 SHA-256 清单。
- 将同样字节物化为 `/data20t/gaokuangda/worldcache_workspace/runtime-resources/nltk-guardrail-d6d4bfa8-r1`，文件只读，无软链接；不改原 HF snapshot / blobs。
- `process_environment` 显式注入该目录为 `NLTK_DATA`。派发器和 supervisor 均在 GPU 资源/预算操作前核对实体目录、精确文件清单、清单哈希及每件字节；supervisor 还核对实际进程环境绑定。
- 不降级 NLTK、不改路径安全校验、不关闭 Guardrail。原失败 stage 与旧 CPU 证明保持原样。

清单 SHA-256：`d43349c4e6b5e31d4f34d600f21c8d49d94cf35b63bd9bb50b05341a37a07571`。

## 实际验证

2026-10-22T16:32:28+08:00 至 2026-10-22T16:33:13+08:00，使用原固定容器镜像、原 Python 3.10 环境和 Cosmos runtime，实际调用新入口生成的环境；2 CPU / 4 GiB，网络关闭，workspace 只读，GPU 隐藏，无 CUDA 初始化。

- 实际 NLTK 英语分词与 WordNet 词形还原通过。
- 实际 `Blocklist` + `GuardrailRunner` 接收原 BANK24 配置的六条完整提示词，6/6 通过；原拦截词表的拒绝对照通过。
- 本地 8 项资源测试、20 项执行链回归、16 项容器生命周期回归全过。
- 独立收件核对 14 项通过，部署的 13 件 payload 与已发布提交逐件一致；75 资源全哈希复核，CPU 容器已移除。
- 7 件原终态原件哈希不变，权威账本 SHA、mtime、大小不变；新增 GPU 提交 0，新增视频 0。

完整机器可读回执：[接入修复与独立验收](../reports/wc_four_card_BANK24_NLTK_integration_repair_R1_20261022.json)。服务器回执 SHA-256：`29900a992a9da8083cd078ce232ea06dcefb56779bc7afbabced01413105f03f`。

## 后续入口

这次接受的是 NLTK / Blocklist 接入，未执行神经 Guardrail、视频生成或新版完整生命周期 CPU。正式重跑必须建立独立 attempt / output，并让新 source 的完整 CPU 注册绑定新生产脚本；原 `6d9cd494` 的 34 项 CPU 证明不能直接覆盖本次变更后的 payload。旧 R2 stage / 输出 / 派发 fence 只可收件与审计，不覆盖、不清零、不回放。

重跑仍保持原 6 请求 × 3 方法、18 正式 + 6 warm、864 pairs / 1728 CFG、四 CAL 固定 gate / DEV 不拟合及累计预算。按原批准与当前资源接续，不缩成小实验，也不将接入 CPU 通过记为科研 GPU 成功。原 19:17 / 23:01 任务仍指向旧句柄，其收件必须按失败终态理解；本次未改这些自动化。
