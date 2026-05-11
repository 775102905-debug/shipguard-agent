# ShipGuard v0.5 Safe RAG / Knowledge Base 设计文档

## 概述

v0.5 在 History Store（v0.4）之上构建了脱敏的知识索引层，支持基于历史审查报告的相似检索、常见风险分析和整改建议生成。

## RAG 只基于脱敏 history summary

```
History Store (SQLite, 已脱敏)
  │
  ├─ rebuild_index() → 读取所有 history records
  │
  ├─ assert_safe_for_index() → 检查每条记录是否仍含敏感信息
  │
  ├─ 构建 KnowledgeDocument (内存索引)
  │
  ├─ search_similar_reports() → 关键词 + difflib 相似度
  │
  └─ generate_advise() → 聚合 fix plan + common risks + interview notes
```

关键约束：
- **RAG 不决定 PASS/REJECT**：knowledge 模块只提供信息检索和建议，不修改 verdict/score
- **所有数据已脱敏**：入索引前调用 `safety.assert_safe_for_index()` 二次校验
- **不索引原始 zip / 完整源码 / 未脱敏 markdown**

## 不保存什么

- ❌ 原始 ZIP
- ❌ 完整源码
- ❌ 未脱敏 Markdown 报告
- ❌ token / key / Authorization / Bearer
- ❌ 服务端绝对路径
- ❌ .env 内容

## 如何开启

```env
KNOWLEDGE_ENABLED=true
KNOWLEDGE_AUTO_INDEX=false
KNOWLEDGE_MAX_RESULTS=5
```

`KNOWLEDGE_AUTO_INDEX` 默认 `false`，用户需调用 `POST /api/knowledge/rebuild` 手动触发索引重建。

## 如何 rebuild index

```bash
curl -X POST http://127.0.0.1:8000/api/knowledge/rebuild
```

## 如何 search / advise

```bash
# 搜索相似报告
curl -X POST http://127.0.0.1:8000/api/knowledge/search \
  -H "Content-Type: application/json" \
  -d '{"query": "python backend security", "max_results": 5}'

# 获取整改建议
curl -X POST http://127.0.0.1:8000/api/knowledge/advise \
  -H "Content-Type: application/json" \
  -d '{"query": "python project", "max_results": 5}'
```

## 为什么 RAG 不决定 PASS/REJECT

1. **历史数据不代表当前质量**：之前 PASS 的项目不保证当前版本也 PASS
2. **RAG 检索存在偏差**：相似度算法可能遗漏或误匹配
3. **规则引擎是权威结论**：ShipGuard 的静态规则审查是确定的，不受 RAG 影响
4. **设计原则**：RAG 是辅助工具（建议参考），不是决策者（判定 pass/fail）

## LlamaIndex fallback 策略

当前版本：
- `KNOWLEDGE_USE_LLAMAINDEX=false`（默认）
- 使用关键词匹配 + `difflib.SequenceMatcher` 文本相似度
- 支持简单的分词匹配和模糊匹配

未来版本（v0.6+）：
- `KNOWLEDGE_USE_LLAMAINDEX=true` 时尝试引入 LlamaIndex
- 如果 LlamaIndex 不可用或导入失败，自动降级为当前关键词检索
- 不因为 LlamaIndex 缺失而阻断整个 knowledge 模块

## 持久化索引风险警告（v0.5.0 P1 关注项）

**当前 v0.5.0 知识索引为内存索引**：
- 索引保存在 `_index` 全局字典中
- 服务重启后需调用 `POST /api/knowledge/rebuild` 重新构建
- 不写入磁盘，不存在 `data/knowledge_index` 文件

**若未来 v0.6 引入持久化向量索引或外部向量库，必须重新做安全审计**：

| 风险 | 说明 |
|------|------|
| 数据泄露 | 持久化索引文件被 git 提交、被共享、被备份泄露 |
| 脱敏回溯 | 历史数据变更后索引未同步，导致旧敏感数据仍然可检索 |
| 索引注入 | 恶意构造的 history record 通过索引影响检索结果 |
| 路径泄露 | 索引文件路径暴露服务端目录结构 |
| 依赖漏洞 | 向量库/Embedding 模型引入 CVE |

**硬性要求**：
1. 持久化索引文件路径必须在 `.gitignore` 中，不允许提交；
2. 入库前必须调用 `redaction_service.redact()` 和 `safety.assert_safe_for_index()`；
3. 持久化索引的 SQLite/向量库路径必须使用配置项，不可硬编码；
4. 向量 Embedding 必须在沙箱环境中执行，不读取原始 zip 或源码；
5. `data/knowledge_index` 不允许提交到 git。

## MCP Knowledge Tools 安全边界

| Tool | 输入 | 输出 | 脱敏 |
|---|---|---|---|
| `knowledge_status` | 无 | 状态文本 | N/A |
| `search_reports` | query/max_results/review_mode | 脱敏搜索摘要 | `redact()` |
| `suggest_fix_plan` | query/max_results | 脱敏整改建议 | `redact()` |
| `generate_interview_notes` | query/max_results | 脱敏面试表达建议 | `redact()` |

所有 MCP knowledge tools：
- 只查询 History Store / 内存知识索引
- 不读取任意路径
- 不读取原始 zip
- 输出经过 `redaction_service.redact()`
- 不调用外部 LLM
- 不返回完整 markdown
- 不返回绝对路径
- 不决定 PASS/REJECT
