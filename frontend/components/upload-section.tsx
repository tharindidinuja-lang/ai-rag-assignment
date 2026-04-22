"use client";

import { useState } from "react";

export function UploadSection() {
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState("");

  const handleUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    setUploading(true);
    setMessage("Uploading...");

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append("files", files[i]);
    }

    try {
      const response = await fetch("http://localhost:8001/api/v1/upload/upload", {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        setMessage(`✅ ${result.message}`);
        
        // Rebuild index after upload
        await fetch("http://localhost:8001/api/v1/ingest/rebuild", {
          method: "POST",
        });
        setMessage(`✅ Uploaded! Index rebuilt. You can now ask questions about your file.`);
      } else {
        setMessage("❌ Upload failed");
      }
    } catch (error) {
      setMessage("❌ Error uploading file");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="upload-section" style={{ marginBottom: "20px" }}>
      <label
        className="upload-button"
        style={{
          display: "inline-block",
          background: "#0f766e",
          color: "white",
          padding: "10px 20px",
          borderRadius: "8px",
          cursor: "pointer",
          fontSize: "14px",
          fontWeight: "500",
        }}
      >
        📁 Upload Files (PDF, DOCX, TXT, ZIP - max 5MB)
        <input
          type="file"
          multiple
          accept=".pdf,.docx,.txt,.zip"
          onChange={handleUpload}
          disabled={uploading}
          style={{ display: "none" }}
        />
      </label>
      {message && (
        <p style={{ marginTop: "10px", fontSize: "14px", color: "#64594c" }}>
          {message}
        </p>
      )}
    </div>
  );
}
