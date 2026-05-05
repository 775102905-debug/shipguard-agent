# AI Delivery Inspector — 前端联调验证提示词

> 保存时间: 2026-05-05
> 红律第二轮运行时验证 trace_id: 61ddf804-9c0a-435a-9cda-5542a35f307e
> 用于后续复盘、迭代、优化

## 目标

完成前端联调，让项目前后端打通。

## 任务清单

1. 检查前端 API 调用
2. 完成页面交互
3. 联调测试（good/bad zip）
4. 体验要求

## 修改文件

| 文件 | 变更 |
|------|------|
| frontend/vite.config.ts | 添加 `server.host: '0.0.0.0'` 和 `server.port: 5173` |
| frontend/src/components/ReportView.tsx | 修复 Markdown 表格渲染（用 `<table>` 包裹，移除旧 regex） |
| frontend/src/api.ts | (之前已改) `VITE_API_BASE` 环境变量 |
| scripts/test_upload.py | 新建 — Python 联调脚本 |
| scripts/read_results.py | 新建 — 读取测试结果 |

## 验证结果

### Good Project
- 总分: 98/100, 结论: PASS
- HIGH=0, MED=2, LOW=0
- 前端展示 ✅

### Bad Project
- 总分: 23/100, 结论: REJECT
- HIGH=3, MED=12, LOW=1
- sk- 检测 ✅, .env 风险 ✅, 修复建议 ✅
- 缺少 README ✅, 缺少 .env.example ✅
- node_modules/ .git/ __pycache__/ dist/ 全部跳过 ✅
