# 等待期间按序推进

用户要求按上轮顺序直接推进。本轮先完成不占用服务器计时资源的准备；当前BANK24继续使用原句柄和原20:33/次日00:17验收安排。

## 1. 完整1624独立四卡入口

- `scripts/wc_four_card_policy_assets_r1.py`：prepare、deploy-cpu、recover、capture、accept、launch-gpu。新物理run `wc-policy-interval-assets-cal4-full1624-ada-r1`，独立stage，原科学run/config不改。
- 7份生成源码可逐项还原；同一host PID容器承载原supervisor/runner并传递原flock FD。CPU隐藏GPU且项目只读；GPU按UUID绑定、原账本结算后做CPU post。原两卡CLI关闭。
- 当前包 `manifests/wc_policy_assets_fourcard_full1624_package_r3_20261022.json`。R1/R2为本地未发布的中间包，保留于ignored .sync；没有远端部署。
- 原四CAL、1624正式格、14完整路径、2030含warm格、13020读出试验、具体12GPUh批准保持。新完整报价从接受后的BANK24实际load/最长完整请求出发，保留原采集、搬运、写读SHA和完整审计项；超过12则整卡不派发，不缩格或拆卡。
- 完整新机CPU仍为原3命令：12单元、28数值路径/4060重载格/26040试验、4实际Cosmos请求与12拒绝控制；另加入实际子进程继承FD/namespace/竞争锁检查。本地测试不能替代这次实际CPU。
- 本地证据 `reports/wc_full1624_port_local_preparation_20261022.json`：11适配+5选样控制、原12采集回归通过，185overlay与1818基础输入0冲突。

## 2. CAL_SELECT 先发布规则再选身份

`plans/cara_policy_generator_20261020/cal_select_protocol_r1_20261022.json`冻结1 AV+1非AV、seed0、完整source-group排除、7份曝光清单及固定salt哈希排序。选样器只读取已提交的身份/来源元数据，不读取质量或运行在途结果；拒绝不补选。发布后运行并填写两个身份。服务器历史曝光元数据在首次端点运行前核对，当前不打扰BANK24。

## 后续本轮工作

依次补齐CAL_SELECT清单、P1费用/结果分析、强前密C/A及refresh-only/pure-proxy/同Q简单搜索接口，最后用已接受Window24全四场景结果制作机制图和方法伪代码。最终状态与运行命令将写回本文。
