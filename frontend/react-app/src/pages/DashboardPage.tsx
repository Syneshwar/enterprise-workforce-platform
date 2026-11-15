
import { useState } from "react";
import {
  LogOut,
  Users,
  BriefcaseBusiness,
  ClipboardList,
  ShieldCheck,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { authService } from "../services/authService";

export default function DashboardPage() {
  const { user, logout } = useAuth();

  const [isVerifying, setIsVerifying] = useState(false);
  const [verificationMessage, setVerificationMessage] = useState("");
  const [verificationError, setVerificationError] = useState("");

  const handleLogout = () => {
    logout();
  };

  const handleVerifyAuthentication = async () => {
    setIsVerifying(true);
    setVerificationMessage("");
    setVerificationError("");

    try {
      const currentUser = await authService.getCurrentUser();

      setVerificationMessage(
        `Authentication successful. Verified user: ${currentUser.email}`
      );
    } catch (error) {
      setVerificationError(
        "Authentication verification failed. Please check the backend."
      );
    } finally {
      setIsVerifying(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-100">
      <header className="flex items-center justify-between border-b bg-white px-8 py-5">
        <div>
          <h1 className="text-xl font-bold text-slate-900">WorkforceHub</h1>
          <p className="text-sm text-slate-500">
            Enterprise Workforce Platform
          </p>
        </div>

        <button
          onClick={handleLogout}
          className="flex items-center gap-2 rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-100"
        >
          <LogOut size={17} />
          Logout
        </button>
      </header>

      <section className="p-8">
        <div className="mb-8">
          <p className="text-sm font-medium text-blue-600">
            AUTHENTICATED DASHBOARD
          </p>

          <h2 className="mt-2 text-3xl font-bold text-slate-900">
            Welcome, {user?.full_name}!
          </h2>

          <p className="mt-2 text-slate-500">
            You have successfully authenticated with the WorkforceHub platform.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          <div className="rounded-xl border bg-white p-6 shadow-sm">
            <Users className="mb-4 text-blue-600" size={28} />
            <h3 className="font-semibold text-slate-900">Employees</h3>
            <p className="mt-2 text-sm text-slate-500">
              Employee management workspace
            </p>
          </div>

          <div className="rounded-xl border bg-white p-6 shadow-sm">
            <BriefcaseBusiness className="mb-4 text-blue-600" size={28} />
            <h3 className="font-semibold text-slate-900">Projects</h3>
            <p className="mt-2 text-sm text-slate-500">
              Project planning and tracking
            </p>
          </div>

          <div className="rounded-xl border bg-white p-6 shadow-sm">
            <ClipboardList className="mb-4 text-blue-600" size={28} />
            <h3 className="font-semibold text-slate-900">Tasks</h3>
            <p className="mt-2 text-sm text-slate-500">
              Task assignment and progress
            </p>
          </div>
        </div>

        <div className="mt-8 rounded-xl border bg-white p-6 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h3 className="font-semibold text-slate-900">
                Authentication verification
              </h3>
              <p className="mt-1 text-sm text-slate-500">
                Test the protected API and automatic access-token renewal.
              </p>
            </div>

            <button
              onClick={handleVerifyAuthentication}
              disabled={isVerifying}
              className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              <ShieldCheck size={17} />
              {isVerifying ? "Verifying..." : "Verify Authentication"}
            </button>
          </div>

          {verificationMessage && (
            <p className="mt-4 text-sm font-medium text-green-600">
              {verificationMessage}
            </p>
          )}

          {verificationError && (
            <p className="mt-4 text-sm font-medium text-red-600">
              {verificationError}
            </p>
          )}
        </div>

        <div className="mt-8 rounded-xl border bg-white p-6 shadow-sm">
          <h3 className="font-semibold text-slate-900">
            Account information
          </h3>

          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <div>
              <p className="text-sm text-slate-500">Full name</p>
              <p className="mt-1 font-medium text-slate-900">
                {user?.full_name}
              </p>
            </div>

            <div>
              <p className="text-sm text-slate-500">Email</p>
              <p className="mt-1 font-medium text-slate-900">
                {user?.email}
              </p>
            </div>

            <div>
              <p className="text-sm text-slate-500">Role</p>
              <p className="mt-1 font-medium capitalize text-slate-900">
                {user?.role}
              </p>
            </div>

            <div>
              <p className="text-sm text-slate-500">Account status</p>
              <p className="mt-1 font-medium text-green-600">
                {user?.is_active ? "Active" : "Inactive"}
              </p>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
