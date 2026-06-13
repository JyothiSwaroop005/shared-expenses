import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getMySummary } from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function Dashboard() {
  const { user } = useAuth();
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    getMySummary()
      .then((res) => setSummary(res.data))
      .catch(() => setError("Could not load summary"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-gray-500 text-sm">Loading…</p>;
  if (error) return <p className="text-red-500 text-sm">{error}</p>;

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-800 mb-1">
        Hi, {user?.name} 👋
      </h1>
      <p className="text-gray-500 text-sm mb-6">Here's your balance summary across all groups.</p>

      {/* Top-level numbers */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <div className="bg-green-50 border border-green-200 rounded-xl p-4">
          <p className="text-xs text-green-600 font-medium uppercase tracking-wide">You are owed</p>
          <p className="text-2xl font-bold text-green-700 mt-1">
            ₹{summary.total_owed_to_me.toFixed(2)}
          </p>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-xl p-4">
          <p className="text-xs text-red-600 font-medium uppercase tracking-wide">You owe</p>
          <p className="text-2xl font-bold text-red-700 mt-1">
            ₹{summary.total_i_owe.toFixed(2)}
          </p>
        </div>
        <div className={`border rounded-xl p-4 ${summary.net >= 0 ? "bg-blue-50 border-blue-200" : "bg-orange-50 border-orange-200"}`}>
          <p className="text-xs font-medium uppercase tracking-wide text-gray-500">Net</p>
          <p className={`text-2xl font-bold mt-1 ${summary.net >= 0 ? "text-blue-700" : "text-orange-700"}`}>
            {summary.net >= 0 ? "+" : ""}₹{summary.net.toFixed(2)}
          </p>
        </div>
      </div>

      {/* Per-group breakdown */}
      <h2 className="text-lg font-semibold text-gray-700 mb-3">By Group</h2>
      {summary.groups.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-6 text-center">
          <p className="text-gray-500 text-sm">You're not in any groups yet.</p>
          <Link to="/groups" className="mt-2 inline-block text-indigo-600 text-sm font-medium hover:underline">
            Create a group →
          </Link>
        </div>
      ) : (
        <div className="space-y-2">
          {summary.groups.map((g) => (
            <Link
              key={g.group_id}
              to={`/groups/${g.group_id}`}
              className="flex items-center justify-between bg-white border border-gray-200 rounded-xl px-4 py-3 hover:border-indigo-300 transition-colors"
            >
              <span className="font-medium text-gray-700">{g.group_name}</span>
              <span className={`text-sm font-semibold ${
                g.status === "owed" ? "text-green-600" :
                g.status === "owes" ? "text-red-500" : "text-gray-400"
              }`}>
                {g.status === "owed" && `+₹${g.my_balance.toFixed(2)}`}
                {g.status === "owes" && `-₹${Math.abs(g.my_balance).toFixed(2)}`}
                {g.status === "settled" && "✓ Settled"}
              </span>
            </Link>
          ))}
        </div>
      )}

      {/* Quick links */}
      <div className="mt-8 grid grid-cols-2 gap-3">
        <Link to="/import" className="bg-indigo-600 text-white rounded-xl p-4 text-center hover:bg-indigo-700 transition-colors">
          <p className="text-lg">📂</p>
          <p className="text-sm font-medium mt-1">Import CSV</p>
        </Link>
        <Link to="/anomalies" className="bg-yellow-500 text-white rounded-xl p-4 text-center hover:bg-yellow-600 transition-colors">
          <p className="text-lg">⚠️</p>
          <p className="text-sm font-medium mt-1">Review Anomalies</p>
        </Link>
      </div>
    </div>
  );
}
