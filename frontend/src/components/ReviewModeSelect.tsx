const REVIEW_MODES = [
  {
    value: "student_assignment",
    label: "学生作业",
    description: "适合学生提交的课程项目作业审查",
  },
  {
    value: "github_showcase",
    label: "GitHub 展示项目",
    description: "适合 GitHub 上的个人开源展示项目",
  },
  {
    value: "interview_project",
    label: "面试项目",
    description: "适合求职面试中提交的项目作品",
  },
  {
    value: "commercial_delivery",
    label: "商业交付",
    description: "适合企业级商业项目交付审查（标准最严格）",
  },
];

interface ReviewModeSelectProps {
  value: string;
  onChange: (value: string) => void;
}

export default function ReviewModeSelect({ value, onChange }: ReviewModeSelectProps) {
  return (
    <div style={{ marginBottom: "1.5rem" }}>
      <label
        style={{
          display: "block",
          marginBottom: "0.5rem",
          fontWeight: 600,
          color: "#e0e0e0",
        }}
      >
        审查模式
      </label>
      <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
        {REVIEW_MODES.map((mode) => (
          <label
            key={mode.value}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.75rem",
              padding: "0.75rem 1rem",
              borderRadius: "8px",
              border: `2px solid ${value === mode.value ? "#7c5cfc" : "#333"}`,
              background: value === mode.value ? "rgba(124, 92, 252, 0.1)" : "transparent",
              cursor: "pointer",
              transition: "all 0.2s ease",
            }}
          >
            <input
              type="radio"
              name="review_mode"
              value={mode.value}
              checked={value === mode.value}
              onChange={(e) => onChange(e.target.value)}
              style={{ accentColor: "#7c5cfc" }}
            />
            <div>
              <div style={{ fontWeight: 600, color: "#e0e0e0" }}>{mode.label}</div>
              <div style={{ fontSize: "0.85rem", color: "#888" }}>{mode.description}</div>
            </div>
          </label>
        ))}
      </div>
    </div>
  );
}
