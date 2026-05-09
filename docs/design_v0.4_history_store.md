# ShipGuard v0.4 History Store 设计文档

## 概述

History Store 是 ShipGuard v0.4.0 引入的历史报告存储、查询、对比和整改建议模块。它允许用户安全地保存脱敏审查报告摘要，并在后续审查中进行对比，追踪项目质量变化。

## 保存什么

- report_id (自动生成 UUID hex[:12])
- project_alias (脱敏)
- project_fingerprint (基于 project_type + languages + score 的 MD5)
- review_mode
- verdict + score
- dimension_scores (6 个维度评分)
- findings_summary (HIGH/MEDIUM/LOW 计数)
- top_*_findings (最多 5 条风险消息，已脱敏)
- commercial_fix_plan (规则型整改建议，已脱敏)
- project_type + detected_languages
- redaction_version
- created_at (ISO 8601)

## 不保存什么

- ❌ 原始 ZIP
- ❌ 完整源码
- ❌ 未脱敏 Markdown 报告
- ❌ 本地绝对路径
- ❌ token / key / Authorization / Bearer
- ❌ .env 内容
- ❌ 上传目录结构

## 存储方式

- 使用 SQLite 本地存储
- 数据库文件: `data/shipguard_history.sqlite`
- `data/` 和 `*.sqlite` 在 `.gitignore` 中
- 默认 `HISTORY_AUTO_SAVE=false`，用户知情后才启用自动保存

## 如何开启

在 `.env` 中配置：

```
HISTORY_ENABLED=true
HISTORY_AUTO_SAVE=true
```

### 手动保存

即使 `HISTORY_AUTO_SAVE=false`，用户仍可通过 API 显式保存：

```bash
curl -X POST http://127.0.0.1:8000/api/history/save-explicit \
  -H "Content-Type: application/json" \
  -d '{"review_result": {...}}'
```

## 如何清理历史数据

```bash
# SQLite 文件路径
backend/data/shipguard_history.sqlite

# 直接删除
rm backend/data/shipguard_history.sqlite

# 或通过空 saves 覆盖（SQLite 自动建表）
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/history/save` | 自动保存（仅在 AUTO_SAVE=true 时生效） |
| POST | `/api/history/save-explicit` | 显式保存（无视 AUTO_SAVE） |
| GET  | `/api/history/reports?limit=20&offset=0` | 列表 |
| GET  | `/api/history/reports/{report_id}` | 详情 |
| POST | `/api/history/compare` | 对比 `{"report_id_a": "...", "report_id_b": "..."}` |

## MCP Tools

| Tool | 说明 |
|------|------|
| `list_reports` | 返回历史报告列表 |
| `get_report` | 返回单个报告详情 |
| `compare_reports_tool` | 对比两次报告 |

## 对比服务输出

- previous_score / current_score / score_delta
- previous_verdict / current_verdict
- fixed_findings (已修复)
- new_findings (新增)
- persistent_findings (仍未解决)
- improved_dimensions
- regressed_dimensions
- next_fix_plan

## 为什么暂不接 LlamaIndex

1. 当前数据量不足以支持向量检索；
2. LlamaIndex 会增加依赖复杂度和攻击面；
3. SQLite LIKE 查询 + 规则对比已满足 v0.4 需求；
4. 未来版本评估语义搜索时再引入。

## 安全边界

1. 所有存储的 summary 字段经过 `redaction_service.redact()`；
2. 不保存原始 ZIP 或完整源码；
3. SQLite 文件在 `.gitignore` 中；
4. History 保存失败不影响主审查流程；
5. 默认 `HISTORY_AUTO_SAVE=false`，用户知情后才启用；
6. API 输出不包含 SQLite 绝对路径。
