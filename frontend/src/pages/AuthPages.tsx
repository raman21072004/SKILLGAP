import { zodResolver } from "@hookform/resolvers/zod";
import { useState, type ReactNode } from "react";
import { useForm } from "react-hook-form";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import type { z } from "zod";
import { Logo } from "@/components/layout/Logo";
import { Button } from "@/components/ui/button";
import { FieldError, Input, Label } from "@/components/ui/form";
import { loginSchema, registerSchema } from "@/features/analysis/schema";
import { errorMessage } from "@/services/api";
import { useAuth } from "@/store/auth";

function Shell({ title, subtitle, children, footer }: { title: string; subtitle: string; children: ReactNode; footer: ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-4 py-10">
      <div className="mb-8"><Logo /></div>
      <div className="w-full max-w-sm rounded-2xl border border-line bg-surface p-7">
        <h1 className="text-2xl font-bold">{title}</h1>
        <p className="mt-1 text-sm text-muted">{subtitle}</p>
        <div className="mt-6">{children}</div>
      </div>
      <p className="mt-6 text-sm text-muted">{footer}</p>
    </div>
  );
}

export function LoginPage() {
  const { login, status } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [serverError, setServerError] = useState<string | null>(null);
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<z.infer<typeof loginSchema>>({ resolver: zodResolver(loginSchema) });
  const from = (location.state as { from?: string } | null)?.from ?? "/dashboard";
  if (status === "authenticated") return <Navigate to={from} replace />;

  const onSubmit = handleSubmit(async (v) => {
    setServerError(null);
    try {
      await login(v.email, v.password);
      toast.success("Signed in");
      navigate(from, { replace: true });
    } catch (e) {
      setServerError(errorMessage(e));
    }
  });

  return (
    <Shell title="Sign in" subtitle="Continue to your analyses and roadmap." footer={<>New here? <Link to="/register" className="font-semibold text-pine hover:underline">Create an account</Link></>}>
      <form onSubmit={onSubmit} noValidate className="space-y-4">
        <div>
          <Label htmlFor="email">Email</Label>
          <Input id="email" type="email" autoComplete="email" aria-invalid={!!errors.email} {...register("email")} />
          <FieldError message={errors.email?.message} />
        </div>
        <div>
          <Label htmlFor="password">Password</Label>
          <Input id="password" type="password" autoComplete="current-password" aria-invalid={!!errors.password} {...register("password")} />
          <FieldError message={errors.password?.message} />
        </div>
        {serverError && <p role="alert" className="rounded-lg bg-missing-soft px-3 py-2 text-sm text-missing">{serverError}</p>}
        <Button type="submit" className="w-full" loading={isSubmitting}>Sign in</Button>
      </form>
    </Shell>
  );
}

export function RegisterPage() {
  const { register: signUp, status } = useAuth();
  const navigate = useNavigate();
  const [serverError, setServerError] = useState<string | null>(null);
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<z.infer<typeof registerSchema>>({ resolver: zodResolver(registerSchema) });
  if (status === "authenticated") return <Navigate to="/dashboard" replace />;

  const onSubmit = handleSubmit(async (v) => {
    setServerError(null);
    try {
      await signUp(v.full_name, v.email, v.password);
      toast.success("Account created");
      navigate("/analyses/new");
    } catch (e) {
      setServerError(errorMessage(e));
    }
  });

  return (
    <Shell title="Create your account" subtitle="Your analyses are private to you and can be deleted at any time."
      footer={<>Already have an account? <Link to="/login" className="font-semibold text-pine hover:underline">Sign in</Link></>}>
      <form onSubmit={onSubmit} noValidate className="space-y-4">
        <div>
          <Label htmlFor="full_name">Name</Label>
          <Input id="full_name" autoComplete="name" aria-invalid={!!errors.full_name} {...register("full_name")} />
          <FieldError message={errors.full_name?.message} />
        </div>
        <div>
          <Label htmlFor="email">Email</Label>
          <Input id="email" type="email" autoComplete="email" aria-invalid={!!errors.email} {...register("email")} />
          <FieldError message={errors.email?.message} />
        </div>
        <div>
          <Label htmlFor="password">Password</Label>
          <Input id="password" type="password" autoComplete="new-password" aria-invalid={!!errors.password} {...register("password")} />
          <FieldError message={errors.password?.message} />
          {!errors.password && <p className="mt-1 text-xs text-muted">At least 8 characters with a letter and a number.</p>}
        </div>
        {serverError && <p role="alert" className="rounded-lg bg-missing-soft px-3 py-2 text-sm text-missing">{serverError}</p>}
        <Button type="submit" className="w-full" loading={isSubmitting}>Create account</Button>
      </form>
    </Shell>
  );
}
