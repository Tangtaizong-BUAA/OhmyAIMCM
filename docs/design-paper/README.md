# OhmyAIMCM 系统设计论文

本文以项目原名 Lab-ultra-unified 撰写。项目现名为 OhmyAIMCM，论文的版本标识、引用与核查记录保留修订时的信息。

[阅读论文](Lab-ultra-unified-整体设计论文.pdf) · [LaTeX 源码](main.tex) · [修订说明](REVISION.md) · [核查记录](qa.json)

《Lab-ultra-unified：面向数学建模论文的双路论文蒸馏与可追溯数模工作流》

2026-09-13 修订，21 页，LaTeX 源码含约 1.5 万汉字；4 幅图、5 张编号表、1 张来源索引长表、21 条参考文献。基于原 lab-Pro 设计论文扩写，适配 `lab-ultra-unified-20260910-r2`；实际 Skill 入口仍为 `$lab-ultra`。

正文详细解释连续文本分块、候选表达动作、引文定位、语义复核、条件归并，以及从 LayoutIR 到页面控制的版式路线。技术栈、来源字段、计数口径、运行时检索和可复现环境均有独立说明。药材论文以两个原页裁图及具体结果展示工作流产物。

## 编译

需要含 XeLaTeX、latexmk 和 Fandol 字体的 TeX Live。此版已在 TeX Live 2025 编译。进入本目录执行：

```sh
latexmk -norc -xelatex -interaction=nonstopmode -halt-on-error -outdir=build main.tex
```

输出为 `build/main.pdf`。TikZ 架构图写在 `main.tex` 内；其余图片由 `assets/` 提供。`assets/herbal-drying.pdf` 是作者提供的 285 页案例原件，编译时只截取指定页面，未修改其内容。

## 核查范围

本次完成编译、21 页目视检查、引用与标签检查、发行资源哈希及实际写作查询。文中 128 项回归、前序协作试验和固定证据改稿均引自已有记录，没有在本次重跑；没有新增模型性能实验，也未对药材源码做全部复算。原设计论文的独立审阅只适用于旧版本。本次使用 humanizer 整理文字，由同一作者代理自校。

附录中的开发仓库路径用于定位原始证据；本源码包不包含全部开发语料。具体文件身份和检查范围见 `qa.json`。
