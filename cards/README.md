# 卡片规格与最小入口

[TEMPLATE.yaml](TEMPLATE.yaml)是新卡草稿。详细角色、顺序、分母、报价和决策协议使用已冻结文件的相对路径与SHA256；模板不是运行授权。正式科学范围以原manifest为真源。

默认仅在本地校验，不连接服务器：

```sh
.venv/bin/python scripts/run_card.py --card cards/TEMPLATE.yaml --command validate
.venv/bin/python scripts/run_card.py --card cards/cal66_existing_r1.yaml --command plan
```

`DRAFT_REVIEW_ONLY`允许讨论未填规格，不表示可以运行。已有CAL66适配器核验66路径、原预算、唯一launch/stage、34个已发布源码文件及引用SHA。该YAML是既有句柄的操作视图，输入和重复顺序由原manifest绑定；它不重登记实验，也不替代原自动检查。

`recover/capture/accept`只委托原白名单工具，须明确指定新回执路径，拒绝覆盖。`capture`还需选择admission/halfway/terminal；`accept`需同launch的原capture，完整科学接受由原独立接受器决定。本次只测试命令构造和离线校验，未实际调用这些远端操作。

第一版无prepare、launch、retry、评分重启、改GPU模式或账本预约命令。后续适配按下一科学卡需要增加和验证，不能将任意脚本路径写进YAML执行。

方法别名以完整执行指纹判断；计时重复、warm、数值控制、历史桥接全部保留物理槽位。`alias_candidates`只给出正式角色别名建议，不修改分母。α、seed、网格、输入或精度不同都不能合并。

固定新输入池增量核查：

```sh
.venv/bin/python scripts/audit_cara_new_pool_delta_r1.py \
  --prior-delta reports/cara_new_input_pool48_delta_r1_20261025.json \
  --output reports/NEW_UNIQUE_POOL_DELTA_RECEIPT.json
```

该命令读取本地新增/改变的身份记录与四卡项目输出元数据，不解码视频张量或导出科学指标，不重新选池。`scoped_no_execution_evidence=true`仅表示本次覆盖范围内无使用证据；实际生成前仍须最新审计及卡片准入。未知连接或读错误不能通过。已知审计元数据只按精确文件SHA豁免，不按文件名通配符跳过。
