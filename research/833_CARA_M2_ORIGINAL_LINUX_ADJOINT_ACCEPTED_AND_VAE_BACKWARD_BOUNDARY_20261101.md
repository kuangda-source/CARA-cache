# 833 — M2原Linux伴随接受与VAE终点反向边界

M2已有两段实际Linux CPU接线：固定源码可微缓存转移，以及完整状态离散伴随／有符号读写价值。各五项检查通过、原CPU均正常退出；核心估值计算已可执行于声明的小权重系统。真实Cosmos权重、视频Alex终点和硬交换效用仍待，尚未建立论文主方法的科学效果。

## 原伴随CPU与唯一恢复

首次[prepare传输](../reports/cara_read_write_adjoint_Linux_CPU_prepare_r1_20261101.json)在SSH banner阶段255，恢复原stage时[未找到注册](../reports/cara_read_write_adjoint_Linux_CPU_capture_r1_20261101.json)。随后只读检查确认[原stage与原容器均不存在](../reports/cara_read_write_adjoint_original_absence_and_vae_read_r1_20261101.json)，才继续同一stage的首次实际准备；没有从UNKNOWN推断不存在或重复派发。

[成功原准备R2](../reports/cara_read_write_adjoint_Linux_CPU_prepare_r2_20261101.json)绑定22ee936b发布源。[原终态R2](../reports/cara_read_write_adjoint_Linux_CPU_capture_r2_20261101.json)确认20:06:17至20:06:54容器正常退出0、无OOM；33.805秒工作，实际CPU26、1核/4GiB/零额外swap/无网络/无GPU。[完整接受](../reports/cara_read_write_adjoint_Linux_CPU_accepted_r1_20261101.json)核对原注册、全部payload/runtime SHA、资源、完整分母与原数值；[三项接收器检查](../reports/cara_read_write_adjoint_acceptor_CPU_r1_20261101.json)拒绝缺差分行、伪造零值、超差梯度和夸大真实权重范围。

实际Torch2.7.1+cu128、WC/RF导入和原UniPC下，完整36步重算伴随与整图梯度最大绝对误差8.67e-17；read/write/total各两个幅度的辅助状态方向差分通过，D起点保持D−C符号，第35更新重置后的write值为零。使用小权重与合成latent目标，不是实际视频梯度或硬交换排序结果。两个M2 CPU容器均已退出；后续复用原件，不为刷新文档重跑。

## 真实终点接线的新证据

[两卡runtime源码只读](../reports/cara_read_write_vae_runtime_source_read_r2_20261101.json)与[反向边界审计](../reports/cara_read_write_vae_backward_source_audit_r1_20261101.json)发现：外层model.decode和已注册WanVAE.decode存在no_grad包装；Wan2.1解码在各latent时间片间保留_conv_idx/_feat_map等特征缓存，原路径以clone/cat保留跨块数值依赖。源码未见detach不能替代真实权重梯度验证。

下一步须绑定实际加载tokenizer类和文件SHA；独立校准适配只绕开已核对的no_grad包装，保留原均值/标准差、dtype、decoder、时间缓存和cache clear。先比较硬前向，后做VJP与多epsilon有限差分；不能把93帧分别独立decode、清缓存或假定模型.decode可反向。完整93帧真实显存/重算费用仍未知，这次未改运行中的VAE、安装软件或启动GPU。

## 原M1继续唯一运行

[20:13:24原句柄观察](../reports/cara_read_write_preterminal_original_status_r1_20261101.json)：12/14完整、1运行、1未到达、0技术失败；原四PID/start ticks仍存活，runner独占，87°C，90°C保护保持。原输出仍余约15.5GiB。仅运维计数，未读部分T_DD、视频指标或科学曲线。

保持原b930df4b源、1.95GPUh、20:36:24停止释放/20:46:24硬截止。同一m1-2仍于20:28终验，半程m1已删除。完整14成功退出/释放/实际唯一结算后，才接受四latent/全93RGB等价、一次八对评分和完整读写分析；旧冻结、旧CAL与保护TEST保持。下一卡不继承M1原账本权限。
