import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getGroup, addMember, removeMember, listGroupExpenses, listUsers } from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function GroupDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const [group, setGroup] = useState(null);
  const [expenses, setExpenses] = useState([]);
  const [allUsers, setAllUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [addUserId, setAddUserId] = useState("");

  const refresh = async () => {
    try {
      const [gRes, eRes, uRes] = await Promise.all([
        getGroup(id),
        listGroupExpenses(id),
        listUsers(),
      ]);
      setGroup(gRes.data);
      setExpenses(eRes.data);
      setAllUsers(uRes.data);
    } catch {
      setError("Could not load group");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { refresh(); }, [id]);

  const handleAddMember = async () => {
    if (!addUserId) return;
    try {
      await addMember(id, { user_id: parseInt(addUserId) });
      setAddUserId("");
      refresh();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to add member");
    }
  };

  const handleRemoveMember = async (userId) => {
    if (!window.confirm("Remove this member?")) return;
    try {
      await removeMember(id, userId);
      refresh();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to remove member");
    }
  };

  if (loading) return <p className="text-gray-500 text-sm">Loading…</p>;
  if (!group) return <p className="text-red-500 text-sm">{error}</p>;

  const activeMembers = group.members.filter((m) => !m.left_at);
  const activeMemberIds = new Set(activeMembers.map((m) => m.user.id));
  const eligibleToAdd = allUsers.filter((u) => !activeMemberIds.has(u.id));

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <Link to="/groups" className="text-indigo-600 text-sm hover:underline">← Groups</Link>
        <h1 className="text-2xl font-bold text-gray-800">{group.name}</h1>
      </div>

      {error && <p className="text-red-500 text-sm mb-4">{error}</p>}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Members panel */}
        <div className="bg-white border border-gray-200 rounded-xl p-4">
          <h2 className="font-semibold text-gray-700 mb-3">Members ({activeMembers.length})</h2>
          <div className="space-y-2 mb-4">
            {activeMembers.map((m) => (
              <div key={m.id} className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-800">{m.user.name}</p>
                  <p className="text-xs text-gray-400">
                    Joined {new Date(m.joined_at).toLocaleDateString()}
                  </p>
                </div>
                {m.user.id !== user?.id && (
                  <button
                    onClick={() => handleRemoveMember(m.user.id)}
                    className="text-xs text-red-400 hover:text-red-600"
                  >
                    Remove
                  </button>
                )}
              </div>
            ))}
          </div>

          {/* Add member */}
          <div className="flex gap-2 mt-2">
            <select
              value={addUserId}
              onChange={(e) => setAddUserId(e.target.value)}
              className="flex-1 border border-gray-300 rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
            >
              <option value="">Add member…</option>
              {eligibleToAdd.map((u) => (
                <option key={u.id} value={u.id}>{u.name}</option>
              ))}
            </select>
            <button
              onClick={handleAddMember}
              disabled={!addUserId}
              className="bg-indigo-600 text-white px-3 py-1.5 rounded-lg text-sm disabled:opacity-40 hover:bg-indigo-700"
            >
              Add
            </button>
          </div>
        </div>

        {/* Quick actions */}
        <div className="bg-white border border-gray-200 rounded-xl p-4 flex flex-col gap-3">
          <h2 className="font-semibold text-gray-700">Quick Actions</h2>
          <Link
            to={`/expenses?group=${id}`}
            className="block bg-indigo-50 text-indigo-700 text-sm font-medium px-3 py-2 rounded-lg hover:bg-indigo-100"
          >
            + Add Expense
          </Link>
          <Link
            to={`/settlements?group=${id}`}
            className="block bg-green-50 text-green-700 text-sm font-medium px-3 py-2 rounded-lg hover:bg-green-100"
          >
            💸 Record Settlement
          </Link>
          <Link
            to={`/balances?group=${id}`}
            className="block bg-gray-50 text-gray-700 text-sm font-medium px-3 py-2 rounded-lg hover:bg-gray-100"
          >
            📊 View Balances
          </Link>
        </div>
      </div>

      {/* Recent expenses */}
      <div className="mt-6">
        <h2 className="font-semibold text-gray-700 mb-3">Recent Expenses</h2>
        {expenses.length === 0 ? (
          <p className="text-gray-400 text-sm">No expenses yet.</p>
        ) : (
          <div className="space-y-2">
            {expenses.slice(0, 10).map((e) => (
              <div key={e.id} className="bg-white border border-gray-200 rounded-xl px-4 py-3 flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-800">{e.description}</p>
                  <p className="text-xs text-gray-400">
                    Paid by {e.paid_by_name} · {new Date(e.expense_date).toLocaleDateString()} ·{" "}
                    <span className="capitalize">{e.split_type}</span> split
                  </p>
                </div>
                <span className="font-semibold text-gray-700">
                  {e.currency !== "INR" ? `$${e.amount}` : `₹${e.amount}`}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
