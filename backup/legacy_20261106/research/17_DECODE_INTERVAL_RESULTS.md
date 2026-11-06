# 两个新进程的阶段诊断：首个差异位于decode返回边界

2026-09-30，结论：`FIRST_DIFFERING_BOUNDARY / decode_output`。这是工程复现区间定位，不是根因确认或候选质量结果。

同一源fa042d3、官方WC、AV工程输入/seed0、原36时间点/72CFG/WC70，两进程分别只生成一次。监督任务stage-r2，两child均exit0；317.200334秒与317.030196秒，合计634.230530秒/0.176175147GPUh，未超过共享900秒截止。原进程均已退出、锁空闲，GPU1为24MiB/no compute apps；两段监控均无观察到外来计算进程，峰值25806MiB。哈希源码与两个视频在远端重验通过。

| 边界/对照 | 结果 |
|---|---|
| 72次net输出、38full/34skip、trace、最终WC缓存 | 完全相同；也与旧W1默认/最近pair官方轨迹相同 |
| 采样配置、记录的运行环境/源码/输入与编码参数 | 相同；输出目录不同且各自隔离 |
| 最终sample与decode输入 | 同一shape/dtype与SHA256 `ee1d0e6c9c037844a6ba16680fc7800ca85991092474b3db99352d51f3011545` |
| decode raw输出 | 不同：A `30ef5976…`，B `d5b47a13…`，首个不同见证 |
| guardrail输入/输出 | 两进程之间不同；每个进程内部输入/输出完全相同，检查仍启用并通过 |
| save输入与MP4 | 均不同；MP4分别`96c2d86b…`、`febcf27c…` |
| CPU完整RGB解码 | 各93帧432×768；两进程的93个帧hash全部不同，时间戳相同 |

观察到的cuDNN benchmark=true、deterministic=false、TF32=true、deterministic_algorithms=false保持原值。它们是待检验线索，不足以证明cuDNN算法选择为根因。当前未比较decoder实际参数/buffers/scale的运行态hash，内部权重/状态及具体算子仍UNKNOWN。源码、checkpoint路径与资产manifest相同，不等于已现场重算全部权重哈希。未保存中间bulk tensor。

r1最初监督脚本复用了输出目录。首进程见证成功；第二child在0.149秒时显式终止自有进程组，未加载模型。该失败对照不能当两进程通过，成本0.086891471GPUh一并计入。已修正目录并加入真正创建各自video目录的模拟child回归检查；本机及Linux针对性13项CPU检查通过。r1原始回执/取消理由完整保留。

累计预算1.823217769/4GPUh，剩余2.176782231GPUh，无在途任务。继续WorldCache工程与数值诊断，默认/recent scalar和shrink仍NO_GAIN_IN_SCOPE，不送入闭环；不是整个方向的否定，也没有新方法/质量正结果。无需引入人评。

依据：[两进程汇总](../reports/stage_r2_summary.json)、[A](../reports/stage_r2_stage_a.json)、[B](../reports/stage_r2_stage_b.json)、[监督](../reports/stage_r2_supervisor.json)、[终态审计](../reports/stage_r2_audit.json)、[预算](../reports/budget.json)。
