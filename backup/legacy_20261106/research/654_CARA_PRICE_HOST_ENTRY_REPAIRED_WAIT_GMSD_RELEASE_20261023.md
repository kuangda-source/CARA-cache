# 价格补测host入口已修复，等待GMSD释放GPU3

用户授权有空闲卡时验收并独占一张。12:58 GPU3确实空闲，完成CPU、源码、原参照、预算和资源准入；首次host入口在CUDA与GPU模式改变之前失败。启动器修复已完成，随后GPU3被另一项GMSD实验占用，目前没有CARA价格GPU运行或新增费用。

## 空闲准入与原始失败

[12:58:23资源](../reports/wc_policy_price_refresh_fresh_user_resources_20261023_125822.json)显示GPU3为24 MiB、0%且没有计算进程，其他三卡有任务。[完整准入](../reports/wc_policy_price_refresh_GPU3_idle_preflight_20261023_1259.json)通过。

[原启动意图](../reports/wc_policy_price_refresh_full1624_GPU_launch_r1_20261023_1300.json)的launch ID为`895d66c7-5e95-42b3-bbff-0f78766eb424`，实际host进程于12:59:04.947620启动，PID941408/start951660830；文件名1300仅为标签。这是host派发，未完成硬件准入。[原件恢复](../reports/wc_policy_price_refresh_original_handle_recovered_20261023_1300.json)及[首次准入收件](../reports/wc_policy_price_refresh_full1624_GPU_admission_r1_20261023_1300.json)证明该进程已退出，没有guardian状态文件、容器、runner、GPU预约，UUID锁可取得、模式仍Default。

[原日志](../reports/wc_policy_price_refresh_original_host_entry_diagnostic_20261023_1300.json)表明子进程使用`sys.executable`直接调用原生Python ELF，绕过已有的glibc兼容wrapper，动态加载器报告GLIBC_2.32/2.33/2.34/2.35缺失。Python主程序没有运行；确认本次GPU提交0、实际GPUh0，账本未写入。原launch、intent和失败日志全部保留。

## 可复核的接入修复

只修改本地控制器和独立接受器，冻结生产source `cecba6647fcc626887761961fc7215c6fe1afa8b`、原stage、注册、采集代码、scope和11.5 GPUh上限均不变。控制器改用已接受并核对wrapper/Python/loader/manifest SHA的`bin/python3`启动guardian。

新增`resume-host-entry`只允许恢复同一个已知解释器前失败意图：核对原进程已退出、原失败日志SHA、无guardian/容器/输出/账本job、原授权身份、完整CPU和fresh资源。若已有恢复intent或恢复launch，只能recover；不删除原intent，不调用第二次launch-gpu。真正恢复时新增独立恢复intent/日志/launch，原失败原件不变；独立终态接受额外核对原始/恢复身份与双SHA。

[真实wrapper CPU复核R2](../reports/wc_policy_price_refresh_host_entry_wrapper_actual_CPU_r2_20261023.json)实际使用同一子进程启动调用，加载冻结guardian入口并验证生产源码/原参照，Python3.10.19、Torch2.7.1+cu128、CUDA未初始化、无模式或账本写入。第一版诊断错误地要求导入闭包中完全没有torch，因CPU合法导入torch而失败；其[原件](../reports/wc_policy_price_refresh_host_entry_wrapper_actual_CPU_20261023.json)保留，R2检验实际CUDA初始化状态。[37项相关CPU检查](../reports/wc_policy_price_refresh_entry_recovery_controller_CPU_20261023.json)全部通过，包括有旧GPU输出/预约/活进程/容器或未知检查时拒绝恢复、已有恢复intent不重复启动，以及独立接受不能隐藏先前GPU使用。修复版本`03f702e2`已发布后才尝试恢复。

## 当前资源与后续动作

[13:03:48恢复前检](../reports/wc_policy_price_refresh_full1624_GPU_recovered_launch_r1_20261023_1304.json)返回`GPU_BUSY`，没有写恢复intent或取sudo凭据。该文件不是实际恢复启动原件。[13:04:36四卡复查](../reports/wc_policy_price_refresh_recovery_resource_recheck_20261023_130436.json)中四卡均有进程。GPU3新增PID942555/start951670638，536 MiB，UID0；[13:05:02归属](../reports/wc_policy_price_refresh_GPU3_new_context_identity_20261023_1305.json)确认其13:00:42启动，属于`gmsd-e07-postupdate-r1-20261023`容器的`evaluate_postupdate.py`，不是CARA的guardian或runner。没有中断该任务或修改忙卡模式。

预算保持已用125.646551890291 GPUh、旧未知责任预留16.5、可用83.853448109709、总上限226。原1624完整接受与6.900543598864 GPUh结算不变；新价格生产CPU仍完整通过，但真实价格尚未产生。

现有`cara-bank24-2`于13:30接续：先恢复读取原意图及任何后来的恢复句柄；若GPU3空闲，使用`resume-host-entry`、本次真实CPU证明和原失败SHA继续同一任务。硬件EXCLUSIVE_PROCESS和唯一原runner上下文通过后，才称为GPU准入成功，半程/全程以实际恢复启动时间重新安排。其他卡空闲不能绕过原UUID绑定。价格完整接受后再接652中的PG-P1/P2准备；不从部分结果调参。
