# L0 原93包本地wheel绑定准备

2026-10-01。状态：CPU4_LOCAL_LINUX_CONTRACT_PASS_NOT_REAL_BINDING_INSTALL_GPU。

旧install-r1下载超时且env仍空；当前六包独立range-r1继续，不改其stage或重启。新绑定程序仅把六个完整审计包由registry URL替换为绝对local file URI，并将单个官方SHA限定在原锁允许集合内。原93个包版本/覆盖完整保留，其余87个requirements block逐字节不变，原四个native local URL也不变。这是原依赖图的transport derivation，不是新的resolver实验。

实现：[绑定CLI](../scripts/bind_l0_native_local_wheels.py)、[绑定契约](../src/wcomr/local_wheel_lock.py)、[安装门](../scripts/prepare_l0_native_environment.py)。安装门需原解析receipt/requirements、selected pins与原四wheel输入身份一致、derived TXT重组成一致，并fresh重哈希六个实际owned cache payload；新stage使用PYTHONPATH=stage/src，不改旧install-r1固定source。

[本地CPU回执](../reports/l0_native_local_binding_local_cpu_20261001.json)4通过0.04s，[Linux同4回执](../reports/l0_native_local_binding_linux_cpu_20261001.json)4通过0.18s/含wrapper2.543548s。测试采用真实原93锁与版本表，但本地wheel路径和metadata是fixture；只验证契约和拒绝版本漂移/锁外digest，不是六包实际绑定或安装验收。修改安装分支仅语法检查，真实分支待完整六包终态审计后执行。

下一：同transitive handle完整6/exit0/3PIDs退出/锁释放后fresh全SHA/meta/source/budget审计并仅关闭owned16501；离线生成derived93 TXT+JSON，同步Git后新唯一install-r2/CPU1800/新owned forward，仍装入empty .sync/l0-native-env-r1。真实93 inventory验收后才新CPU native probe；旧probe helper必须按实际r2终态适配，不能直接执行。

GPU预算仍3.6512467238638138/4h；新4GPUh clean50未得到答复，无新GPU workload/人工评审/训练/付费。
