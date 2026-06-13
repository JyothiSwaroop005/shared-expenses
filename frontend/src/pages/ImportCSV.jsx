import React, { useState, useEffect } from "react";
import { uploadCSV, listImportSessions } from "../api/client";

const ACTION_COLORS = {
  skipped: "bg-red-50 text-red-600",
  pending_review: "bg-yellow-50 text-yellow-700",
  imported_with_warning: "bg-blue-50 text-blue-600",
  rejected: "bg-gray-100 text-gray-500",
};

export default function ImportCSV() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    listImportSessions().then((r) => setSessions(r.data));
  }, []);

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;
    setLoading(true);
    setError("");
    setResult(null);
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await uploadCSV(formData);
      setResult(res.data);
      listImportSessions().then((r) => setSessions(r.data));
    } catch (err) {
      setError(err.response?.data?.detail || "Upload failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-800 mb-6">Import CSV</h1>

      {/* Upload form */}
      <form onSubmit={handleUpload} className="bg-white border border-gray-200 rounded-xl p-5 mb-6">
        <h2 className="font-semibold text-gray-700 mb-3">Upload expenses_export.csv</h2>
        <div className="flex items-center gap-3">
          <input
            type="file"
            accept=".csv"
            onChange={(e) => setFile(e.target.files[0])}
            className="text-sm text-gray-600 file:mr-3 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-indigo-50 file:text-indigo-700 file:font-medium hover:file:bg-indigo-100"
          />
          <button
            type="submit"
            disabled={!file || loading}
            className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50"
          >
            {loading ? "Importing…" : "Import"}
          </button>
        </div>
        {error && <p className="text-red-500 text-sm mt-3">{error}</p>}
      </form>

      {/* Import result */}
      {result && (
        <div className="bg-white border border-gray-200 rounded-xl p-5 mb-6">
          <h2 className="font-semibold text-gray-700 mb-3">Import Report — {result.filename}</h2>
          <div className="grid grid-cols-4 gap-3 mb-4">
            {[
              { label: "Total Rows", value: result.total_rows, color: "bg-gray-50" },
              { label: "Imported", value: result.imported_rows, color: "bg-green-50 text-green-700" },
              { label: "Skipped", value: result.skipped_rows, color: "bg-red-50 text-red-600" },
              { label: "Anomalies", value: result.anomaly_count, color: "bg-yellow-50 text-yellow-700" },
            ].map((s) => (
              <div key={s.label} className={`${s.color} rounded-lg p-3 text-center`}>
                <p className="text-2xl font-bold">{s.value}</p>
                <p className="text-xs font-medium mt-1">{s.label}</p>
              </div>
            ))}
          </div>

          {result.anomalies.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-gray-600 mb-2">Detected Anomalies</h3>
              <div className="space-y-2 max-h-80 overflow-y-auto">
                {result.anomalies.map((a) => (
                  <div key={a.id} className="border border-gray-100 rounded-lg p-3">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <span className="text-xs font-mono text-gray-400">Row {a.row_number}</span>
                        <span className="ml-2 text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded">{a.anomaly_type}</span>
                        <p className="text-sm text-gray-700 mt-1">{a.description}</p>
                      </div>
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium whitespace-nowrap ${ACTION_COLORS[a.action_taken] || "bg-gray-100 text-gray-500"}`}>
                        {a.action_taken.replace(/_/g, " ")}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Past sessions */}
      <h2 className="font-semibold text-gray-700 mb-3">Past Import Sessions</h2>
      {sessions.length === 0 ? (
        <p className="text-gray-400 text-sm">No imports yet.</p>
      ) : (
        <div className="space-y-2">
          {sessions.map((s) => (
            <div key={s.id} className="bg-white border border-gray-200 rounded-xl px-4 py-3 flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-800">{s.filename}</p>
                <p className="text-xs text-gray-400">{new Date(s.created_at).toLocaleString()}</p>
              </div>
              <div className="text-right text-xs text-gray-500">
                <p>{s.imported_rows}/{s.total_rows} imported</p>
                <p className={s.anomaly_count > 0 ? "text-yellow-600 font-medium" : ""}>{s.anomaly_count} anomalies</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
