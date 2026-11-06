# 原入口已通过手机热点与 Tailscale 恢复

用户切换手机热点并明确要求使用 Tailscale 后，两卡原 P1 句柄与四卡原中央账本均成功回读。见 [原句柄恢复](../reports/cara_v1_P1_original_status_hotspot_r6_20261102.json)、[原中央只读回执](../reports/cara_v1_P1_central_status_hotspot_r2_20261102.json)。这次完成了公钥认证和远程命令，能够用于后续恢复；原私有 SSH profile、HostKeyAlias 与密钥保持。

恢复时原stage无GPU意图、派发或容器，0/146；原52GiB准入仍拒绝，资源只读回读50.07249GiB，原GPU空闲46°C。上述是资源修订前快照。随后用户要求复核内存门，已完成启动前工程修订和唯一实际启动，当前状态见 [862](862_CARA_P1_MEMORY50_CPU_AMENDMENT_AND_ACTUAL_START_20261102.md)。

此前用户位于服务器内网，本机10.130.2.111：旧记录确认两卡10.128.160.181:22、中央10.156.160.3:22617。关闭TUN前普通端口探测可返回，但SSH未完成握手；绑定真实en0检查在CONNECT超时。用户关闭TUN后路由经en0/10.130.2.254，用户Terminal与代理的直连SSH均超时，网关可达。不能据此把剩余故障唯一归因为Clash或本应用权限。

本轮仅试验任务私有直连候选，未完成认证后已恢复原Tailscale profile（SHA f5750eedef629c0f64441300ddfbebac8a9d38e5076fda69cbb421404ef13f6d）；未修改系统路由、Clash、服务器服务或安装软件。[LAN/TUN诊断原件](../reports/cara_v1_P1_user_LAN_and_TUN_off_recovery_r1_20261102.json)保留。当前遵循用户最新指令继续原Tailscale，不再自动切LAN或重复询问已回答的相同网络测试。
