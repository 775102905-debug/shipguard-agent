import { useState, useCallback, type DragEvent } from "react";

interface UploadPanelProps {
  onUpload: (file: File) => void;
  uploading: boolean;
}

export default function UploadPanel({ onUpload, uploading }: UploadPanelProps) {
  const [dragOver, setDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleDragOver = useCallback((e: DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setDragOver(false);
  }, []);

  const handleDrop = useCallback((e: DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file && file.name.endsWith(".zip")) {
      setSelectedFile(file);
    }
  }, []);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
    }
  }, []);

  const handleSubmit = () => {
    if (selectedFile) {
      onUpload(selectedFile);
    }
  };

  return (
    <div
      style={{
        border: `2px dashed ${dragOver ? "#7c5cfc" : "#444"}`,
        borderRadius: "12px",
        padding: "3rem 2rem",
        textAlign: "center",
        background: dragOver ? "rgba(124, 92, 252, 0.05)" : "transparent",
        transition: "all 0.3s ease",
        marginBottom: "1.5rem",
      }}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <div style={{ fontSize: "3rem", marginBottom: "1rem" }}>📦</div>
      <p style={{ color: "#ccc", marginBottom: "1rem" }}>
        {selectedFile
          ? `已选择: ${selectedFile.name} (${(selectedFile.size / 1024 / 1024).toFixed(2)} MB)`
          : "拖拽 ZIP 文件到此处，或点击下方按钮选择"}
      </p>
      <div style={{ display: "flex", gap: "1rem", justifyContent: "center", alignItems: "center" }}>
        <label
          style={{
            display: "inline-block",
            padding: "0.6rem 1.5rem",
            borderRadius: "8px",
            background: "#333",
            color: "#fff",
            cursor: "pointer",
            fontSize: "0.95rem",
            transition: "background 0.2s",
          }}
        >
          选择 ZIP 文件
          <input
            type="file"
            accept=".zip"
            onChange={handleFileSelect}
            style={{ display: "none" }}
          />
        </label>
        {selectedFile && (
          <button
            onClick={handleSubmit}
            disabled={uploading}
            style={{
              padding: "0.6rem 1.5rem",
              borderRadius: "8px",
              border: "none",
              background: uploading ? "#555" : "#7c5cfc",
              color: "#fff",
              cursor: uploading ? "not-allowed" : "pointer",
              fontSize: "0.95rem",
              fontWeight: 600,
              transition: "background 0.2s",
            }}
          >
            {uploading ? "审查中..." : "开始审查"}
          </button>
        )}
      </div>
      <p style={{ color: "#666", fontSize: "0.8rem", marginTop: "0.75rem" }}>
        支持 .zip 格式，最大 50MB
      </p>
    </div>
  );
}
