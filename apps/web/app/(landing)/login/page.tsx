import { LoginForm } from "@/components/login/LoginForm";

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ redirect?: string }>;
}) {
  const { redirect } = await searchParams;
  return (
    <section className="flex min-h-[calc(100vh-3.5rem)] items-center justify-center px-4 py-12">
      <LoginForm redirect={redirect ?? "/chat"} />
    </section>
  );
}
