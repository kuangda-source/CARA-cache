## 02:00独立修复安装与请求已过；解码验证脚本修复以新R3补验

原R2已终态，前六命令全0：独立基础复制、四官方wheel安装、cosmos-cuda、依赖声明对齐、uv pip check、真实Cosmos CPU请求导入均已通过。第七命令在实际解码前触发SyntaxError：验证脚本全局VIDEO占位符替换误伤了输出标记，属于新增验证代码错误；失败原件与接受false保留，不能称完整环境通过。新R3用独立job和GitHub新source，以命令行参数传视频路径，补实际CPU解码/原冻结guarded推理导入/freeze；只读复用env-r3，不重装/复制基础或修改原R2。新测试代码编译与占位符回归已通过，真实R3尚未启动。原BANK24两卡02:30与完整1624批准/前置保持。

## 原01:50完整收件已完成，独立修复最终查收重估为02:00

原R1终态实际01:49:46.301收件（已过01:49:05.400最早时点），原PID/自身容器均退出、source/manifest/11runtime/原生库SHA一致；13命令中11项0，两项失败完整保留，离线接受为false，原worldcache-3完成删除。独立R2原01:44终态时点的回执实际01:44:43.215保存：仍在安装本地官方wheel，已完成基础独立复制340.728秒，decord payload/runtime SHA保持，未发现错误。此为RUNNING回执，不送终态接受、不覆盖；按安装与后续CPU导入/解码一次重估02:00，worldcache-2已改约新terminal_recheck_20261021_0200.json，原launch/worker不改。两卡02:30资源检查保持。

## 2026-10-21 01:37四卡独立CPU修复已启动，半程正常，01:44完整查收

官方四wheel已在四卡逐SHA核对，GitHub source32062b18的独立修复于01:37:25.700单次启动PID330428/start930290906，worker97c7af2e/manifest9574f4a5。原env-r2/R1 job及项目c9a2f95b保持；新env-r3仍在复制已验基础。实际01:40:46.765半程源/句柄一致、无错误，未提前完整接受；本次半程监控已完成删除。新worldcache-2已约01:44终态（最早01:43:25.700），原R1 01:50失败收件与两卡02:30资源检查保持。0GPU/模型加载/账本写；实际修复CPU、模型/GPU兼容仍待。

# 四卡环境故障：官方wheel转运与独立CPU修复

人类在00:56直接要求解决完整环境故障。本修复仅准备四卡环境；原双卡BANK24、完整1624采集卡的冻结范围、CPU/gate、上游顺序和具体12GPUh批准保持。

## 原故障与依赖边界

原R1已结束，结果SHA为28c07df2fd0ad7004f66a275b71f5efccce59be3dcea6588ca48cc4ec8cd4237。Transformer Engine 2.2/cu128/torch27从官方GitHub Release下载三次重试后超时；随后Cosmos请求导入失败。源码检查另确认原显式安装步骤遗漏同版本cosmos-cuda包，不能只重试下载或跳过官方检查。

原环境只读metadata检查还识别两项打包问题：cosmos-predict2声明cosmos-oss==0.1.0，而同一固定源码树实际包版本为1.4.0；decord官方py3发布文件内部仍标cp36。实际x86_64/glibc2.36/Python3.10的decord CPU导入正常，但不能把它直接充完整解码验证。

## 独立修复方案

- 从官方发布源取得FlashAttention2.7.3、NATTEN0.21.0、Transformer Engine2.2的cp310/cu128/torch27二进制wheel，另补匹配Torch2.7.1的xFormers0.0.31；逐项使用官方SHA256校验，再转运到本人数据盘，服务器从本地文件安装，不依赖其GitHub Release下载链路。
- 将原已安装基础复制至独立envs/wc-cosmos-py310-cu128-r3。原env、R1 job/source/log/result不改，不重复基础Torch安装。
- 从原固定源码安装同版本cosmos-cuda；只在新runtime打包overlay中修正依赖版本声明，11项关键执行源码SHA逐字节保持。decord只修复制后环境的WHEEL/RECORD声明，37项官方decoder payload SHA全部保持；实际四帧合成CPU解码另验，不作研究结果。
- 隐藏GPU、2CPU/16GB、只读root、复用同一固定容器和数据盘原生库，不改宿主机包/驱动/daemon，不加载模型或写GPU账本。
- 实际检查完整依赖、普通Cosmos请求导入、原生产CPU边界下的推理模块导入、精确版本/freeze、原环境metadata未变、原PID/容器退出。接受只代表环境CPU准备，不代表新机生产CPU、模型资产或GPU驱动兼容。

配置与实现：manifests/wc_four_card_environment_isolated_repair_recipe_r2_20261021.json；scripts/repair_wc_four_card_environment_r2.py；scripts/analyze_wc_four_card_environment_repair_r2.py。官方wheel和decord来源/SHA单独登记在本轮manifests下。私有transport只在本地恢复原授权，不导出凭据。

当前为修复准备/转运阶段，未确认新CPU启动或通过。新job预定wc-fourcard-env-repair-r2-20261021；真实launch后+120秒技术半程、+360秒完整查收各一次，已有句柄/未知派发只恢复，不重放。原R1的01:50完整收件及两卡02:30资源任务保留。
