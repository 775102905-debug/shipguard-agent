import { useState } from "react";
import UploadPanel from "./components/UploadPanel";
import ReviewModeSelect from "./components/ReviewModeSelect";
import ReportView from "./components/ReportView";
import { submitReview, type ReviewResponse } from "./api";

type Phase = "upload" | "reviewing" | "result";

export default function App() {
  const [phase, setPhase] = useState<Phase>("upload");
  const [reviewMode, setReviewMode] = useState("student_assignment");
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<ReviewResponse | null>(null);

  const handleUpload = async (file: File) => {
    setError(null);
    setPhase("reviewing");
    try {
      const result = await submitReview(file, reviewMode);
      setResponse(result);
      setPhase("result");
    } catch (err) {
      setError(err instanceof Error ? err.message : "未知错误");
      setPhase("upload");
    }
  };

  const handleReset = () => {
    setResponse(null);
    setError(null);
    setPhase("upload");
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#121212",
        color: "#e0e0e0",
        fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
      }}
    >
      <header
        style={{
          borderBottom: "1px solid #333",
          padding: "1.25rem 2rem",
          display: "flex",
          alignItems: "center",
          gap: "0.75rem",
        }}
      >
        <span style={{ fontSize: "1.75rem" }}>🛡️</span>
        <div>
          <h1 style={{ margin: 0, fontSize: "1.25rem", color: "#fff" }}>
            AI Delivery Inspector
          </h1>
          <p style={{ margin: 0, fontSize: "0.85rem", color: "#888" }}>
            AI 项目交付审查官
          </p>
        </div>
      </header>

      <main
        style={{
          maxWidth: "900px",
          margin: "2rem auto",
          padding: "0 1.5rem",
        }}
      >
        {phase === "upload" && (
          <>
            <ReviewModeSelect value={reviewMode} onChange={setReviewMode} />
            <UploadPanel onUpload={handleUpload} uploading={false} />
            {error && (
              <div
                style={{
                  padding: "1rem",
                  borderRadius: "8px",
                  background: "rgba(244,67,54,0.1)",
                  border: "1px solid #f44336",
                  color: "#f44336",
                  marginTop: "1rem",
                }}
              >
                ❌ {error}
              </div>
            )}
          </>
        )}

        {phase === "reviewing" && (
          <div
            style={{
              textAlign: "center",
              padding: "4rem 2rem",
            }}
          >
            <div
              style={{
                fontSize: "3rem",
                marginBottom: "1.5rem",
                animation: "spin 1.5s linear infinite",
              }}
            >
              🔍
            </div>
            <h2 style={{ color: "#e0e0e0", margin: "0 0 0.5rem" }}>
              正在审查项目...
            </h2>
            <p style={{ color: "#888", margin: 0 }}>
              正在解析项目结构、检查安全风险、评估文档质量
            </p>
            <div
              style={{
                marginTop: "2rem",
                width: "100%",
                maxWidth: "400px",
                height: "4px",
                background: "#333",
                borderRadius: "2px",
                overflow: "hidden",
                marginLeft: "auto",
                marginRight: "auto",
              }}
            >
              <div
                style={{
                  width: "30%",
                  height: "100%",
                  background: "#7c5cfc",
                  borderRadius: "2px",
                  animation: "loading 1.5s ease-in-out infinite",
                }}
              />
            </div>
          </div>
        )}

        {phase === "result" && response && (
          <ReportView response={response} onReset={handleReset} />
        )}
      </main>

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        @keyframes loading {
          0%, 100% { width: 20%; margin-left: 0; }
          50% { width: 80%; margin-left: 20%; }
        }
      `}</style>
    </div>
  );
}
