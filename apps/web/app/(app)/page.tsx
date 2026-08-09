import { Suspense } from "react";
import { ChatView } from "@/components/chat/ChatView";

// Chat is the front door: a visitor lands in the working tool rather than on a
// page describing it.
export default function HomePage() {
  return (
    <Suspense fallback={null}>
      <ChatView />
    </Suspense>
  );
}
