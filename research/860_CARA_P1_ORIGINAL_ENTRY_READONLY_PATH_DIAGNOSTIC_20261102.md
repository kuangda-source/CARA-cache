# P1原入口持续不通：只读路径诊断与原句柄保留

单次19GPUh及本卡原中央事务批准保持，未请求新GPU派发或预约。[本次运维回执](../reports/cara_v1_P1_prelaunch_operational_r3_20261102_134423.json)承接上一轮12:51的原入口UNKNOWN；本次13:44原status仍在Windows100.103.229.16:22前超时，未读取到服务器原句柄。当前GPU/内存状态均UNKNOWN，不能把旧49.78GiB或旧“未启动”当新现场事实，不能推进refresh/预算/dispatch。

只读检查显示Tailscale BackendState为Running、Windows peer广告为Online/Active，但原peer ping超时；同一Windows的IPv4和Tailscale IPv6 SSH22都超时。本机netcheck的UDP/IPv4、Hong Kong DERP与无captive portal结果通过。广告在线不等于可用SSH；这些记录未确定故障在Mac、Windows或中间路径，不能归因为服务器或Clash。未修改网络、路由、配置或任何实验源。

需要恢复原Mac↔Windows通路后才能重新核原句柄与52GiB准入。保留同一p1准入检查和既有批准，发送一次连接恢复问题；待回复时不重复询问预算或网络状态。原1462源码本机SHA保持一致；没有读取部分科学结果。原固定源/容器/stage/GPU及19GPUh硬限不变，不重启、不重派。
