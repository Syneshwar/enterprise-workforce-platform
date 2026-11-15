
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import axios from "axios";

import {
  Eye,
  EyeOff,
  LockKeyhole,
  Mail,
  Users,
} from "lucide-react";

import { useAuth } from "../context/AuthContext";

const loginSchema = z.object({
  email: z.string().trim().email("Enter a valid email address"),
  password: z.string().min(1, "Password is required"),
});

type LoginFormData = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const navigate = useNavigate();
  const { login, isLoading } = useAuth();

  const [showPassword, setShowPassword] = useState(false);
  const [apiError, setApiError] = useState("");

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginFormData) => {
    setApiError("");

    try {
      await login({
        email: data.email,
        password: data.password,
      });

      navigate("/dashboard", { replace: true });
    } catch (error: unknown) {
      if (axios.isAxiosError(error)) {
        const detail = error.response?.data?.detail;

        setApiError(
          typeof detail === "string"
            ? detail
            : "Login failed. Please check your credentials."
        );
      } else {
        setApiError("An unexpected error occurred. Please try again.");
      }
    }
  };

  return (
    <main className="grid min-h-screen bg-white lg:grid-cols-2">

      {/* Branding section */}
      <section className="hidden flex-col justify-between bg-slate-950 p-12 text-white lg:flex">

        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-blue-600 p-3">
            <Users size={25} />
          </div>

          <span className="text-xl font-bold tracking-wide">
            Workforce<span className="text-blue-400">Hub</span>
          </span>
        </div>

        <div className="max-w-lg">
          <p className="mb-4 text-sm font-semibold uppercase tracking-[0.2em] text-blue-400">
            Enterprise Workforce Platform
          </p>

          <h1 className="text-5xl font-bold leading-tight">
            Manage people.
            <br />
            Deliver projects.
            <br />
            <span className="text-blue-400">Achieve more.</span>
          </h1>

          <p className="mt-6 text-lg leading-8 text-slate-300">
            A unified workspace to manage employees, projects,
            tasks, collaboration and organizational performance.
          </p>
        </div>

        <p className="text-sm text-slate-400">
          © 2026 WorkforceHub. All rights reserved.
        </p>
      </section>

      {/* Login form */}
      <section className="flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-md">

          <div className="mb-10 lg:hidden">
            <div className="flex items-center gap-3 text-slate-900">
              <div className="rounded-xl bg-blue-600 p-3 text-white">
                <Users size={24} />
              </div>

              <span className="text-xl font-bold">
                Workforce<span className="text-blue-600">Hub</span>
              </span>
            </div>
          </div>

          <div className="mb-8">
            <h2 className="text-3xl font-bold tracking-tight text-slate-900">
              Welcome back
            </h2>

            <p className="mt-2 text-slate-500">
              Sign in to access your workforce dashboard.
            </p>
          </div>

          <form
            onSubmit={handleSubmit(onSubmit)}
            className="space-y-6"
            noValidate
          >

            {/* Email */}
            <div>
              <label
                htmlFor="email"
                className="mb-2 block text-sm font-semibold text-slate-700"
              >
                Email address
              </label>

              <div className="relative">
                <Mail
                  size={19}
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
                />

                <input
                  id="email"
                  type="email"
                  autoComplete="email"
                  placeholder="you@company.com"
                  {...register("email")}
                  className="w-full rounded-lg border border-slate-300 py-3 pl-11 pr-4 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                />
              </div>

              {errors.email && (
                <p className="mt-1 text-sm text-red-600">
                  {errors.email.message}
                </p>
              )}
            </div>

            {/* Password */}
            <div>
              <label
                htmlFor="password"
                className="mb-2 block text-sm font-semibold text-slate-700"
              >
                Password
              </label>

              <div className="relative">
                <LockKeyhole
                  size={19}
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
                />

                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  placeholder="Enter your password"
                  {...register("password")}
                  className="w-full rounded-lg border border-slate-300 py-3 pl-11 pr-12 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                />

                <button
                  type="button"
                  onClick={() => setShowPassword((value) => !value)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-700"
                >
                  {showPassword ? (
                    <EyeOff size={19} />
                  ) : (
                    <Eye size={19} />
                  )}
                </button>
              </div>

              {errors.password && (
                <p className="mt-1 text-sm text-red-600">
                  {errors.password.message}
                </p>
              )}
            </div>

            {/* Backend error */}
            {apiError && (
              <div
                role="alert"
                className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700"
              >
                {apiError}
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full rounded-lg bg-blue-600 px-4 py-3 font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isLoading ? "Signing in..." : "Sign in"}
            </button>
          </form>

          <p className="mt-8 text-center text-sm text-slate-500">
            Don't have an account?{" "}
            <Link
              to="/register"
              className="font-semibold text-blue-600 hover:text-blue-700"
            >
              Create an account
            </Link>
          </p>

        </div>
      </section>
    </main>
  );
}
