# H-T58：真实2B成对接口完整结果

**发现及价值：真实Cosmos-Predict2.5-2B上，同一S22状态、同一CC／DD动作的成对执行与原顺序逐值等价。两侧浅层先支付，再决定完整续算，已从Toy CPU走到真实模型。** 这为后续完整刷新调度提供了可用接口，但尚未产生新策略的质量／速度优势。

## 目标、方法与完整范围

沿用[执行前计划](../plans/WORLD_CACHE_REAL_PAIRED_INTERFACE_20261009.md)及[实际生产CPU与启动](190_WC_REAL_PAIRED_INTERFACE_SELECTED_CPU_AND_EXECUTION_20261009.md)。固定曝光CAL Common完整prompt、负prompt、seed3，A6000单卡，768×432、93帧、16fps，guidance7／原权重8与−7，35请求／36实际UniPC-Karras更新／72父CFG调用，原WC设置和安全管线保持。

同一真实S22／44状态，CC／DD×观察OFF／ON×二严格重复×原／成对顺序，共**8比较、16局部pair、32诊断net、48实际FP32张量**。局部不更新solver；每次完整恢复缓存／buffer／模式／solver／RNG／冻结条件，原父继续生成。两个完整原生WC父OFF／ON各产生93帧视频，用于验证诊断无扰动。没有S23、完整反事实后缀、新路由政策、终点或未来成本标签。

选择器只接收两侧不可变PaidProbe统计，CC／DD在本卡固定。临时拥有forward／denoise绑定并精确恢复原对象，compiled WC／RF体来自实际模块全局；观察ON显式记录每分支输入／输出，OFF不执行这些观察。保护区、原算术、缓存更新和求解器不改。

## 完整结果

| 检查 | 完整结果 |
|---|---|
| 同动作分支／guided FP32 | 全16pair／48张量服务器实际CPU重读、直接torch.equal及原CFG表达式重建通过 |
| 原／成对、观察开关、二严格重复 | 全8比较相同，包含完整1216项origin／end／恢复状态与solver、冻结条件 |
| 实际层访问 | CC每个probe层2次、26个深层0次；DD全部28层各2次 |
| 两完整父 | 全72net／36solver的输入、输出、deep、cache、测量、终态与backend／pipeline相同 |
| 两完整视频 | 各93／93帧、768×432／16fps，全文件与全部解码RGB SHA相同 |
| 执行来源 | source9f01274、156载荷和runtime前后SHA不变，原GPU／CPU全部成功退出 |

视频SHA均为`cb8b06ab2e3c1af5333bcfab5628e058f83775f36fb4c25222e5263d59f0af6c`。全部原件见[原终态捕获](../reports/wc_real_paired_interface_r1_terminal_20261009_capture_and_independent_audit.json)、[完整独立验收](../reports/wc_real_paired_interface_r1_complete_alias_independent_audit_20261009.json)和[所有结果／费用摘要](../reports/wc_real_paired_interface_r1_complete_result_summary_20261009.json)。

## 成本与适用条件

下表每格包含两次严格重复的均值，单位秒。计时包围同步的当前velocity、层hook、控制器及相应观察，**仍是局部带诊断计时**，不包括所有clone、状态hash、写出和恢复。

| 动作 | 分支观察 | 原顺序均值 | 成对均值 | 成对／原顺序 |
|---|---|---:|---:|---:|
| CC | OFF | 0.654472 | 0.654851 | 1.000579 |
| CC | ON | 1.508113 | 1.516662 | 1.005669 |
| DD | OFF | 6.650510 | 6.631648 | 0.997164 |
| DD | ON | 7.486764 | 7.490298 | 1.000472 |

数值没有显示大的成对执行核心开销，也不能用两次固定执行顺序的细小差异证明加速。观察输入／输出hash在CC上约增加0.86秒、DD约增加0.84秒（带诊断条件差），因此后续部署计时应另设明确边界。

真实快照逻辑tensor约2.635GiB（2,828,989,246字节），调用前GPU free约32.16GiB，二份快照加8GiB工作区／prefix预留要求约13.27GiB，准入通过。局部记录的PyTorch峰值allocated约11.62GiB，仅限本进程allocator统计；不是全进程峰值或所有场景显存上界。所有16次内存原始记录保留。

原父OFF带诊断wall903.816941秒、ON含全局部实验／恢复／写出2077.098263秒，加载103.754713秒。完整supervisor **3125.424150秒＝0.868173375GPUh**，导入、加载、诊断、clone／恢复、hash和flush全计；不能把ON／OFF差直接当算法成本或未来节省标签。

## 原件捕获修复与费用

原GPU3445779／3445791、绑定后CPU3445780／3455334全部退出0且消失，目标GPU24MiB／无计算进程、共享锁释放。账本已保存服务器结算原字节：**29.895246590／50GPUh，剩20.104753410GPUh，65次提交，无GPU在途**；旧`used=50`只是原任务预留。

本地第一次完整独立捕获将runner记录的`/home/...`路径字符串与服务器CPU的`Path.resolve()`结果`/media/...`直接相等比较，失败记录保留。两个路径确为同一个文件：另做标准库只读检查，**全部16个实际文件**逐一resolve、核对完整路径／大小／SHA并绑定原记录，其他完整验收保持，然后通过独立审计。没有重跑模型或修改原156载荷／CPU结果，也没有按basename放松路径检查。

## 下一步

1. 继续[H-T60完整四动作CPU](192_WC_FOUR_ACTION_FULL_SAMPLER_CPU_EXECUTION_20261009.md)。R1汇总变量错误保留；R2只修该处，原68控制、新32比较／64全36路径／12失败全量不缩，当前实际CPU在跑。通过只代表Toy CPU接口，不代表真实完整部署。
2. 因三条已完成轨迹均出现DC，真实完整36步验证须支持CC／DC／CD／DD，保留原生／固定mask回放／成对回放的区别，不将共同OR算术称原生政策。完整模型等价后，再做正确终点收益和未来真实成本、原WC／简单共同刷新／Cosmos校准RA基线。
3. 保留W1视频混合结果、稀疏适用条件、旧Human CD例外、所有失败与判据。当前结果是曝光Common同动作实现等价，非新身份CONF、物理质量、算法创新或干净端到端速度；RA近邻仍需比较。

组会飞书随后由CLI更新完整结果并回读。累计50GPUh及单次>2GPUh具体确认保持；不缩拆对照、训练Head／LoRA、扩稀疏／OMR／DRE或引入人评。goal active，继续研究。
