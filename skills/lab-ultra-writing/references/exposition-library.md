# 统一技巧的检索入口

通用技巧保存在[exposition-cards.json](exposition-cards.json)，[统一写作技巧](writing-techniques.md)是其生成视图。原34个ID保留，后续分析按相同解释任务合并，新增条目不成为必经步骤。

在本Skill目录离线查询；只需要Python标准库：

```sh
python3 scripts/query_exposition.py query 共享 校准
python3 scripts/query_exposition.py query 阈值 优先级
python3 scripts/query_exposition.py query 人工 附件
python3 scripts/query_exposition.py query 分母 参照
python3 scripts/query_exposition.py show physical-07-forward-before-inverse
```

`list`列出读者困难，`show`读取指定ID，`query`仅按关键词命中，不是质量排名。无匹配时自行组织，不按算法或获奖篇数选技巧。实际使用前看conditions/evidence_needed；misuse/source_weakness限定迁移边界，transfer_example不是本题事实。

数据源不随分发包安装。卡内已有自足的动作与限制，sources的仓库路径和哈希仅供维护审计；普通写作无需拥有原语料、联网或重做蒸馏。涉及相互矛盾的建议先看[冲突裁决](conflict-decisions.md)。

维护时修改JSON，然后运行`python3 scripts/render_techniques.py --write`；只检查视图一致性用不带`--write`的命令。图表渲染、论文机械检查仍由SKILL入口按实际任务调度。

更具体的条件差异、来源逐项归并和排除依据见[条件细分检索](technique-variants.md)。通用卡与细分共同构成统一技巧库，不是按原论文分立的 Skill。
