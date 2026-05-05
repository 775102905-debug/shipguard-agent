# AI Delivery Inspector — AI 项目交付审查官

自动审查 AI 项目源码的交付完整性、安全风险和文档质量的智能系统。

## 功能

- 上传项目 ZIP 包，自动解析项目结构
- 四种审查模式：学生作业、GitHub 展示、面试项目、商业交付
- 多维度审查：交付完整性、安全风险、依赖配置、README 文档、部署材料
- 自动生成 Markdown 审查报告
- 基于 LangGraph 的工作流引擎，支持后续扩展 LLM 节点

## 技术栈

- **后端**: Python + FastAPI + LangGraph
- **前端**: React + Vite + TypeScript
- **数据库**: 第一版无需数据库

## 环境要求

- Python 3.10+
- Node.js 18+

## 安装与运行

### 后端

```bash
cd backend
pip install -r ../requirements.txt
python main.py
```

后端默认运行在 http://localhost:8000

### 前端

```bash
cd frontend
npm install
npm run dev
```

前端默认运行在 http://localhost:5173

## 配置

复制 `.env.example` 为 `.env` 并根据需要修改配置：

```bash
cp .env.example .env
```

## API 接口

### POST /api/review

上传项目 ZIP 包进行审查。

**参数:**
- `file`: ZIP 文件
- `review_mode`: 审查模式（student_assignment / github_showcase / interview_project / commercial_delivery）

**返回:** Markdown 格式审查报告

## Docker 部署

```bash
docker-compose up --build
```

## 许可证

MIT
