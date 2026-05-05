import type { ReviewResponse } from "../api";

interface ReportViewProps {
  response: ReviewResponse;
  onReset: () => void;
}

export default function ReportView({ response, onReset }: ReportViewProps) {
  const { report_markdown, total_score, verdict, findings_count } = response;

  const getVerdictEmoji = (v: string) => {
    switch (v) {
      case "PASS":
        return "✅";
      case "CONDITIONAL_PASS":
        return "⚠️";
      case "REJECT":
        return "❌";
      default:
        return "❓";
    }
  };

  const getVerdictColor = (v: string) => {
    switch (v) {
      case "PASS":
        return "#4caf50";
      case "CONDITIONAL_PASS":
        return "#ff9800";
      case "REJECT":
        return "#f44336";
      default:
        return "#888";
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 70) return "#4caf50";
    if (score >= 50) return "#ff9800";
    return "#f44336";
  };

  return (
    <div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "1.5rem",
        }}
      >
        <h2 style={{ color: "#e0e0e0", margin: 0 }}>审查报告</h2>
        <button
          onClick={onReset}
          style={{
            padding: "0.5rem 1.25rem",
            borderRadius: "8px",
            border: "1px solid #555",
            background: "transparent",
            color: "#ccc",
            cursor: "pointer",
            fontSize: "0.9rem",
          }}
        >
          返回上传
        </button>
      </div>

      <div
        style={{
          display: "flex",
          gap: "1.5rem",
          marginBottom: "1.5rem",
          flexWrap: "wrap",
        }}
      >
        <div
          style={{
            flex: 1,
            minWidth: "200px",
            padding: "1.25rem",
            borderRadius: "12px",
            background: "rgba(255,255,255,0.03)",
            border: "1px solid #333",
          }}
        >
          <div style={{ fontSize: "0.85rem", color: "#888", marginBottom: "0.25rem" }}>
            总分
          </div>
          <div style={{ fontSize: "2.5rem", fontWeight: 700, color: getScoreColor(total_score) }}>
            {total_score}
            <span style={{ fontSize: "1rem", color: "#666" }}>/100</span>
          </div>
        </div>
        <div
          style={{
            flex: 1,
            minWidth: "200px",
            padding: "1.25rem",
            borderRadius: "12px",
            background: "rgba(255,255,255,0.03)",
            border: "1px solid #333",
          }}
        >
          <div style={{ fontSize: "0.85rem", color: "#888", marginBottom: "0.25rem" }}>
            结论
          </div>
          <div style={{ fontSize: "1.5rem", fontWeight: 700, color: getVerdictColor(verdict) }}>
            {getVerdictEmoji(verdict)} {verdict}
          </div>
        </div>
        <div
          style={{
            flex: 1,
            minWidth: "200px",
            padding: "1.25rem",
            borderRadius: "12px",
            background: "rgba(255,255,255,0.03)",
            border: "1px solid #333",
          }}
        >
          <div style={{ fontSize: "0.85rem", color: "#888", marginBottom: "0.25rem" }}>
            问题统计
          </div>
          <div style={{ display: "flex", gap: "1rem", fontSize: "1.1rem" }}>
            <span style={{ color: "#f44336" }}>🔴 {findings_count.HIGH}</span>
            <span style={{ color: "#ff9800" }}>🟡 {findings_count.MEDIUM}</span>
            <span style={{ color: "#4caf50" }}>🟢 {findings_count.LOW}</span>
          </div>
        </div>
      </div>

      <div
        style={{
          background: "rgba(255,255,255,0.02)",
          border: "1px solid #333",
          borderRadius: "12px",
          padding: "1.5rem",
          overflow: "auto",
          maxHeight: "70vh",
        }}
      >
        <div
          className="markdown-body"
          style={{ color: "#d4d4d4", lineHeight: 1.7 }}
          dangerouslySetInnerHTML={{ __html: renderMarkdown(report_markdown) }}
        />
      </div>
    </div>
  );
}

function renderMarkdown(md: string): string {
  let html = md
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  html = html.replace(/^### (.+)$/gm, '<h3 style="color:#e0e0e0;margin-top:1.5rem;">$1</h3>');
  html = html.replace(/^## (.+)$/gm, '<h2 style="color:#e0e0e0;margin-top:1.5rem;">$1</h2>');
  html = html.replace(/^# (.+)$/gm, '<h1 style="color:#fff;margin-top:1rem;">$1</h1>');

  html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");

  html = html.replace(/^(\d+)\. /gm, "<br><strong>$1.</strong> ");

  html = html.replace(/^- (.+)$/gm, '<li style="margin:0.25rem 0;">$1</li>');

  html = html.replace(/^---$/gm, '<hr style="border-color:#444;margin:1rem 0;">');

  html = html.replace(
    /```([\s\S]*?)```/g,
    '<pre style="background:#1e1e1e;padding:1rem;border-radius:8px;overflow-x:auto;color:#ce9178;"><code>$1</code></pre>'
  );

  let tableOpen = false;
  const lines = html.split('\n');
  const resultLines: string[] = [];
  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith('|') && trimmed.endsWith('|') && trimmed.includes('|')) {
      if (trimmed.includes('---') || trimmed.includes(':---')) {
        continue;
      }
      if (!tableOpen) {
        resultLines.push('<table style="border-collapse:collapse;width:100%;margin:0.5rem 0;">');
        tableOpen = true;
      }
      const cells = trimmed.split('|').filter(c => c.trim()).map(c =>
        `<td style="padding:0.3rem 0.75rem;border:1px solid #444;color:#d4d4d4;">${c.trim()}</td>`
      );
      resultLines.push(`<tr>${cells.join('')}</tr>`);
    } else {
      if (tableOpen) {
        resultLines.push('</table>');
        tableOpen = false;
      }
      resultLines.push(line);
    }
  }
  if (tableOpen) resultLines.push('</table>');
  html = resultLines.join('\n');

  html = html.replace(/\n\n/g, '<br><br>');

  return html;
}
