# AI Delivery Inspector — 运行时联调验证提示词

> 保存时间: 2026-05-05
> 红律第一轮审查 trace_id: fddf0865-74e7-4d73-8200-6db315350435
> 用于后续复盘、迭代、优化

## 目标

完成运行时联调验证，让项目从"代码结构通过"进入"真实可运行 MVP"。

## 任务清单

1. 确认后端 FastAPI 可启动：
   - 检查 backend/main.py
   - 检查 /health
   - 检查 POST /api/review
   - 统一前后端 API 地址为 http://127.0.0.1:8000

2. 完成前端联调：
   - 上传 zip
   - 选择 review_mode
   - 调用 POST /api/review
   - 展示返回的 Markdown 报告
   - 展示错误信息

3. 增加最小测试样例：
   - scripts/create_test_zips.py 自动生成 good_project.zip 和 bad_project.zip
   - bad_project 包含：缺少 README、缺少 .env.example、C:\Users\fake\path、sk-test-not-real、node_modules

4. 增加最小验证脚本：
   - scripts/smoke_test.py
   - 验证：/health、good_project.zip、bad_project.zip

5. 安全要求：
   - .env 只能报告风险，不能读取或展示内容
   - 跳过 node_modules、.git、.venv、dist、build、__pycache__
   - 使用 pathlib，不硬编码绝对路径

## 验证结果

全部 25 项检查通过。

### Good Project (well-structured)
- 总分: 98/100
- 结论: PASS
- README ✅、.env.example ✅、Dockerfile ✅

### Bad Project (intentionally broken)
- 总分: 23/100
- 结论: REJECT
- 高危: 3（sk- API Key、ghp_ Token 等）
- 中危: 12（路径硬编码、.env 文件、缺少关键文件等）
- 低危: 1
- 忽略目录验证: node_modules ✅ .git ✅ __pycache__ ✅ dist ✅
- .env 安全处理: 只报告风险，不读取内容 ✅
