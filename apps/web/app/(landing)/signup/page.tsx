import { SignupForm } from "@/components/login/SignupForm";

export default async function SignupPage({
  searchParams,
}: {
  searchParams: Promise<{ redirect?: string }>;
}) {
  const { redirect } = await searchParams;
  return (
    <section className="flex min-h-screen items-center justify-center px-4 py-12">
      <SignupForm redirect={redirect ?? "/chat"} />
    </section>
  );
}
