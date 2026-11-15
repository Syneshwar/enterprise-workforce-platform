
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
  User,
  Users,
} from "lucide-react";

import { authService } from "../services/authService";

// Registration form validation schema
const registerSchema = z
  .object({
    full_name: z
      .string()
      .trim()
      .min(2, "Enter your full name")
      .max(150, "Full name cannot exceed 150 characters"),

    email: z
      .string()
      .trim()
      .email("Enter a valid work email address"),

    password: z
      .string()
      .min(8, "Password must contain at least 8 characters")
      .max(72, "Password cannot exceed 72 characters"),

    confirm_password: z
      .string()
      .min(1, "Please confirm your password"),
  })
  .refine((data) => data.password === data.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"],
  });

type RegisterFormData = z.infer<typeof registerSchema>;

export default function RegisterPage() {
  const navigate = useNavigate();

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const [apiError, setApiError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
  });

  // Register user through FastAPI Auth Service
  const onSubmit = async (data: RegisterFormData) => {
    setApiError("");
    setSuccessMessage("");

    try {
      await authService.register({
        full_name: data.full_name,
        email: data.email,
        password: data.password,
      });

      setSuccessMessage(
        "Account created successfully. Redirecting to login..."
      );

      setTimeout(() => {
        navigate("/login");
      }, 1500);
    } catch (error: unknown) {
      if (axios.isAxiosError(error)) {
        const detail = error.response?.data?.detail;

        setApiError(
          typeof detail === "string"
            ? detail
            : "Registration failed. Please check your details and try again."
        );
      } else {
        setApiError(
          "An unexpected error occurred. Please try again."
        );
      }
    }
  };

  return (
    <main className="grid min-h-screen bg-white lg:grid-cols-2">

      {/* Left branding section */}
      <section className="hidden flex-col justify-between bg-slate-950 p-12 text-white lg:flex">

        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-blue-600 p-3">
            <Users size={25} />
          </div>

          <span className="text-xl font-bold">
            Workforce<span className="text-blue-400">Hub</span>
          </span>
        </div>

        <div className="max-w-lg">
          <p className="mb-4 text-sm font-semibold uppercase tracking-[0.2em] text-blue-400">
            Join your organization
          </p>

          <h1 className="text-5xl font-bold leading-tight">
            One platform.
            <br />
            Better teamwork.
            <br />
            <span className="text-blue-400">
              Greater impact.
            </span>
          </h1>

          <p className="mt-6 text-lg leading-8 text-slate-300">
            Create your account to collaborate with colleagues
            and manage your organization's work in one place.
          </p>
        </div>

        <p className="text-sm text-slate-400">
          © 2026 WorkforceHub. All rights reserved.
        </p>
      </section>

      {/* Registration form section */}
      <section className="flex items-center justify-center px-6 py-12">

        <div className="w-full max-w-md">

          {/* Mobile branding */}
          <div className="mb-8 lg:hidden">
            <div className="flex items-center gap-3 text-slate-900">
              <div className="rounded-xl bg-blue-600 p-3 text-white">
                <Users size={24} />
              </div>

              <span className="text-xl font-bold">
                Workforce<span className="text-blue-600">Hub</span>
              </span>
            </div>
          </div>

          {/* Page heading */}
          <div className="mb-8">
            <h2 className="text-3xl font-bold tracking-tight text-slate-900">
              Create your account
            </h2>

            <p className="mt-2 text-slate-500">
              Enter your details to get started.
            </p>
          </div>

          {/* Registration form */}
          <form
            onSubmit={handleSubmit(onSubmit)}
            className="space-y-5"
            noValidate
          >

            {/* Full name */}
            <div>
              <label
                htmlFor="full_name"
                className="mb-2 block text-sm font-semibold text-slate-700"
              >
                Full name
              </label>

              <div className="relative">
                <User
                  size={19}
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
                />

                <input
                  id="full_name"
                  type="text"
                  autoComplete="name"
                  placeholder="Your full name"
                  {...register("full_name")}
                  className="w-full rounded-lg border border-slate-300 py-3 pl-11 pr-4 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                />
              </div>

              {errors.full_name && (
                <p className="mt-1 text-sm text-red-600">
                  {errors.full_name.message}
                </p>
              )}
            </div>

            {/* Email */}
            <div>
              <label
                htmlFor="email"
                className="mb-2 block text-sm font-semibold text-slate-700"
              >
                Work email
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
                  className="w-full rounded-lg border border-slate-300 py-3 pl-11 pr-4 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
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
                  autoComplete="new-password"
                  placeholder="Create a password"
                  {...register("password")}
                  className="w-full rounded-lg border border-slate-300 py-3 pl-11 pr-12 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                />

                <button
                  type="button"
                  onClick={() =>
                    setShowPassword((value) => !value)
                  }
                  aria-label={
                    showPassword ? "Hide password" : "Show password"
                  }
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

            {/* Confirm password */}
            <div>
              <label
                htmlFor="confirm_password"
                className="mb-2 block text-sm font-semibold text-slate-700"
              >
                Confirm password
              </label>

              <div className="relative">
                <LockKeyhole
                  size={19}
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
                />

                <input
                  id="confirm_password"
                  type={
                    showConfirmPassword ? "text" : "password"
                  }
                  autoComplete="new-password"
                  placeholder="Re-enter your password"
                  {...register("confirm_password")}
                  className="w-full rounded-lg border border-slate-300 py-3 pl-11 pr-12 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                />

                <button
                  type="button"
                  onClick={() =>
                    setShowConfirmPassword((value) => !value)
                  }
                  aria-label={
                    showConfirmPassword
                      ? "Hide password"
                      : "Show password"
                  }
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-700"
                >
                  {showConfirmPassword ? (
                    <EyeOff size={19} />
                  ) : (
                    <Eye size={19} />
                  )}
                </button>
              </div>

              {errors.confirm_password && (
                <p className="mt-1 text-sm text-red-600">
                  {errors.confirm_password.message}
                </p>
              )}
            </div>

            {/* Backend error message */}
            {apiError && (
              <div
                role="alert"
                className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700"
              >
                {apiError}
              </div>
            )}

            {/* Backend success message */}
            {successMessage && (
              <div
                role="status"
                className="rounded-lg border border-green-200 bg-green-50 p-3 text-sm text-green-700"
              >
                {successMessage}
              </div>
            )}

            {/* Submit button */}
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full rounded-lg bg-blue-600 px-4 py-3 font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isSubmitting ? "Creating account..." : "Create account"}
            </button>
          </form>

          {/* Login navigation */}
          <p className="mt-7 text-center text-sm text-slate-500">
            Already have an account?{" "}
            <Link
              to="/login"
              className="font-semibold text-blue-600 hover:text-blue-700"
            >
              Sign in
            </Link>
          </p>

        </div>
      </section>
    </main>
  );
}
