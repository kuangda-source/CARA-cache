# 共享952 CPU：装饰器命名空间修复，完整R3已派发

更新：2026-10-16。N05服务器完整66、原15d77ac/1078249/1078290/post1078250和今天12:05查收完全保持；本轮0SSH/0GPUh/0预算写。

**修复的是本地CPU观察器的装饰器解包，不是采样器或缓存算法。** 原R2在进入第一条完整采样之前因`KeyError: misc`退出，失败和完整952分母保留；新R3经过新增控制后，在独立目录按原952范围单次派发，尚未接受。

## 1. 原R2终态与触发

本地提交时，普通Git状态意外显示原CPU的exit/failure文件已生成。为定位已报告的技术错误，本轮在原05:49之前只核对了一次原PID/终态与错误文件；没有循环观察，也未读取N05任何在途输出。此终态事件例外单独记录，不把它改说成按ETA成功接受。

- 原PID9614已不存在，原exit=1；source89381c1保持。
- 原CPU占用1.226805秒；错误发生在观察器获取sampler `misc`之前，未进入注册的第一条采样，0完成路径/952原分母。
- `torch.inference_mode`的外层函数使用Torch自身命名空间，直接读外层`__globals__['misc']`会KeyError。
- 修复为`inspect.unwrap`，并核对解包后函数确实来自固定runtime的原sampler文件；不改其函数体、RNG或执行参数。
- 原R2隔离source、failure、exit、事件捕获与原R1大归档均保留，不原地修改、不补部分点。

原件：`reports/wc_paper_shared_registry952_R2_terminal_failure_incident_20261016.json`及其中绑定的原exit/failure；第一次打包中断仍见472，不混为同一失败。

## 2. 新增验证与完整范围

新增单项控制用真实Torch装饰器重现“外层缺misc/解包后恢复原命名空间”，同时核对原函数co_filename。原五项seed/context/180排程/源可逆/异常恢复全部保持，六项本地控制通过，见`reports/wc_paper_shared_execution_scalar_CPU_R3_controls_20261016.json`。

新的R3仍是两flow×四Toy×17原配置×三seed的816 audit/lean＋136旧seed0控制，**952路径/32816pairs/65632CFG**。408audit/lean、136完整guided旧新桥接、实际seed/初始噪声、72Native计数、mask与owner释放均保持。最终N07的8prompt×2seed×10配置/180未选择、不缩改；本地CPU不等于最终生产CPU/真实Native/新视频结果。

## 3. R3单次派发

|项目|当前值|
|---|---|
|source|`616caef408285a0d8374692b879ee1d5b5b880f4`|
|原PID|9817，只在准入确认live|
|stage|`.sync/wc-paper-shared-registry952-local-cpu-r3-20261016`|
|封存payload|2272文件，精确Git blob与SHA256绑定|
|启动|2026-10-16T05:48:48.865855+08:00|
|预计|7—12分钟，不设CPU到时强停|
|最早查收|2026-10-16T06:00:48.865855+08:00，unix1792101648.865855|
|安排|**今天06:02一次查收**，原05:49查旧CPU已暂停|

原launch：`reports/wc_paper_shared_registry952_local_CPU_R3_launch_20261016.json`。新的R3 source与旧R2字节快照分开；只读collector在当前项目执行，不向隔离CPU改代码。

```text
.venv/bin/python scripts/capture_wc_shared_registry952_local_cpu_r1.py \
 --launch-ref reports/wc_paper_shared_registry952_local_CPU_R3_launch_20261016.json \
 --output reports/新的R3完整952捕获.json.gz
.venv/bin/python scripts/accept_wc_shared_registry952_local_cpu_r1.py \
 --capture 同捕获.json.gz --output reports/新的R3独立接受.json
```

若仍live，依据同一捕获的剩余工作量估时另约一次即结束，不循环看进度。若有新技术问题保留原失败并修复fresh版本，不把partial、五/六项标量或接口等价当完整科学接受。此CPU仅验证执行，不自动启N07 GPU、训练或新方法。

## 4. 主线不变

N05今天12:05一次完整验收后，综合N05/N06锁定N07工作点与前密C/A强对照，再依完整CPU/费用/fresh余额按原严格<12规则推进。单次>=12或余额不足询问具体整卡，不拆控制或重置48窗口。原cap104.971363333、最近实结89.486094218、N05预留9.5和可准入5.985269115快照均未重查/改写。

F/B关闭，P/T1增强后排，无新生成器训练、OMR或人评。当前有明确、已修复的CPU夹具错误；尚没有新的共享测试视频或方法质量负结果。
