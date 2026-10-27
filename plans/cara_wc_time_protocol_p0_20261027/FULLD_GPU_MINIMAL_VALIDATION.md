# 三臂最小真实GPU验证预注册（未运行）

范围为A阶段12条诊断：前两旧CAL × Native / WC-wrapper-allD / WC-README × timing OFF/ON，外加A阶段6warm的相关预热；不临时添加重复。单一服务器、单一独占GPU、相同真实Cosmos权重和生产guarded入口，完全相同条件、初噪声、scheduler、dtype、attention/offload。

验收：逐步guided输出、最终latent、decode RGB、RNG状态与双CFG action trace；同臂OFF/ON必须完全一致。Native与allD初噪声/条件一致、36更新/72调用、allD双支全D、最终latent/RGB一致。默认严格相等；若真实后端非确定导致不等，登记失败并定位，不在看到结果后放宽容差或删异常。编码video hash作为单独诊断，不能用容器元数据差替代RGB比较。README允许相对Native有缓存偏移，但自身OFF/ON不得改变数值。

最小验证同时需要真实同步、异常/拒绝终态、还原patch、缓存request reset与source身份。若数值或身份失败，停止后续校准，不把历史全部偏移归因缓存；费用按已执行实际结算。CPU相等不代表GPU通过。

实际GPU运行尚未授权。本文件没有派发命令。GPU准入须一次性提交A+B完整报价、评分CPU预算、保护最终确认预算与可用独占卡，并恢复所有已有intent。严禁两台同时跑同一张卡。
