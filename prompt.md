# AI Delivery Inspector — 项目初始提示词

> 保存时间: 2026-05-05
> 用于后续复盘、迭代、优化

## 项目目标

用户上传一个 AI 项目源码 zip，系统自动解析项目结构，执行交付完整性、安全风险、依赖配置、README 文档、部署材料等多维度审查，并输出一份 Markdown 格式的交付审查报告。

## 技术栈要求

1. 后端使用 Python + FastAPI。
2. 工作流使用 LangGraph，但第一版可以用规则节点为主，LLM 节点预留接口。
3. 前端使用 React + Vite。
4. 第一版不需要数据库。
5. 第一版不需要登录系统。
6. 第一版不需要真实运行用户上传的代码。
7. 第一版只支持上传 .zip 项目包。
8. 第一版重点支持 Python/FastAPI/LangGraph/RAG/Agent 项目，以及 React/Vite 前端项目。
9. 必须提供 .env.example、README.md、requirements.txt、docker-compose.yml。
10. 所有路径处理必须使用 pathlib，禁止硬编码本地绝对路径。
11. 请把本次提示词保存为 md 文档，以供后续复盘、迭代、优化。

## MVP 功能

1. 前端提供上传 zip 的页面。
2. 用户可以选择审查模式：
   - student_assignment
   - github_showcase
   - interview_project
   - commercial_delivery
3. 后端提供 POST /api/review 接口，接收 zip 文件和 review_mode。
4. 后端解压 zip 到临时目录。
5. 解压前后必须做安全校验，防止 zip slip 路径穿越。
6. 默认忽略以下目录：
   .git, node_modules, .venv, venv, __pycache__, dist, build, .next, .cache, logs, data, uploads, tmp, .pytest_cache
7. 自动寻找工程根目录：优先寻找包含 README.md、requirements.txt、pyproject.toml、package.json、Dockerfile、docker-compose.yml 的目录。
8. 生成项目画像，包括：
   - project_type
   - has_backend
   - has_frontend
   - detected_languages
   - detected_frameworks
   - key_files
9. 执行结构审查：
   - README.md
   - requirements.txt / pyproject.toml / package.json
   - .env.example
   - .gitignore
   - Dockerfile
   - docker-compose.yml
   - tests/
   - LICENSE
10. 执行安全审查：
    - 疑似 API key/token
    - sk-
    - ghp_
    - AKIA
    - SECRET
    - PASSWORD
    - Bearer
    - Authorization
    - C:\Users\
    - /Users/
    - debug=True
    - DEBUG=True
    - CORS *
11. 执行依赖审查：
    - Python 项目检查 requirements.txt 或 pyproject.toml 是否存在
    - Node 项目检查 package.json 是否存在
    - 不需要做复杂 AST，只做 MVP 级别规则检查
12. 执行 README 审查：
    - 是否有项目简介
    - 是否有环境要求
    - 是否有安装步骤
    - 是否有运行命令
    - 是否有测试说明
    - 是否有配置说明
13. 根据评分规则生成总分：
    - 交付物完整性 20 分
    - 安全风险 25 分
    - 运行与依赖配置 20 分
    - README 文档质量 15 分
    - Docker / 部署说明 10 分
    - 项目结构与可维护性 10 分
14. 输出结论：
    - PASS
    - CONDITIONAL_PASS
    - REJECT
15. 输出 Markdown 报告，包含：
    - 总分
    - 审查模式
    - 项目画像
    - 风险等级
    - 文件完整度清单
    - 高危问题
    - 中危问题
    - 低危问题
    - 修复建议
    - 可复制给 Trae/Cursor 的修复 Prompt

## 验收标准

1. 能启动后端 FastAPI。
2. 能启动前端 React。
3. 上传 zip 后能返回 Markdown 审查报告。
4. 上传包含 .env 的项目时，报告必须提示风险，但不要读取和展示 .env 的真实内容。
5. 上传包含 node_modules 的项目时，扫描必须跳过 node_modules。
6. 上传包含 C:\Users\ 或 /Users/ 的代码时，报告必须提示路径硬编码风险。
7. 上传缺少 README 的项目时，报告必须扣分。
8. 上传缺少 .env.example 的项目时，报告必须扣分。
9. 代码不得硬编码本机路径。
10. 所有临时解压目录在审查结束后应尽量清理。
11. 不要引入复杂数据库、登录、GitHub OAuth、沙箱运行、自动修复 PR。
