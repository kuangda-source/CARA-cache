## 2026-10-21 四卡依赖故障已修复；完整推理仍缺固定Guardrail模型资产

官方四扩展wheel已安装并逐SHA核对，匹配cosmos-cuda、依赖声明和decord元数据修正完成；实际uv依赖检查、Cosmos CPU请求导入/精确版本与四帧合成CPU编码解码通过。29项组件范围独立核对全过，196份实际已装依赖metadata已保存。原R2验证脚本的VIDEO占位符错误保留为失败，由GitHub source e8f80c6c的只读R3实际补验解码；未重装原基础或修改旧stage/env。完整推理导入另在固定Cosmos-Guardrail1 revision d6d4bfa899a71454a700907664f3e88f503950cf的离线缓存缺失处停止，R1/R2/R3完整接受仍false；只接受已修好的依赖组件，不称完整环境/新scope生产CPU/GPU就绪。原env-r2、项目c9a2f95b、11关键runtime、37项decoder payload及原失败结果保持；修复和补验PID/自身容器均退出，0CUDA初始化/模型加载/GPU/账本写。下一步仍需固定模型资产、GPU兼容及新机scope生产CPU/报价/共同v2；原BANK24优先和两卡02:30资源检查、完整1624具体12批准及上游条件保持。已完成的四卡半程/终态自动化均删除，缺模型不重试安装。

## 实际修复与验收边界

原故障是官方GitHub Release下载超时、显式安装遗漏cosmos-cuda，以及cosmos-oss/decord两项打包声明不一致。四个固定官方wheel合计1,274,999,302字节，使用官方SHA256校验并转运到数据盘；原R1全部失败原件保留。

R2 source32062b18在独立env-r3安装成功，前六条实际命令全0。原第七条解码测试代码全局替换VIDEO误伤输出标记，导致SyntaxError，实际未解码。R3 sourcee8f80c6c通过sys.argv传路径，只读复用相同已装环境，实际解码通过。其后推理导入需要当前未具备的Guardrail模型缓存，明确记录为资产阻挡，不绕过模型保护或声明完整通过。

当前环境路径：`/data20t/gaokuangda/worldcache_workspace/envs/wc-cosmos-py310-cu128-r3`。Torch2.7.1+cu128、TorchVision0.22.1+cu128、FlashAttention2.7.3+cu128.torch27、NATTEN0.21.0+cu128.torch27、Transformer Engine2.2+cu128.torch27、Triton3.3.1、xFormers0.0.31、decord0.6.0均由实际请求probe及最终METADATA再次核对。

环境组件接受只覆盖安装、依赖一致性、请求导入和CPU编解码。原31项完整补验协议的失败接受原件继续保留，不得用组件范围的正结果替代未通过的完整推理、模型资产或新机生产验证。

## 原件

- [R2安装与失败原件](../reports/wc_four_card_environment_isolated_CPU_repair_R2_terminal_recheck_20261021_0200.json)
- [R2完整协议未接受](../reports/wc_four_card_environment_isolated_CPU_repair_R2_independent_acceptance_20261021.json)
- [R3单次实际launch](../reports/wc_four_card_environment_validation_CPU_R3_launch_20261021.json)
- [R3实际完整收件](../reports/wc_four_card_environment_validation_CPU_R3_terminal_marker_corrected_20261021.json)
- [R3完整协议未接受](../reports/wc_four_card_environment_validation_CPU_R3_independent_acceptance_20261021.json)
- [依赖组件独立接受及模型阻挡](../reports/wc_four_card_dependency_repair_components_independent_acceptance_20261021.json)

模型接续仍按615和四卡环境计划：固定生产资产从获授权且SHA可核对的来源准备，认证文件不转运；未具备完整模型时不重试同一导入、不启GPU、不借双卡旧CPU赋予四卡通过。双卡BANK24和完整1624卡不因这次环境修复迁移或改变原冻结范围。
