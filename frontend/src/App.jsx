import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Navbar from "./components/Navbar";

import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Groups from "./pages/Groups";
import GroupDetail from "./pages/GroupDetail";
import Expenses from "./pages/Expenses";
import Balances from "./pages/Balances";
import ImportCSV from "./pages/ImportCSV";
import AnomalyReview from "./pages/AnomalyReview";
import Settlements from "./pages/Settlements";

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public route - no auth needed */}
          <Route path="/login" element={<Login />} />

          {/* All other routes require login */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <div className="min-h-screen bg-gray-50">
                  <Navbar />
                  <main className="max-w-5xl mx-auto px-4 py-6">
                    <Navigate to="/dashboard" replace />
                  </main>
                </div>
              </ProtectedRoute>
            }
          />

          {/* Wrap all protected pages with Navbar */}
          {[
            { path: "/dashboard", element: <Dashboard /> },
            { path: "/groups", element: <Groups /> },
            { path: "/groups/:id", element: <GroupDetail /> },
            { path: "/expenses", element: <Expenses /> },
            { path: "/balances", element: <Balances /> },
            { path: "/import", element: <ImportCSV /> },
            { path: "/anomalies", element: <AnomalyReview /> },
            { path: "/settlements", element: <Settlements /> },
          ].map(({ path, element }) => (
            <Route
              key={path}
              path={path}
              element={
                <ProtectedRoute>
                  <div className="min-h-screen bg-gray-50">
                    <Navbar />
                    <main className="max-w-5xl mx-auto px-4 py-6">{element}</main>
                  </div>
                </ProtectedRoute>
              }
            />
          ))}

          {/* Catch-all redirect */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
