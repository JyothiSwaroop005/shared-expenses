import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listGroups, createGroup } from "../api/client";

export default function Groups() {
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: "", description: "" });
  const [error, setError] = useState("");

  const fetchGroups = () =>
    listGroups()
      .then((res) => setGroups(res.data))
      .catch(() => setError("Could not load groups"))
      .finally(() => setLoading(false));

  useEffect(() => { fetchGroups(); }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      await createGroup(form);
      setForm({ name: "", description: "" });
      setShowForm(false);
      fetchGroups();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to create group");
    }
  };

  if (loading) return <p className="text-gray-500 text-sm">Loading…</p>;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-800">Groups</h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700"
        >
          + New Group
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="bg-white border border-gray-200 rounded-xl p-4 mb-6 space-y-3">
          <h2 className="text-sm font-semibold text-gray-700">Create New Group</h2>
          <input
            value={form.name}
            onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))}
            placeholder="Group name (e.g. Goa Trip)"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
            required
          />
          <input
            value={form.description}
            onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))}
            placeholder="Description (optional)"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
          />
          {error && <p className="text-red-500 text-sm">{error}</p>}
          <div className="flex gap-2">
            <button type="submit" className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700">
              Create
            </button>
            <button type="button" onClick={() => setShowForm(false)} className="text-gray-500 text-sm px-4 py-2">
              Cancel
            </button>
          </div>
        </form>
      )}

      {groups.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-8 text-center text-gray-500">
          No groups yet. Create one to get started.
        </div>
      ) : (
        <div className="space-y-3">
          {groups.map((g) => (
            <Link
              key={g.id}
              to={`/groups/${g.id}`}
              className="block bg-white border border-gray-200 rounded-xl px-5 py-4 hover:border-indigo-300 transition-colors"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-semibold text-gray-800">{g.name}</p>
                  {g.description && <p className="text-sm text-gray-500 mt-0.5">{g.description}</p>}
                </div>
                <span className="text-xs bg-gray-100 text-gray-500 px-2 py-1 rounded-full">
                  {g.members.filter((m) => !m.left_at).length} members
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
