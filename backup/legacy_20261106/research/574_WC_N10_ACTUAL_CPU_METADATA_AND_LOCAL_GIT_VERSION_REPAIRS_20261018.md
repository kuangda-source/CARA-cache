# 五模型CPU失败已定位，限定修复通过58项本地控制

2026-10-18。**两次被拦截事件来自同一个本地依赖检查，不是模型请求下载权重：timm／PyIQA导入wandb，再由GitPython执行本地`git version`。** 原五模型CPU结果1／5接受及全部失败保留；新完整CPU尚未派发。

[两次独立导入诊断](../reports/wc_N10_dependency_import_network_event_diagnostic_20261018.json)复用原注册SHA和原进程级禁止网络函数，仅以事件列表的append记录调用栈。timm与PyIQA各一个全新CPU子进程，网络及权重加载继续禁止，0模型实例／0GPU／原stage不写；两者都在GitPython的`Git.refresh→version→Popen`链触发原`git`下载命令拦截。

## 修复范围

1. **DINO：** 官方原 `Resize(size=224)` 保留宽高比，432×768输入实际得到224×398；独立验收的输入描述从误写的224×224修正为真实形状。官方transform、输入图像、权重和模型均未改动。
2. **AMT：** 对实际model_source和注册根作规范路径解析，再按注册payload的相对路径和原SHA验证，解决`utils/../networks`的等价路径。越界路径及错误源码SHA仍拒绝；探针也保存规范路径。
3. **导入保护：** 仅允许显式argv为`git version`或`git --version`（限定标准git路径、无shell、无其他可执行覆盖）的本地只读查询，单独记录`allowed_read_only_process_probes`。其他Git动作、wget／curl／pip及Python网络连接仍拦截。不是把联网事件删掉或放宽成“联网也算通过”。
4. **失败诊断：** 无论成功与否都保留实际checkpoint／state_dict加载记录；若模型输出已返回再失败，也保留partial actual。被拦截事件新增调用栈，以便直接定位原原因，不改变失败接受条件。

## 本地接受与剩余

[58项本地接受](../reports/wc_N10_actual_CPU_R1_scoped_repairs_local58_20261018.json)＝原54相关控制＋4项实际修复控制，零失败。新增控制使用原R1真实DINO／AMT／RAFT数据检验实际接口；伪造DINO方形输入、AMT越界或错误源码SHA仍拒绝；本地git只读版本查询被允许，clone／fetch／config／额外参数、shell、可执行覆盖及socket／下载全部拒绝。

这证明了适配范围与保护边界，不代表新五模型已接受。下一步以新Git source和独立stage重做**完整五角色真实CPU**，保留同一216官方源码、12 DINO源、固定五权重、BPE、FP32/eval及输入。新资源不下载，不使用子集，不触发视频评分；全部五项独立接受后才接完整960指标位置。

连续修正88 CPU原source57b4c19／PID1685865及02:14半程、02:20终态不改，原运行stage不受本地N10源码修复影响。N09两GPU外部占用、原0GPU准入与费用保持；新GPU测速时不并发重CPU。累计cap226及全部历史账不变，本轮0GPUh，F/B关闭。
