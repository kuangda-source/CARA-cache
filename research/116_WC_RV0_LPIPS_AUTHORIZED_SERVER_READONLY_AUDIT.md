# LPIPS指定脚本服务器CPU只读审计通过

2026-10-04。用户直接允许将`audit_wc_rv0_lpips_resource.py`经现有SSH传到`/home/gaokuangda/data/gkd/worldcache_omr`，执行对`.sync/wc-rv0-lpips-resource-v2`的CPU只读文件及哈希审计。本次只传送这一文件，未传送其他私有运行/监督/评分代码。

[完整回执](../reports/wc_rv0_lpips_resource_server_audit_v2_20261004.json)状态`AUTHORIZED_LPIPS_CPU_READONLY_SERVER_AUDIT_PASS`，exit0。远端脚本SHA为`6a54e5987944e2265fddfd9f5b7c18636d933a82850230ca3d8d82691fe4284a`，与本地和此前待审脚本完全一致；目标仅新增该审计脚本，已有资源没有修改。调用既有Cosmos Python，关闭CUDA可见设备和bytecode写入，55秒timeout，审计含SSH耗时1.478912秒。

实际审计读取CPU回执原件、协议源文件、公开PyPI元数据、lpips0.1.4 wheel及其53763 bytes长度、四份已装包源码、AlexNet backbone与v0.1 linear两份权重。核对路径origin、SHA、协议、既有合成图/重复/四拒绝检查以及预算变化来源。服务器返回原件SHA `796c9ef2762b90c8ebea7e12c5382be64bcc8848f74097a510125dafbc6407ff`，协议源SHA `453660dc89595548f808892e3f81e47c13b4bb169d6d104f075db88868eadf60`，与[115的原生哈希本地审计](../reports/wc_rv0_lpips_resource_native_audit_v2_20261004.json)完全匹配。资源/权威预算/直接授权共12个文件的前后SHA逐个相同。

这是指定脚本在实际服务器上的只读文件/哈希审计。审计脚本没有导入Torch或执行LPIPS模型前向；引用的7.315361秒预训练CPU合成图结果是既有V2回执，本次没有重跑或冒称新的全视频验证。真实C/D视频评分、同预算标签、Head、CONF和质量结论仍未产生。GPU提交0、GPU费用增量0、共享环境未改。

现有账本保持13GPUh累计上限、used11.022315686839217、45jobs、无inflight，前后字节不变；没有用旧104单次身份再提交任务。此直接授权解决了历史审批记录中**该LPIPS审计脚本**的传输许可。新W3生产/监督/视频读取/评分代码的同步不在本次许可范围内；[115未选草案](115_WC_RV0_EXECUTION_DRAFT_AND_NATIVE_READONLY_AUDITS.md)与其源码哈希、实际主机CPU/解码/部署待验状态保持。科学goal仍active，本次指定审计已完成。
