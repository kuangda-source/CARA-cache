# H-T55：成对probe接入原Video2World velocity与完整UniPC的CPU同动作对照

2026-10-09，承接H-T54全局／显式观察CPU通过。Common H-T52原95源／全部40对／两父视频继续，当前卡只执行独立CPU，不加载在途教师、修改原stage或提交GPU。

## 要回答的问题与实现

保持原Video2World `get_velocity_fn_from_batch`条件构造、两侧视频条件和 `cond + guidance*(cond-uncond)` 运算顺序，只把相邻两次denoise改为一次成对executor调用。反向AST必须完全还原原函数；实际RF模块全局按对象身份核对。原WC／RF compiler和所有H-T54控制保持，不能改旧已验收源码来配合新结果。

原完整Text2World采样函数体及UniPC用于35请求／36更新／72分支。生成器、CPU噪声、normalize／broadcast、条件类构造、4层网络／attention仍明确为Toy适配；这不是真实2B、VAE或视频。模型get_velocity临时安装只作用于本卡独立副本，denoise及net.forward在成对路径保持原方法绑定。观察开／关分别登记，不能把哈希时间称为干净延迟。

## 完整预登记范围

- 旧H-T54全28行（8主、2初始化、16失败、2源）原范围保留。
- flow OFF／ON × 恒CC／恒DD／交替CC-DD × 显式观察OFF／ON × 两严格重复，共24个原顺序／成对顺序完整比较，48条父采样、1,728次solver更新、3,456次分支计算。
- warmup、68／69尾部、70循环reset以及最后0／1保护如实执行；selector只在原合法双前缀就绪后接收PaidProbe，不能用当前深层teacher。
- 全36条velocity／solver返回、最终latent／WC字段／buffers／参数版本／eval／条件／CPU-Python-NumPy RNG／seed generator，以及13、21、33、35、36五检查点全部组件一致。第22步在两条路径均执行完整状态roundtrip，并真实从恢复latent继续；条件独立检查与恢复，不声称模型任意故障可回滚。
- 观察ON比较全部72分支输入与net输出（按调用槽匹配，原／成对的中间事件时序如实不同）；观察OFF输出和完整状态须仍一致。两重复及观察ON／OFF需各自跨组相同。
- 四类失败×两flow＝8完整范围保留的拒绝：step23 selector异常、最终solver异常、forward绑定变更、视频条件构造异常。失败副本弃用；不以成功子集代表整卡通过。

## 来源、执行与下一步

代码、此计划及载荷SHA登记提交推送后，同现有venv在新独立CPU目录执行；沿用H-T54 R2已审计的退出进程导入适配并在测试前恢复。CUDA初始化、权重加载、下载、Triton执行均禁止，CPU不写账本、不占GPU锁。保存首次失败、原PID、日志、源SHA及原字节，完整独立分组核对；合法的Common费用结算只记录，不当成本卡修改账本。

CPU通过仅为实际函数／完整求解器接口证据。真实模型同动作输出／显存／成本和原生WC／共同刷新／RA联合基线仍待，终点刷新收益及未来真实成本标签不由此产生。下一GPU完整成本预测≤2GPUh才可依原自主权限，>2需具体批准，不能缩拆此范围或消耗旧卡身份；累计50GPUh、旧正负／判据保留，不训练／扩稀疏／OMR／DRE／人评。
