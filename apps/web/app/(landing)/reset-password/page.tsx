import { Suspense } from "react";
import { ResetPasswordForm } from "@/components/login/ResetPasswordForm";

export default function ResetPasswordPage() {
  return (
    <section className="flex min-h-screen items-center justify-center px-4 py-12">
      <Suspense fallback={null}>
        <ResetPasswordForm />
      </Suspense>
    </section>
  );
}
