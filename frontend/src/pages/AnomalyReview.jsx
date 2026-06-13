import React, { useEffect, useState } from "react";
import { getPendingAnomalies, reviewAnomaly } from "../api/client";

const TYPE_LABELS = {
  duplicate_expense: "Duplicate",
  missing_payer: "Missing Payer",
  payer_not_in_group: "Payer Not In Group",
  invalid_amount: "Invalid Amount",
  negative_amount: "Negative Amount",
  zero_amount: "Zero Amount",
  future_date: "Future Date",
  invalid_date: "Invalid Date",
  invalid_currency: "Invalid Currency",
  unknown_split_type: "Unknown Split Type",
  group_not_found: "Group Not Found",
  user_not_found: "User Not Found",
  participant_not_in_group: "Participant Not In Group",
  percentage_sum_not_100: "Percentages ≠ 100%",
  exact_sum_mismatch: "Exact Sum Mismatch",
  settlement_as_expense: "Settlement as Expense",
  missing_participants: "Missing Participants",
};

export default function AnomalyReview() {
  const [anomalies, setAnomalies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(null);

  const fetchPending = () =>
    getPendingAnomalies()
      .then((r) => setAnomalies(r.data))
      .finally(() => setLoading(false));

  useEffect(() => { fetchPending(); }, []);

  const handleReview = async (id, decision) => {
    setProcessing(id);
    try {
      await reviewAnomaly(id, decision);
      setAnomalies((prev) => prev.filter((a) => a.id !== id));
    } catch {
      alert("Could not update anomaly");
    } finally {
      setProcessing(null);
    }
  };

  if (loading) return <p className="text-gray-500 text-sm">Loading…</p>;

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-800 mb-1">Anomaly Review</h1>
      <p className="text-gray-500 text-sm mb-6">
        These rows were flagged during CSV import and need your decision before they are acted on.
      </p>

      {anomalies.length === 0 ? (
        <div className="bg-white border border-gray-200 rounded-xl p-8 text-center">
          <p className="text-2xl mb-2">✅</p>
          <p className="text-gray-600 font-medium">No pending anomalies</p>
          <p className="text-gray-400 text-sm mt-1">All flagged rows have been reviewed.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {anomalies.map((a) => (
            <div key={a.id} className="bg-white border border-yellow-200 rounded-xl p-5">
              <div className="flex items-start justify-between gap-4 mb-3">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-mono text-gray-400">Row {a.row_number}</span>
                    <span className="text-xs bg-yellow-100 text-yellow-700 px-2 py-0.5 rounded-full font-medium">
                      {TYPE_LABELS[a.anomaly_type] || a.anomaly_type}
                    </span>
                  </div>
                  <p className="text-sm text-gray-800">{a.description}</p>
                </div>
              </div>

              {/* Show raw CSV data for Rohan's traceability requirement */}
              {a.raw_data && (
                <details className="mb-3">
                  <summary className="text-xs text-indigo-600 cursor-pointer hover:underline">View raw CSV row</summary>
                  <div className="mt-2 bg-gray-50 rounded p-3 text-xs font-mono text-gray-600 overflow-x-auto">
                    {Object.entries(a.raw_data).map(([k, v]) => (
                      <div key={k}><span className="text-gray-400">{k}:</span> {v}</div>
                    ))}
                  </div>
                </details>
              )}

              <div className="flex gap-2">
                <button
                  onClick={() => handleReview(a.id, "approved")}
                  disabled={processing === a.id}
                  className="bg-green-600 text-white px-3 py-1.5 rounded-lg text-xs font-medium hover:bg-green-700 disabled:opacity-50"
                >
                  ✓ Approve & Import
                </button>
                <button
                  onClick={() => handleReview(a.id, "rejected")}
                  disabled={processing === a.id}
                  className="bg-red-500 text-white px-3 py-1.5 rounded-lg text-xs font-medium hover:bg-red-600 disabled:opacity-50"
                >
                  ✗ Reject & Skip
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
