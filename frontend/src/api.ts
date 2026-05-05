const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

export interface ReviewResponse {
  report_markdown: string;
  total_score: number;
  verdict: "PASS" | "CONDITIONAL_PASS" | "REJECT";
  project_profile: Record<string, unknown>;
  findings_count: {
    HIGH: number;
    MEDIUM: number;
    LOW: number;
  };
}

export async function submitReview(
  file: File,
  reviewMode: string
): Promise<ReviewResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("review_mode", reviewMode);

  const response = await fetch(`${API_BASE}/api/review`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || "审查请求失败");
  }

  return response.json();
}
