import { redirect } from "next/navigation";

// Chat moved to "/". Kept so links already in the wild keep working.
export default function ChatPage() {
  redirect("/");
}
