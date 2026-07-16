# 维护与更新

本页供 sansanskill 仓库维护者使用。

## 新增朋友圈案例

优先运行：

```bash
python3 tools/add-case.py --type 反馈圈 --title "案例标题"
```

## 新增商业原子

优先运行：

```bash
python3 tools/add-business-atom.py --type principle --title "原子标题"
```

## 重新构建

填写真源文件后运行：

```bash
./tools/build-release.sh
```

构建流程会重新生成原子库和知识包，检查数量、编号、来源、权利状态和路由，校验已经上线的 Skill，并生成独立安装包与系统整包。
