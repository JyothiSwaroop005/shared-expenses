import React, { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { listGroups, getGroupBalances } from "../api/client";

export default function Balances() {
  const [searchParams] = useSearchParams();
  const defaultGroup = searchParams.get("group") || "";
  const [groups, setGroups] = useState([]);
  const [selectedGroup, setSelectedGroup] = useState(defaultGroup);
  const [balances, setBalances] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    listGroups().then((r) => setGroups(r.data));
  }, []);

  useEffect(() => {
    if (!selectedGroup) return;
    setLoading(true);
    getGroupBalances(selectedGroup)
      .then((r) => setBalances(r.data))
      .catch(() => setError("Could not load balances"))
      .finally(() => setLoading(false));
  }, [selectedGroup]);

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-800 mb-6">Balances</h1>

      <select
        value={selectedGroup}
        onChange={(e) => { setSelectedGroup(e.target.value); setBalances(null); }}
        className="border border-gray-300 rounded-lg px-3 py-2 text-sm mb-6 focus:outline-none focus:ring-2 focus:ring-indigo-400"
      >
        <option value="">Select a group…</option>
        {groups.map((g) => <option key={g.id} value={g.id}>{g.name}</option>)}
      </select>

      {loading && <p className="text-gray-500 text-sm">Calculating…</p>}
      {error && <p className="text-red-500 text-sm">{error}</p>}

      {balances && (
        <div className="space-y-6">
          {/* Simplified view — Aisha's requirement */}
          <div className="bg-white border border-gray-200 rounded-xl p-5">
            <h2 className="font-semibold text-gray-700 mb-1">Who Pays Whom</h2>
            <p className="text-xs text-gray-400 mb-4">Minimum transactions to settle all debts</p>
            {balances.simplified_transactions.length === 0 ? (
              <p className="text-green-600 text-sm font-medium">✓ All settled up!</p>
            ) : (
              <div className="space-y-2">
                {balances.simplified_transactions.map((t, i) => (
                  <div key={i} className="flex items-center gap-2 text-sm">
                    <span className="font-medium text-red-600">{t.from_user_name}</span>
                    <span className="text-gray-400">pays</span>
                    <span className="font-medium text-green-700">{t.to_user_name}</span>
                    <span className="ml-auto font-bold text-gray-800">₹{t.amount.toFixed(2)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Raw balances — Rohan's requirement */}
          <div className="bg-white border border-gray-200 rounded-xl p-5">
            <h2 className="font-semibold text-gray-700 mb-1">Individual Balances</h2>
            <p className="text-xs text-gray-400 mb-4">Net position for each person</p>
            <div className="space-y-2">
              {balances.raw_balances.map((b) => (
                <div key={b.user_id} className="flex items-center justify-between text-sm">
                  <span className="text-gray-700 font-medium">{b.user_name}</span>
                  <span className={`font-bold ${
                    b.status === "owed" ? "text-green-600" :
                    b.status === "owes" ? "text-red-500" : "text-gray-400"
                  }`}>
                    {b.status === "owed" && `+₹${b.balance.toFixed(2)}`}
                    {b.status === "owes" && `-₹${Math.abs(b.balance).toFixed(2)}`}
                    {b.status === "settled" && "₹0.00"}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
