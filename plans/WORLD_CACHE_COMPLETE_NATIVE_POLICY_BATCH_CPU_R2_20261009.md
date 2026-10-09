# H-T63实际batch CPU R2：逐调用观察内容对齐，完整范围不变

R1 sourcee5fd9df／123载荷8实际源，3459240／3459241退出1且消失，driver61.629411秒；默认flow OFF的完整成功batch在最终观察事件比较时停止，错误为Observer order/repeat parity differs。原件／完整4行范围与全部原artifact保持，未接受通过子集；新增GPU0／预算SHA不变。这是新观察验收的实现问题待区分，不是方法或研究方向否定。

新接口按设计先进入两个prefix、再分别完成两个分支；原序为before0／after0／before1／after1，成对序为before0／before1／after0／after1。不能要求这两种日志列表时序字面相同。R2仍保留完整原始日志时序，验收按相同call及before／after键对齐所有内容；144事件与唯一键、全部实际输入和输出内容、同动作／guided／全状态、观察和严格重复的原判据不放宽。不修改controller／实际WC／RF／求解器／动作／任何张量，也不删观察或减少重复。

同时为实际Toy batch保存独立完整receipt，以便任何失败均保留全部已进入路径及状态；不把R1未保存状态补写或重构为原件。R2两个flow均完整成功16路径和完整16路径最后向量写出失败，共4行64完整路径2304solver4608net；成功32路径1152 guided＋32 latent实际重读、24语义破坏拒绝、2实际文件截断拒绝、2最后写出失败。全部完成并独立验收后才称新batch CPU通过，不能提前收敛到通过子集。

旧H-T62／60／61源和回执按SHA复用。独立R2 stage、源冻结后CPU执行，CPU不写GPU账本。真实2B全16路径和>2GPUh具体批准仍待完整代码／生产CPU／forecast；不缩拆、训练、扩稀疏、OMR／DRE或人评。
