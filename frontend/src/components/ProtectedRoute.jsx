import React from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

// Wraps any route that requires authentication.
// If user is not logged in, redirects to /login.
// While we're checking localStorage (loading=true), show nothing.
export default function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();

  if (loading) return null;
  if (!user) return <Navigate to="/login" replace />;

  return children;
}
