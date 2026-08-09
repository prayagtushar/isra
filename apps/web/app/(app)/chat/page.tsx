import { redirect } from "next/navigation";

// Chat moved to "/". Kept so links already in the wild — the README, the
// deployed demo link — keep working.
export default function ChatPage() {
  redirect("/");
}
