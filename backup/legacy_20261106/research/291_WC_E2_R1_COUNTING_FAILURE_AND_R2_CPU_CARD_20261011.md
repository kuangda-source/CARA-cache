# E2 新计时入口R1观察接线失败与R2完整CPU修正

2026-10-11。source061ce31的原R1已退出1，监督4042084／子4042085均消失，原件只读捕获。211载荷不变、budget不写、新GPU0。完成一个WC路径后，RA代表路径的动作／计数观察核对失败，完整76原位置保留，不能称CPU通过或RA／A方法失败。

原BlockCounts在最后深层block执行时总标记最后一个浅层调用。成对RA先付两分支probe，随后顺序续深层；因此两个深层访问都记在第二分支。R2新增局部PairedBlockCounts，在深层pre-hook按实际net.cnt匹配最新未完成的prefix，原首／末钩子不增GPU运算、不改输出／控制器／深算，循环counter0匹配最新实际调用。WC串行与Native也覆盖。

修正保持全部40确认／32计时／4附加AUDIT，完整flow OFF／ON 152成功路径及八旧saved Toy parity／32新计时parity，故障、拒绝、语义mutation与截断范围不变。R1源、stage、错误、费用与原件保留，不在旧目录改源或覆盖重投；R2独立identity、哈希、登记与目录。R2此处仍待实际CPU执行；不宣称真实2B输出等价、clean latency或视频结果，真实GPU仍需整卡forecast／实际CPU／源资产／live准入。
