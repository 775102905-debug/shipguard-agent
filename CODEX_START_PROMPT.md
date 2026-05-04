# Codex Start Prompt

请读取本仓库的 README.md、AGENTS.md、ROADMAP.md 和 .env.example。

先不要大改，先输出 CP1 最小实现计划。

MVP 目标：

1. FastAPI 后端
2. React + Vite 前端
3. 支持上传项目 zip
4. 安全解压并读取目录结构
5. 检查 README、.env.example、Dockerfile、docker-compose.yml、依赖文件、测试文件
6. 扫描 .env、API Key、token、数据库、日志等误提交风险
7. 生成 P0/P1/P2 问题清单
8. 生成可复制给 Trae/Cursor/Codex 的修复提示词
9. 导出 Markdown 报告

硬约束：

- V1 不自动修改用户上传项目
- V1 不做登录系统
- V1 不接 OCR
- V1 不强依赖付费 API
- 不输出真实 secret，只能输出脱敏结果
- 每个 finding 必须包含 evidence_file、severity、reason、suggested_fix

