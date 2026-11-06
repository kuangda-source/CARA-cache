# P 真实入口 CPU 的本地回执路径修复

P 生产 R1 在本地 `git show` 校验阶段停止：已保存的 P 独立 capture 使用绝对 `local_path`，准备器把五个压缩回执的绝对路径直接带入新 payload，Git 校验需要仓库相对路径。source `bc992cd` 的原配置／登记保持，原错误为退出 128；没有 SSH、远端 CPU 目录、GPU 提交或账本写入，见 [原本地失败记录](../reports/wc_p_reference_same_state_production_r1_predeployment_failure_20261011.json)。这不是模型或算法负结果。

R2 只把新增回执路径先 resolve 再严格 `relative_to(repository root)`，仓库外路径会拒绝；新配置、登记、生成请求目录及部署 stage 使用 R2 身份。原 444 只读字节、五读出数值、真实 runner、全部合同和 CPU checker不变。完整成本 **13.060019179 GPUh**、两 flow／8 父／32 suffix／48 点／688 pairs／1160 张量及 240 次候选恢复不变，旧成本文件按完整 JSON 相等复用，不改写 R1。

接续摘要：[360路径修复](research/360_WC_P_REFERENCE_PREDEPLOYMENT_RELATIVE_PATH_REPAIR_20261011.md)：P生产R1仅本地git回执绝对路径校验退出128、0SSH／0远端目录／0GPU，原sourcebc992cd／配置及失败保留；R2仅严格仓库内相对路径归一，新身份保留444原数值与两flow完整范围、forecast13.060019179，实际服务器CPU待。原E5继续；E3全64／复用10／补54／20加载已直接批准，待E5退出与独立验收优先执行；新P above8授权未授，预算cap保持、无人评训练，goal active。以下为历史。
