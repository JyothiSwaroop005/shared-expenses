import React, { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { listGroups, listGroupExpenses, createExpense, listUsers, deleteExpense } from "../api/client";
import { useAuth } from "../context/AuthContext";

const SPLIT_TYPES = ["equal", "percentage", "exact"];

export default function Expenses() {
  const { user } = useAuth();
  const [searchParams] = useSearchParams();
  const defaultGroupId = searchParams.get("group") || "";

  const [groups, setGroups] = useState([]);
  const [allUsers, setAllUsers] = useState([]);
  const [expenses, setExpenses] = useState([]);
  const [selectedGroup, setSelectedGroup] = useState(defaultGroupId);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState("");

  // Form state
  const [form, setForm] = useState({
    description: "",
    amount: "",
    currency: "INR",
    paid_by_id: "",
    split_type: "equal",
    expense_date: new Date().toISOString().slice(0, 16),
    notes: "",
  });
  // participants: [{user_id, value}] - value is % or exact amount; null for equal
  const [participants, setParticipants] = useState([]);

  useEffect(() => {
    Promise.all([listGroups(), listUsers()]).then(([g, u]) => {
      setGroups(g.data);
      setAllUsers(u.data);
    });
  }, []);

  useEffect(() => {
    if (selectedGroup) {
      listGroupExpenses(selectedGroup).then((res) => setExpenses(res.data));
    }
  }, [selectedGroup]);

  const handleParticipantToggle = (userId) => {
    setParticipants((prev) =>
      prev.find((p) => p.user_id === userId)
        ? prev.filter((p) => p.user_id !== userId)
        : [...prev, { user_id: userId, value: "" }]
    );
  };

  const handleParticipantValue = (userId, value) => {
    setParticipants((prev) =>
      prev.map((p) => (p.user_id === userId ? { ...p, value } : p))
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      const payload = {
        group_id: parseInt(selectedGroup),
        paid_by_id: parseInt(form.paid_by_id),
        description: form.description,
        amount: parseFloat(form.amount),
        currency: form.currency,
        split_type: form.split_type,
        expense_date: new Date(form.expense_date).toISOString(),
        notes: form.notes,
        participants: participants.map((p) => ({
          user_id: p.user_id,
          value: p.value ? parseFloat(p.value) : null,
        })),
      };
      await createExpense(payload);
      setShowForm(false);
      setForm({ description: "", amount: "", currency: "INR", paid_by_id: "", split_type: "equal", expense_date: new Date().toISOString().slice(0, 16), notes: "" });
      setParticipants([]);
      listGroupExpenses(selectedGroup).then((res) => setExpenses(res.data));
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to create expense");
    }
  };

  const handleDelete = async (expenseId) => {
    if (!window.confirm("Delete this expense?")) return;
    try {
      await deleteExpense(expenseId);
      setExpenses((prev) => prev.filter((e) => e.id !== expenseId));
    } catch (err) {
      setError(err.response?.data?.detail || "Cannot delete expense");
    }
  };

  const groupMembers = selectedGroup
    ? (groups.find((g) => g.id === parseInt(selectedGroup))?.members || [])
        .filter((m) => !m.left_at)
    : [];

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Expenses</h1>
        {selectedGroup && (
          <button
            onClick={() => setShowForm(!showForm)}
            className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700"
          >
            + Add Expense
          </button>
        )}
      </div>

      {/* Group selector */}
      <div className="mb-4">
        <select
          value={selectedGroup}
          onChange={(e) => { setSelectedGroup(e.target.value); setExpenses([]); }}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
        >
          <option value="">Select a group…</option>
          {groups.map((g) => (
            <option key={g.id} value={g.id}>{g.name}</option>
          ))}
        </select>
      </div>

      {/* Create Expense Form */}
      {showForm && (
        <form onSubmit={handleSubmit} className="bg-white border border-gray-200 rounded-xl p-5 mb-6 space-y-4">
          <h2 className="font-semibold text-gray-700">New Expense</h2>

          <div className="grid grid-cols-2 gap-3">
            <div className="col-span-2">
              <label className="text-xs font-medium text-gray-600">Description</label>
              <input
                value={form.description}
                onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mt-1 focus:outline-none focus:ring-2 focus:ring-indigo-400"
                placeholder="Dinner at restaurant"
                required
              />
            </div>

            <div>
              <label className="text-xs font-medium text-gray-600">Amount</label>
              <input
                type="number"
                step="0.01"
                min="0.01"
                value={form.amount}
                onChange={(e) => setForm((p) => ({ ...p, amount: e.target.value }))}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mt-1 focus:outline-none focus:ring-2 focus:ring-indigo-400"
                required
              />
            </div>

            <div>
              <label className="text-xs font-medium text-gray-600">Currency</label>
              <select
                value={form.currency}
                onChange={(e) => setForm((p) => ({ ...p, currency: e.target.value }))}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mt-1 focus:outline-none focus:ring-2 focus:ring-indigo-400"
              >
                <option value="INR">INR (₹)</option>
                <option value="USD">USD ($)</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-medium text-gray-600">Paid by</label>
              <select
                value={form.paid_by_id}
                onChange={(e) => setForm((p) => ({ ...p, paid_by_id: e.target.value }))}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mt-1 focus:outline-none focus:ring-2 focus:ring-indigo-400"
                required
              >
                <option value="">Select payer…</option>
                {groupMembers.map((m) => (
                  <option key={m.user.id} value={m.user.id}>{m.user.name}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-xs font-medium text-gray-600">Split type</label>
              <select
                value={form.split_type}
                onChange={(e) => { setForm((p) => ({ ...p, split_type: e.target.value })); setParticipants([]); }}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mt-1 focus:outline-none focus:ring-2 focus:ring-indigo-400"
              >
                {SPLIT_TYPES.map((t) => (
                  <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
                ))}
              </select>
            </div>

            <div className="col-span-2">
              <label className="text-xs font-medium text-gray-600">Date</label>
              <input
                type="datetime-local"
                value={form.expense_date}
                onChange={(e) => setForm((p) => ({ ...p, expense_date: e.target.value }))}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mt-1 focus:outline-none focus:ring-2 focus:ring-indigo-400"
                required
              />
            </div>
          </div>

          {/* Participants */}
          <div>
            <label className="text-xs font-medium text-gray-600 block mb-2">
              Participants{" "}
              {form.split_type === "percentage" && "(enter % for each)"}
              {form.split_type === "exact" && "(enter exact amount for each)"}
            </label>
            <div className="space-y-2">
              {groupMembers.map((m) => {
                const isSelected = participants.find((p) => p.user_id === m.user.id);
                return (
                  <div key={m.user.id} className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={!!isSelected}
                      onChange={() => handleParticipantToggle(m.user.id)}
                      className="rounded"
                    />
                    <span className="text-sm text-gray-700 w-24">{m.user.name}</span>
                    {isSelected && form.split_type !== "equal" && (
                      <input
                        type="number"
                        step="0.01"
                        placeholder={form.split_type === "percentage" ? "%" : "₹"}
                        value={isSelected.value}
                        onChange={(e) => handleParticipantValue(m.user.id, e.target.value)}
                        className="border border-gray-300 rounded px-2 py-1 text-sm w-24 focus:outline-none focus:ring-2 focus:ring-indigo-400"
                      />
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {error && <p className="text-red-500 text-sm">{error}</p>}
          <div className="flex gap-2">
            <button type="submit" className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700">
              Save Expense
            </button>
            <button type="button" onClick={() => setShowForm(false)} className="text-gray-500 text-sm px-4 py-2">
              Cancel
            </button>
          </div>
        </form>
      )}

      {/* Expense list */}
      {!selectedGroup && (
        <p className="text-gray-400 text-sm">Select a group to see expenses.</p>
      )}
      {selectedGroup && expenses.length === 0 && (
        <p className="text-gray-400 text-sm">No expenses in this group yet.</p>
      )}
      <div className="space-y-3">
        {expenses.map((e) => (
          <div key={e.id} className="bg-white border border-gray-200 rounded-xl px-5 py-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="font-medium text-gray-800">{e.description}</p>
                <p className="text-xs text-gray-400 mt-0.5">
                  Paid by <span className="text-gray-600 font-medium">{e.paid_by_name}</span> ·{" "}
                  {new Date(e.expense_date).toLocaleDateString()} ·{" "}
                  <span className="capitalize bg-gray-100 px-1.5 py-0.5 rounded text-gray-600">{e.split_type}</span>
                </p>
              </div>
              <div className="text-right">
                <p className="font-bold text-gray-800">
                  {e.currency === "USD" ? `$${e.amount}` : `₹${e.amount}`}
                </p>
                {e.currency === "USD" && (
                  <p className="text-xs text-gray-400">≈ ₹{parseFloat(e.amount_inr).toFixed(2)}</p>
                )}
              </div>
            </div>
            {/* Splits */}
            <div className="mt-2 flex flex-wrap gap-2">
              {e.splits.map((s) => (
                <span key={s.id} className="text-xs bg-indigo-50 text-indigo-600 px-2 py-0.5 rounded-full">
                  {s.user_name}: ₹{parseFloat(s.owed_amount).toFixed(2)}
                </span>
              ))}
            </div>
            {e.paid_by_id === user?.id && (
              <button
                onClick={() => handleDelete(e.id)}
                className="mt-2 text-xs text-red-400 hover:text-red-600"
              >
                Delete
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
