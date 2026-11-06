# Q5 Native50 参考组件双端 CPU 接受

2026-10-30。Q5 唯一请求50步网格的 Native 参考与 all-D 数值控制，已在四卡 Ada、两卡 A6000 主机的 GPU 隐藏容器中完整验证并正常退出。实际 UniPC 网格为51次更新、52个 sigma，每条成功路径实际调用102次 CFG 模型；两端网格逐值相同。每端48条成功小张量路径与12次预定失败控制通过，新增 GPUh 和账本写入为0。

## 范围与实现

原 Native 入口只接受请求18至35步，完整 all-D 请求也固定35步/36次更新。新组件在独立命名空间中仅替换 Native 范围检查和完整请求的数值边界；原 Requests 的调用字节码相同，原 Native、clean 模块及稀疏策略入口保持原字节。源码逆变换的三项本地控制验证了这些修改点，并拒绝父函数对应位置变化。

新组件只允许请求50步的 Native/all-D 角色，不开放 sparse51。原36更新生产策略仍拒绝51更新 profile；原 Native 入口仍拒绝50步。GPU 正式候选和 S 规则尚未映射到该新网格。

[启动前 CPU 意图](../plans/cara_next_stage_20261028/mainline/r2/Q5_NATIVE50_CPU_FRAGMENT_R1.json)从派发前任务私有意图原字节归档，绑定四份新增源 SHA。两端复制各自已接受 F18 CPU 父 stage 的1045份 payload，只增加四份本组件源；原12份 runtime 源哈希不变。新 CPU 接受器另行绑定父接受回执、原启动、registration 与完整 CPU proof。

验证使用原 CLI、真实模型模块、CFG、UniPC 和 WorldCache 方法体，小张量网络、条件/噪声、准备、解码和写出是明确声明的 CPU 替代。不加载 Cosmos 权重或真实 VAE，不产生真实视频质量、GPU速度或 Q5 科学结果。

## 完整 CPU 矩阵

四个旧 CAL 输入，各自运行 Native50 与 all-D50，每个角色分别计时 ON、OFF、审计 ON：每个 flow 共24条成功路径。两角色各做文本拒绝、解码失败、写出失败，共六次失败控制。两种原 flow 模式合计每端48成功、12预定失败，共60次小张量尝试；这不是 Q5 GPU 的物理范围。

实际验证了51次更新及首末真实 block 各102次调用；Native 不安装缓存，all-D 动作为51个 DD。每个输入跨角色和 ON/OFF/审计模式的最终 latent、RGB、RNG 逐值相同，全部51份审计 guided 输出相同。clean 路径研究复制、哈希与检查点为0；失败后原状态恢复，禁止对同一尝试重放。

实际 timesteps 为51个整数，包含两个993，这是原调度器量化所得，未去重或修改；sigma 严格递减并追加0，共52个。完整数值保留在[双端接受回执](../reports/cara_Q5_Native50_CPU_component_accepted_r1_20261030.json)，不会把请求50步误记为50次更新或100次 CFG 调用。

## 原句柄与终态

| 主机 | 原 CPU 容器 | client PID / start ticks | 工作者墙钟 | 进程 CPU 时间 | 终态 |
|---|---|---|---:|---:|---|
| four_card | cara-Q5-Native50-CPU-ada-r1-20261030-cpu | 4151718 / 1012434476 | 366.645s | 227.258s | exited / 0 |
| two_card | cara-Q5-Native50-CPU-a6000-r1-20261030-cpu | 2000210 / 663434278 | 208.108s | 204.702s | exited / 0 |

两端均为1 vCPU、4 GiB、无 swap、CPU26、无网络、只读根文件系统、DeviceRequests=null，原工作600秒/退出60秒上限不变。启动前各主机可用内存要求提高到12 GiB，为 S 工作保留余量。

首次55秒状态读取超时，原句柄保持 UNKNOWN；仅延长本地只读传输等待到120秒，随后恢复同一 stage、容器和 PID/start ticks 的原记录。未重新 prepare、重启、重派或改动运行源。两端正常终态与完整 proof 均从原 stage 取回，原 CPU/容器已退出。

接受器通过六项本地控制，覆盖缺少/重复主机、未结束/失败/不同启动、proof 字节变化、网格或矩阵缺失及稀疏域扩大、CUDA 初始化和设备隔离缺失。原 B36 的52执行/4汇总/6绘图源及 A32 冻结 SHA 保持；两端继承的22份关键组件与当前接受源相同。

## 下一步

Native50 参考组件已经接受。后续仍需冻结 S 方法、Q5 对应的保护和年龄映射、可区分规则/模板的正式比较、完整物理范围、生命周期与整卡报价，才形成 GPU 卡。不能将本 CPU 矩阵或一个 Native 网格解释为完整 Q5 就绪。GPU 顺序保持 S 优先，原最终输入与额外 seed 持续保护。

同日用户对 B36 原视频的完整32条诊断记录见[760](760_CARA_B36_COMPLETE_SINGLE_REVIEWER_DIAGNOSTIC_20261030.md)，与本 CPU 实现验证分别登记。未重跑 A32/B36、原指标、bootstrap 或费用结算。
