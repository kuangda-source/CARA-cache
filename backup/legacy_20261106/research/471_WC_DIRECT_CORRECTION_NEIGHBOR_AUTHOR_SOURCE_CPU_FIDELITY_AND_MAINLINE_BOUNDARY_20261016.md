# 直接修正近邻：作者源码CPU核查与Cosmos适配边界

更新：2026-10-16。执行全部在本地CPU，无服务器查询、新GPU、权重下载或训练；N05原source、句柄、范围和12:05一次查收保持。

**已把直接修正近邻从“有仓库和示例”推进到固定完整源码与可复核CPU调用路径。** AdaCorrection的偏移分数、截断融合核可以运行，但作者接口不能直接识别Cosmos；最小调用还暴露了需要修复/说明的缓存状态问题。当前不能把它当成已经可运行的第12个N05对手，也不能按融合权重推算节省比例。这是具体移植和版本问题，不是方法方向被否定。

## 1. 主来源与范围

- [论文v3](https://arxiv.org/html/2602.13357v3)，2026-08-05版本，方法与Algorithm 1。
- [作者仓库固定提交](https://github.com/NoakLiu/FastCache-xDiT/tree/cc468521527ab2c3610ede8ee0315b469c0570f5)。下载完整archive，只解出201份文本，其中156份Python；不导入整个xfuser包、不执行构造器中的CUDA分配。
- [分发入口](https://github.com/NoakLiu/FastCache-xDiT/blob/cc468521527ab2c3610ede8ee0315b469c0570f5/xfuser/model_executor/cache/diffusers_adapters/__init__.py#L20)与[实际修正路径](https://github.com/NoakLiu/FastCache-xDiT/blob/cc468521527ab2c3610ede8ee0315b469c0570f5/xfuser/model_executor/cache/utils.py#L1156)。

论文正文明确指向该仓库，但这不代表其中每一项接口已支持Cosmos。源码archive SHA为`d5330ab574344c5f2b12aef58bf9252e2b51cd5c70b4576ea99fbee0ccf83082`；201文件逐项SHA、完整树与CPU绑定均保留。`utils.py` SHA为`e0b2de550cc1e33460875a8c588744e7d1097a6ca989f87511ec160d00ad8c14`。

CPU仅装载已审阅方法的原AST体，使用1×3×4小张量、三个计数Block、Identity投影和显式CPU状态。完整上游构造器、真实Flux/PixArt/Cosmos、训练权重和视频均未运行；这些控制用于识别算术与调用语义，不证明完整适配或生成效果。

## 2. 已复核的可复用部分

截断融合核的三个边界控制通过：分数负值/0.25/超1分别得到0/0.25/1的融合权重。无历史偏移分数返回0；实际偏移计算与其代码中的通道总体方差和token范数公式一致。

存在必须标明的版本差异：论文v3 Eq.(3)的时间项未平方，而固定实现的时间项平方。一个低幅CPU例子分别得到0.119004958与0.035309513；这只说明两种定义不同，不证明哪种视频效果更好。后续若移植必须事前选定“固定作者代码版”或“论文公式复现版”，不能混用名字和参数。

## 3. 三个实际调用发现

|控制|本地CPU实际观察|对公平比较的意义|
|---|---|---|
|Cosmos类名分发|以真实骨干同名`MinimalV1LVGDiT`替身调用原分发函数，记录Unknown后返回原对象，未加载后端|直接调用公开入口可能成为未加速原模型；必须独立核对补丁生效，不能只看函数未报错|
|修正分支费用|首次权重0、约0.5、1三种控制，三个Block都各执行一次完整fresh；混合前已取得fresh结果|权重0.5不意味着只付0.5个Block；真实成本必须包含dense和投影/融合，不能以插值比例估价|
|缓存状态生命周期|原方法最小首调用后两份residual仍None；相同输入第二次命中cache时出现Tensor＋NoneType的TypeError|源码路径需要明确残差初始化/维护；这是默认方法组合的CPU重现，尚未运行完整上游pipeline|

另设显式有效残差的cache-hit控制：原forward返回缓存残差，完整Block调用0、偏移分数调用0。它与上表的fresh-blend路径是两条不同分支。只有在此控制中人为提供了残差，原失败记录没有被该fixture覆盖，也没有据此宣称上游实现已修复。

固定实现还创建逐Block Linear投影，示例加载中未核实其训练/预训练权重绑定。本轮Identity只用于追踪控制流，不能替代这些投影来声称忠实复现AdaCorrection的生成质量。

## 4. GP-Refiner资源复核

对[作者仓库commits接口](https://api.github.com/repos/Aredstone/GP-Refiner/commits?per_page=1)本次只读请求仍返回409与`Git Repository is empty.`。原始HTTP/返回体保留，属于当前公开资源状态，不是该方法的性能负结果。

## 5. 下一动作与主线边界

N05现有完整11配置继续运行，不加第12项、不追改已派source/配置或费用。该卡仍回答WC/RA阈值网格、少步Native与两个冻结工作点的公平前沿。

直接修正近邻保持显式待补：若采用AdaCorrection，需要先明确版本、投影权重/初始化、Cosmos逐层边界、残差与CFG双分支独立生命周期，再完成同输入的OFF/完整路径/连续cache控制与实际成本。可逆的状态修复可以研究，但须保存原失败、公开偏离并使用fresh独立实现；不能把修复后的自定义控制器叫作未经改动的官方实现。GP-Refiner待公开资源或论文可完整重建的必要参数，不发消息索取、不引入人评。

本轮不自动开启该近邻GPU、不用伪简化补满对照。N05接受后，先据N05/N06冻结N07主线与前密C/A强简单对照，再核定整卡费用与生产CPU。近邻适配若仍未成立，在论文中如实限定比较范围；不把这项移植问题变成无限期阻塞已可执行主线的门槛。

## 6. 原件与复跑

- `reports/wc_mainline_direct_neighbor_deep_source_CPU_inventory_20261016.json`：完整文本源码清单、SHA、GP-Refiner原始返回。
- `reports/wc_adacorrection_author_method_CPU_characterization_20261016.json`：最初方法核与分支检查。
- `reports/wc_adacorrection_author_method_CPU_characterization_r2_20261016.json`：补齐未知Cosmos分发检查，其余核心保持。
- `scripts/audit_wc_adacorrection_source_cpu_r1.py`：只读选择方法，GPU调用会被CPU guard拒绝；源码包位于忽略目录，原件archive不入Git。

复跑使用固定原archive并指定新的output文件，不覆盖旧回执：

```text
.venv/bin/python scripts/audit_wc_adacorrection_source_cpu_r1.py \
 --source-root .sync/adacorrection-complete-source-cc468521 \
 --output reports/新的直接近邻CPU回执.json
```

这是主线基线实施核查。F/B继续关闭，所有频域/Token merge/增强投影开关均未启动，无新GPU质量、速度或整卡CPU接受结论。
