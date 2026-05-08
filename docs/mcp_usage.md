# ShipGuard MCP Server 使用说明

## MCP 是什么

MCP (Model Context Protocol) 是 Anthropic 推出的一种开放协议，用于让 AI 工具（如 Claude Desktop、Cursor、Trae）与外部服务和工具进行安全交互。

ShipGuard MCP Server 允许 AI 编程工具通过 MCP 协议调用 ShipGuard 的静态审查能力，从而在 AI 编码过程中自动完成项目交付质量评估。

## 如何启动

```bash
# 确保后端依赖已安装
pip install -r requirements.txt

# 启动 MCP Server（默认监听 127.0.0.1:8100）
python scripts/run_mcp_server.py
```

启动后，MCP Server 会在 `http://127.0.0.1:8100` 监听，支持 SSE (Server-Sent Events) 传输协议。

## 如何配置

在项目根目录 `.env` 中配置：

```
MCP_ENABLED=true
MCP_SAFE_UPLOAD_DIR=examples
MCP_MAX_ZIP_MB=50
```

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `MCP_ENABLED` | `false` | 是否启用 MCP Server |
| `MCP_SAFE_UPLOAD_DIR` | `examples` | 允许读取的 ZIP 文件目录（相对项目根目录） |
| `MCP_MAX_ZIP_MB` | `50` | ZIP 文件大小上限 |

## 安全边界

1. **路径白名单**：MCP 只能读取 `MCP_SAFE_UPLOAD_DIR` 目录下的 ZIP 文件，无法读取任意系统路径。
2. **文件类型限制**：只允许 `.zip` 后缀。
3. **文件大小限制**：`MCP_MAX_ZIP_MB` 控制上限。
4. **路径穿越防护**：使用 `Path.resolve()` 检测 zip slip 攻击。
5. **不执行代码**：只做静态文件扫描，不运行任何用户代码。
6. **输出脱敏**：所有 MCP 输出经过 `redaction_service.redact()` 脱敏，API 响应和 Markdown 报告也经过脱敏。
7. **不泄露路径**：错误信息不包含服务端绝对路径，白名单目录以相对路径形式展示。
8. **不建议公网暴露**：MCP Server 默认监听 127.0.0.1，仅供本地使用。

## 支持的 Tools

### 1. list_review_modes

返回支持的四种审查模式：

```
- student_assignment: 学生作业
- github_showcase: GitHub 展示项目
- interview_project: 面试项目
- commercial_delivery: 商业交付
```

### 2. review_zip

审查一个 ZIP 项目文件，返回评分摘要。

**参数**：
- `zip_path`：ZIP 文件路径（必须在安全白名单目录内）
- `review_mode`：审查模式（可选，默认 `student_assignment`）

**返回**：
```
审查模式: 学生作业
总分: 45/100
结论: REJECT
项目类型: python-backend
高危: 1, 中危: 14, 低危: 1
```

### 3. get_last_report

返回最近一次审查的摘要，无参数。

### 4. explain_fix_plan

基于最近一次审查结果生成分类整改建议，按 HIGH → MEDIUM 排序。

## 与 Cursor/Trae 集成

在 Cursor 或 Trae 中配置 MCP Server：

```json
{
  "mcpServers": {
    "shipguard": {
      "url": "http://127.0.0.1:8100"
    }
  }
}
```

然后 AI 编码助手即可调用 `review_zip` 等工具来自动审查项目交付质量。

## 不执行用户代码

ShipGuard MCP Server 只做静态文件扫描：
- 检查文件存在性
- 正则匹配危险模式
- 评分和评分规则
- 不解释、不编译、不运行任何用户代码

## 已知限制

1. **无认证**：MCP Server 默认仅监听 `127.0.0.1`，但公网暴露时无鉴权机制。
2. **大型 ZIP 内存占用**：`_run_review` 将整个 ZIP 读入内存 `BytesIO`，大文件场景下内存占用较高。
3. **高频调用需观察**：并发测试已验证 10 次并发调用不崩溃，但高频场景下的资源管理仍需实际使用验证。
4. **仅支持 SSE 传输**：当前使用 `FastMCP.run()` 的 SSE + HTTP 传输，未评估 HTTPS 或其他传输协议。
5. **只审查 zip**：MCP Server 当前只接受 `.zip` 格式的项目文件，不支持直接审查目录或代码仓库 URL。
6. **白名单目录可扩展**：`MCP_SAFE_UPLOAD_DIR` 虽然支持额外目录，但用户需自行确保新增目录的安全性。
