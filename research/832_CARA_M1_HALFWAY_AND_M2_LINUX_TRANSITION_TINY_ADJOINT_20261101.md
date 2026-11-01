# 832 — M1半程与M2实际Linux缓存转移／小模型伴随

原M1半程已核对7/14完整、0技术失败、原四句柄存活且单卡独占，67°C。M2固定源码缓存转移通过两卡实际Linux五项CPU验收，原容器退出0；离散伴随与有符号读写值另通过五项本地小模型检查。当前没有真实Cosmos伴随或完整视频方法收益结论。

## 原M1半程

[原运行](../reports/cara_read_write_halfway_original_status_r1_20261101.json)与[半程接受](../reports/cara_read_write_halfway_accepted_r1_20261101.json)只读取14分母运维计数、原进程、温度、资源和独占；未读部分T_DD/LPIPS/曲线。原16GiB输出仍余约15.5GiB。原四卡[中央只读](../reports/cara_read_write_halfway_central_status_r1_20261101.json)确认cap226、used194.03986128165678、reserved18.45、available13.510138718343217；其中旧16.5与本卡原1.95预约保持，没有重复预约或结算活跃任务。

m1已[按单次处理删除](../reports/cara_read_write_halfway_automation_deleted_r1_20261101.json)。[检查R2](../reports/cara_read_write_acceptance_schedule_r2_20261101.json)保留原m1-2的20:28及原定义SHA；按7/14计数与墙钟没有提前终验的依据，未新增检查或延长20:46:24硬限。

## M2实际Linux缓存导数

[原CPU准备](../reports/cara_read_write_transition_Linux_CPU_prepare_r1_20261101.json)、[原终态](../reports/cara_read_write_transition_Linux_CPU_capture_r1_20261101.json)及[唯一接受](../reports/cara_read_write_transition_Linux_CPU_accepted_r1_20261101.json)绑定发布源e458394d、原注册和全payload。实际1核/4GiB/零额外swap/CPU26/无网络/无GPU配置核对通过，启动前宿主可用约28.7GiB；44.91秒工作，原容器正常退出。M1保持独立的CPU24、25与原GPU源。

实际Torch2.7.1+cu128、WC/RF模块及globals下五项检查通过：两flow完整36输出/缓存/buffer逐值等价；C非恒等工作状态；输入和残差缓存有限差分；原UniPC完整小模型图VJP；冻结/未就绪/inference-mode拒绝。原官方GPU依赖只使用已登记CPU导入适配，未加载真实权重或启用CUDA。[四项独立接收器控制](../reports/cara_read_write_transition_acceptor_CPU_r1_20261101.json)拒绝未退出、额外swap、外来源、缺行及伪造有限差分容差。

## 已补的离散伴随

`cara_read_write_adjoint_r1.py`按完整连续状态坐标重算一步并做VJP，不显式建立Jacobian；latent、全部UniPC预测/last_sample与cache/buffer都参与。离散timesteps、order、source/validity保持各实际分支的语义。硬D−C后状态收缩给出有符号read/write；空槽布局或solver离散状态错位直接拒绝，不暗中补None或伪造来源。

[本地五项原件](../reports/cara_read_write_adjoint_CPU_component_r2_20261101.json)：实际WC/RF/UniPC方程与小权重下，完整36步重算伴随相对整图梯度最大绝对误差7.98e-17；read/write/total各两个幅度的辅助状态有限差分通过；Dense起点仍用D−C符号；第35更新重置之后的write值为零；缺余向量、错精度、错槽和错solver阶数拒绝。

[精度诊断R1](../reports/cara_read_write_adjoint_CPU_precision_diagnostic_r1_20261101.json)保留：RF原生FP32使约1.45e-6的read方向在0.1幅度差分下偏差1.06e-7，未过5%界。没有修改RF或放宽5%相对容差；对这个小方向使用0.5与1.0两个辅助幅度后，误差分别1.08e-9与5.66e-9。write/total保留0.1/0.2幅度。它验证声明的小系统，不作为真实模型精度或硬行动排序证据。

下一步同一伴随组件的实际Linux接线、真实固定槽/来源映射、真实模型VJP与93帧VAE/Alex终点桥接，见[M2安排](../plans/cara_next_stage_20261101/read_write/M2_ADJOINT_IMPLEMENTATION_AND_HARD_ACTION_PLAN_R1.md)。M2完整GPU范围/全段费用仍未冻结；原M1及旧结果/TEST保护保持，没有新GPU或新账本事务。
