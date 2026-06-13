import React, { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { listGroups, listGroupSettlements, recordSettlement, listUsers } from "../api/client";

export default function Settlements() {
  const [searchParams] = useSearchParams();
  const defaultGroup = searchParams.get("group") || "";
  const [groups, setGroups] = useState([]);
  const [allUsers, setAllUsers] = useState([]);
  const [selectedGroup, setSelectedGroup] = useState(defaultGroup);
  const [settlements, setSettlements] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    payer_id: "", payee_id: "", amount: "", currency: "INR", notes: "",
  });

  useEffect(() => {
    Promise.all([listGroups(), listUsers()]).then(([g, u]) => {
      setGroups(g.data);
      setAllUsers(u.data);
    });
  }, []);

  useEffect(() => {
    if (selectedGroup) {
      listGroupSettlements(selectedGroup).then((r) => setSettlements(r.data));
    }
  }, [selectedGroup]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      await recordSettlement({
        group_id: parseInt(selectedGroup),
        payer_id: parseInt(form.payer_id),
        payee_id: parseInt(form.payee_id),
        amount: parseFloat(form.amount),
        currency: form.currency,
        notes: form.notes,
      });
      setShowForm(false);
      setForm({ payer_id: "", payee_id: "", amount: "", currency: "INR", notes: "" });
      listGroupSettlements(selectedGroup).then((r) => setSettlements(r.data));
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to record settlement");
    }
  };

  const groupMembers = selectedGroup
    ? (groups.find((g) => g.id === parseInt(selectedGroup))?.members || []).filter((m) => !m.left_at)
    : [];

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Settlements</h1>
        {selectedGroup && (
          <button onClick={() => setShowForm(!showForm)} className="bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-green-700">
            + Record Payment
          </button>
        )}
      </div>

      <select
        value={selectedGroup}
        onChange={(e) => { setSelectedGroup(e.target.value); setSettlements([]); }}
        className="border border-gray-300 rounded-lg px-3 py-2 text-sm mb-6 focus:outline-none focus:ring-2 focus:ring-indigo-400"
      >
        <option value="">Select a group…</option>
        {groups.map((g) => <option key={g.id} value={g.id}>{g.name}</option>)}
      </select>

      {showForm && (
        <form onSubmit={handleSubmit} className="bg-white border border-gray-200 rounded-xl p-5 mb-6 space-y-4">
          <h2 className="font-semibold text-gray-700">Record a Payment</h2>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-medium text-gray-600">Who paid</label>
              <select value={form.payer_id} onChange={(e) => setForm((p) => ({ ...p, payer_id: e.target.value }))}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mt-1 focus:outline-none focus:ring-2 focus:ring-indigo-400" required>
                <option value="">Select…</option>
                {groupMembers.map((m) => <option key={m.user.id} value={m.user.id}>{m.user.name}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs font-medium text-gray-600">Paid to</label>
              <select value={form.payee_id} onChange={(e) => setForm((p) => ({ ...p, payee_id: e.target.value }))}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mt-1 focus:outline-none focus:ring-2 focus:ring-indigo-400" required>
                <option value="">Select…</option>
                {groupMembers.map((m) => <option key={m.user.id} value={m.user.id}>{m.user.name}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs font-medium text-gray-600">Amount</label>
              <input type="number" step="0.01" min="0.01" value={form.amount}
                onChange={(e) => setForm((p) => ({ ...p, amount: e.target.value }))}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mt-1 focus:outline-none focus:ring-2 focus:ring-indigo-400" required />
            </div>
            <div>
              <label className="text-xs font-medium text-gray-600">Currency</label>
              <select value={form.currency} onChange={(e) => setForm((p) => ({ ...p, currency: e.target.value }))}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mt-1 focus:outline-none focus:ring-2 focus:ring-indigo-400">
                <option value="INR">INR</option>
                <option value="USD">USD</option>
              </select>
            </div>
            <div className="col-span-2">
              <label className="text-xs font-medium text-gray-600">Notes (optional)</label>
              <input value={form.notes} onChange={(e) => setForm((p) => ({ ...p, notes: e.target.value }))}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mt-1 focus:outline-none focus:ring-2 focus:ring-indigo-400"
                placeholder="UPI transfer, cash, etc." />
            </div>
          </div>
          {error && <p className="text-red-500 text-sm">{error}</p>}
          <div className="flex gap-2">
            <button type="submit" className="bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-green-700">Save</button>
            <button type="button" onClick={() => setShowForm(false)} className="text-gray-500 text-sm px-4 py-2">Cancel</button>
          </div>
        </form>
      )}

      {settlements.length === 0 && selectedGroup && (
        <p className="text-gray-400 text-sm">No settlements recorded yet.</p>
      )}

      <div className="space-y-3">
        {settlements.map((s) => (
          <div key={s.id} className="bg-white border border-gray-200 rounded-xl px-5 py-4 flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-800">
                <span className="text-indigo-600">{s.payer_name}</span>
                <span className="text-gray-400 mx-2">→</span>
                <span className="text-green-700">{s.payee_name}</span>
              </p>
              <p className="text-xs text-gray-400 mt-0.5">
                {new Date(s.settled_at).toLocaleDateString()}{s.notes ? ` · ${s.notes}` : ""}
              </p>
            </div>
            <p className="font-bold text-gray-800">
              {s.currency === "USD" ? `$${s.amount}` : `₹${s.amount}`}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
