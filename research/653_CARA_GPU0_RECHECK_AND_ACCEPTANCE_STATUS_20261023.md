# GPU0实时复查与验收状态

用户要求核对GPU0并验收实验。本次实际观察显示GPU0仍被BeamNG使用，完整准入唯一未满足项为`GPU_BUSY`；没有提交价格补测GPU任务。

## 本次实测

- [12:51:50四卡资源与原价格stage句柄](../reports/wc_policy_price_refresh_user_GPU0_resource_20261023_125149.json)：GPU0显存4523 MiB、利用率58%，PID731146为BeamNG；GPU1/2/3仍分别有PID848533/848534/848535。低利用率不能当作空闲。原价格stage没有intent、launch、guardian或admission-failure句柄。
- [12:52:14进程归属](../reports/wc_policy_price_refresh_GPU0_owner_20261023_1252.json)：PID731146，UID1000、账号`user`，start_ticks945323552，状态R；可执行文件为`/data20t/shentong/BeamNG.tech.v0.35.5.0/BinLinux/BeamNG.tech.x64`。账号与路径不能单独确认实际操作人员，该进程不是注册的CARA runner。
- [12:52:26完整只读GPU0准入](../reports/wc_policy_price_refresh_GPU0_user_full_preflight_20261023_1252.json)：重新计算价格CPU独立接受，核对冻结源码、注册、原参照及预算，唯一失败条件为`GPU_BUSY`。此时该进程显存4693 MiB，模式Default，无MPS；磁盘剩余135296770048字节，MemAvailable66910056448字节。两次显存值属于不同采样时刻。

没有获取sudo凭据、改GPU模式、干预进程、写预算预约或提交GPU。预算仍为已用125.646551890291 GPUh、旧两卡未知责任预留16.5、可用83.853448109709、总上限226。

## 哪些已验收，哪些待运行

原1624完整数值、Native控制与实际6.900543598864 GPUh费用已接受，保留[原完整接受](../reports/wc_policy_assets_full1624_fourcard_GPU_accepted_20261023_0826.json)，不重复派发或收件。原动作价格受到同GPU竞争影响，仍不能作为干净价格。

独立价格补测的[完整生产CPU接受](../reports/wc_policy_price_refresh_full1624_CPU_accepted_r1_20261023.json)在本次准入中复核通过；冻结生产stage与10路径/1624正式格/24360读出/11.5 GPUh上限不变。GPU提交仍为0，因此目前没有新的价格GPU终态可验收，硬件独占尚待空闲卡实际验证。

[652的P1/P2等待期准备](652_CARA_PG_P1_P2_CPU_PREPARATION_AND_HANDOFF_20261023.md)保持，包括SELECT曝光核查、历史窗口诊断接口和少步Native对照设计；这些不替代未来PG生产CPU及整卡报价。现有`cara-bank24-2`仍于13:30作fresh资源复查，有空闲才硬独占单次启动并按实际启动时间安排半程与全程；不新增重复检查。
