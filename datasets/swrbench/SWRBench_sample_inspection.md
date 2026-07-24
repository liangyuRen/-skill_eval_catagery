# SWR-Bench 真实样本结构说明

> 数据来源：`datasets/swrbench/sample_change_pr.json`（从官方 `data/swr_datasets_d5c5.jsonl` 前 488KB 中解析出的第一条 Change-PR）
> 论文：arXiv:2509.01494，FSE 2026
> 官方仓库：https://github.com/ZZR0/SWRench

## 1. 顶层字段

| 字段 | 类型 | 含义 |
|---|---|---|
| `repo` | string | 仓库名，例 `astropy/astropy` |
| `instance_id` | string | 唯一 ID，例 `astropy__astropy-187` |
| `pr_title` | string | PR 标题 |
| `pr_statement` | string | PR 描述/正文 |
| `change_introduced` | bool | **核心标签**：`true`=含引入的缺陷；`false`=Clean-PR（无缺陷） |
| `base_commit` | string | PR 基于的 commit sha |
| `created_at` | string | PR 创建时间 |
| `changes` | array | **Ground Truth**：每条是一个缺陷的 change-action |
| `pr_commits` | array | PR 所有 commit 的完整 diff，含 `diff_text` 与结构化 `diff[].patch` |
| `pr_timeline` | array | commits/reviews/comments 时间线 |
| `all_commits` | array | 仓库相关 commit 列表 |

## 2. GT（changes[]）字段详情

```json
{
  "change_type": "F.2 Logic",
  "change_introducing": {
    "code_snippet": "<diff 片段，引入问题的代码>",
    "commit_sha": "<引入问题的 commit>"
  },
  "change_discussion": {
    "discussion_summary": "<reviewer 与作者的讨论摘要>",
    "first_mention_timestamp": "<首次提及时间>",
    "original_reviewer_comment": "<reviewer 原始评论>"
  },
  "change_resolve_info": {
    "code_snippet": "<修复后的 diff 片段>",
    "commit_sha": "<修复 commit>",
    "resolution_explanation": "<修复说明>"
  }
}
```

change_type 的 taxonomy 来自 Beller 2014 / Fregnan 2022，分 F（Functional）和 E（Evolutionary）两大类，例：`F.2 Logic`、`E.3.2 Solution Approach`。详见仓库 README。

## 3. 当前样本的 GT 概览

- 仓库：`astropy/astropy`
- instance_id：`astropy__astropy-187`
- PR 标题：`Fix doc building to use astropy source`
- change_introduced：`True`
- GT 缺陷数：`1`

### 缺陷 #1
- **change_type**：`F.2 Logic`
- **original_reviewer_comment**：`Very welcome change.  For me, `python setup.py build_sphinx` seems to dump the built docs into `docs/docs/_build/html` rather than `docs/_build/html`.  Any idea why?...`
- **discussion_summary**：`Reviewer `mdboom` reported that the documentation build output was placed in an incorrect nested directory (`docs/docs/_build/html`). Reviewer `embray` confirmed seeing the same behavior. The author (`eteq`) later acknowledged the issue, identified the cause as changing the directory within the subp...`
- **resolution_explanation**：`The fix addresses the issue by ensuring that all directory paths (`iden` ending with `_dir`) passed into the subprocess code are converted to absolute paths using `os.path.abspath(val)`. This prevents the `os.chdir()` call within the subprocess from causing relative paths (like the build output dire...`

## 4. PR commits 结构
- 本 PR 共有 `8` 个 commit
- 每个 commit 含字段：type、sha、message、author、date、diff_text、diff[]
- 第一条 commit：sha=`b47c52ecf1bd46f0a2a361553f44aa8c70803171`，message=`cosmetic fixes in build_sphinx`
- `diff[].file` 为文件路径，`diff[].patch` 为标准化 unified diff

## 5. 如何获取完整数据

```bash
# 完整 jsonl 约 81MB（本环境下载极慢）
curl -L -o swr_datasets_d5c5.jsonl   https://raw.githubusercontent.com/ZZR0/SWRench/main/data/swr_datasets_d5c5.jsonl
# 或 git clone 仓库
```
