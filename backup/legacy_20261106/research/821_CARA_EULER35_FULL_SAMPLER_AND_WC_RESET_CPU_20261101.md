# 821 — Euler35完整采样与WC计数CPU接线

2026-11-01，Asia/Shanghai。E1单次46路径/硬7GPUh审批仍待用户，未启动GPU、未访问四卡或真实中央账本。本轮推进已授权的独立EULER-E0 CPU适配，原E1的1268文件payload SHA全部保持。

## 实现与验证

新增隔离的`CosmosEuler35`，将818已声明的显式35点正sigma＋终点0网格接入原Cosmos sampler的`set_timesteps/step`接口。沿用原采样器、视频子类CFG、速度含义和一阶更新；只在显式context内替换scheduler，正常/异常退出均恢复原对象，不修改原UniPC入口或上游文件。

实际采样器传入原tensor的逐步scalar view。入口前固定网格及参数，循环内检查view身份及张量元数据，不为时间步校验增加GPU到CPU标量同步。错误网格/请求、错序/复制时间步、额外更新、重复初始化、错误dtype/shape及嵌套安装被拒绝；5项本地单元检查通过。

沿用已接受的`compile_wc_adapter(..., paper_port=True)`，把ATS系数明确固定为4，保留原70分支调用horizon；不再重复开发解耦逻辑。强制全计算只改原skip判断；其余probe、history、head和计数走固定WC代码。论文式阈值0.08、motion2、saliency0.12、空间scale0.5显式传入。flow开/关分别检查，两者不是两个科学实验。

在原完整inference→sampler→实际视频CFG函数→官方Native/WC forward函数→decoder/writer入口下，完成8条微型CPU路径：每组Native、allD、allD无计时重复、paper-style WC各1条，flow开/关两组。每条35更新/70CFG，总280更新/560分支调用。

- Native与allD的同初噪、全部70个分支输出、35个更新latent、最终latent、解码RGB和RNG完全一致。
- allD计时开/关一致；连续去噪至解码边界使用原两个同步调用位置。
- WC每条请求前计数重置，实际pre-counter为0…69，post-counter为1…69、0，恰在第70调用重置，无第71/72调用。
- 原scheduler在正常与注入失败后恢复。CUDA未初始化，权重未加载，无GPU或账本操作。

## 证据范围

[实际CPU回执](../reports/cara_euler35_sampler_CPU_r1_20261101.json)绑定源SHA、固定runtime SHA、原CFG源码及实际checker输出。此次执行在本地macOS CPU，尚未做Linux运行；使用明确的微型权重、condition对象、patch embedding、attention、decoder、mock writer及CUDA遥测替身。93帧微型RGB一致不是真实Cosmos权重/编码视频/GPU数值一致，也不是吞吐或保真结论。源中的论文式参数仍为重建，不称官方逐位复现。

## 后续

E0的完整微型入口与horizon/ATS接线已补齐。待UniPC E1完整结果确定方法后，前瞻冻结Euler策略的噪声坐标、保护/年龄/晚期间隔约束与完整卡费用。若进入未来单独授权的Euler卡，必须先验证真实权重Native/wrapper-allD逐步和RGB等价，以本Euler Native为质量参考；失败停止科学排序。

当前推荐的唯一GPU卡仍是[820的E1审批卡](../plans/cara_next_stage_20261101/e1/ENDPOINT7_SINGLE7GPUH_REVIEW_R1.md)。不把CPU工作扩展成Euler GPU许可，不改变E1待批7GPUh、原冻结、四旧CAL或保护TEST。
