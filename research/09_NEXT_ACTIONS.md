# Next actions — judge CPU r3续传live，准备后续完整性与VQA runner

1. 继续同一`outputs/w1-judge-assets-r3`：source202e21d/Linux4项CPU检查通过，三个PIDs已live验证，cap3600秒CPU-only，partial850MiB/未完整。原r1失败/r2timeout终态已审计，不重启旧任务；不改在跑CPU源码/manifest，不据旧RUNNING或观察失败重复提交。[启动](../reports/w1_judge_assets_r3_launch_20261001.json)/[观察](../reports/w1_judge_assets_r3_live_observation.json)。
2. 终态后核验PIDs退出、CPU lock释放/source一致，归档原supervisor/downloader/实际wall。若exit0，用`verify_public_assets.py`与[官方hash manifest](../manifests/w1_development_judge_integrity.json)逐文件Git/LFS digest核验；只有完整验收才能称模型资源齐备。匿名镜像仅运输路径；partial或prefix一致不代替全文件hash。
3. [开发VQA卡](26_W1_DEVELOPMENT_VQA_PREPARATION.md)/[输入协议](../manifests/w1_development_vqa_protocol.json)：原8/42题、单题原提示、requested2fps实际10帧、严格YES/NO/invalid bounds、robot拒绝不插补。本地7CPU和真实Linux config/processor/video输入通过，尚未VLM forward。准备runner/Linux检查，完整资产后再作加载和成本准入。
4. 后续拟GPU单batch900秒/all原8/all原题/一次load，从原余额划拨；必须fresh预算/锁/GPU准入及source hash，加载/失败/评分/flush全计费。当前原GPU累计3.612360697/4h、余0.387639303h，无GPU在途，不自动扩额。
5. 固定重放8技术轨迹/7接受1robot拒绝、MUSIQ3升4降/mean delta+0.004254295，无整体/物理质量或clean速度正结果，暂不加W2。小2B不是235B标准Joint/独立确认。仍需标准语义/物理、clean重复配对和独立确认；资源不足时先形成具体方案再交用户。不引入非必要人评/付费/训练；代码/回执/docs每次同步GitHub。
