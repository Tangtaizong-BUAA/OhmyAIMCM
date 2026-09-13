# 条件写作技巧检索

通用技巧与条件细分构成同一套写作能力。先按当前读者缺口选通用技巧，再在需要时检索更具体的条件。不要将全部来源逐篇加载，也不按支持来源数量判断科学正确性。

在本 Skill 目录运行，无需联网或原语料：

```sh
python3 scripts/query_variants.py query 搜索 --limit 3
python3 scripts/query_variants.py query 类比 --limit 3
python3 scripts/query_variants.py query 未完成 --limit 3
python3 scripts/query_variants.py show variant-0001
python3 scripts/query_variants.py source V00000
```

`query` 按规则或父技巧 ID 字面匹配，默认最多返回 3 条；`--card` 可限定父技巧。返回的 rule、conditions、misuse 必须一起使用：描述已有工作，不据此要求改变模型、增加实验或填造结果。无匹配时自行组织段落。

`show` 读取一个确切细分；`source` 读取一个确切候选的原分析定位。检索只带一个来源定位及成员数，完整成员对应和排除理由在 technique-variants.json 中。证据路径用于维护审计，分发包不包含原论文语料。

本轮保留并扩展为 68 个通用技巧、145 个条件细分。6,230 条原候选全部有归并或排除去向；归并不是独立科学验证。原始语料中尚未转换或未成功处理的文件不在此完成声明内。
