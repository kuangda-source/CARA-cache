# 接续说明：2026-11-06 主线归档

先读 [README](../../README.md)、[主线机制](../../docs/MAINLINE.md)、[当前状态](../../research/02_CURRENT_STATE.md) 和 [最终原始报告](../../reports/cara_primary11_r1_20261106/REPORT.md)。

用户已知仓库公开，明确要求直接推送最新结果，再保留主线、将旧方向放入 backup。最新结果已先以 `8671422cd2c497d0cb7ab42084b3e09f5f84dc81` 正常快进到远端 main；随后在 `codex/mainline-cleanup-20261106` 整理目录。没有重跑实验、改写运行逻辑或批准 PR。

主线为 frozen generator v1 的 D/light-C 预算规划；R18C 为主点，R16/R21 为辅助，F17 为强对照。已授权 11 项队列全部终结，8 个共同可评输入与固定九输入交付率分开报告，原完整九/十输入终点不可评价。

全部旧 tracked 文件按 [ARCHIVE_MANIFEST](../../backup/ARCHIVE_MANIFEST.json) 留存：13191 个移到 `backup/legacy_20261106/`，893 个保留原位置。源码、冻结清单、历史回执保持原字节。少量旧名公共依赖保留，依据在 [依赖清单](../../docs/RETAINED_DEPENDENCIES.json)。

原公开推送拒绝记录是拒绝当时的历史回执；后续明确授权及成功发布见本交接和 Git 提交，不能回写原拒绝原件。HTTPS 缺认证的尝试未执行写入；成功发布使用仓库原有 SSH 认证。

原导航生成器、project_status、paper registries 和模板已整体归档；当前不要运行旧生成器覆盖新主线导航。使用 `python3 tools/verify_repository_layout.py` 核验当前树。

PR #3/#4、历史分支与 Git 历史均保留，不在本次操作中批准、合并、删除或强推。后续研究只是建议，P/S/Q、ORR 和其他模块暂停。
