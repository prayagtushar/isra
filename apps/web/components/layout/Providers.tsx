"use client";

import { ThemeProvider } from "@/lib/theme";
import { SettingsProvider } from "@/lib/store/settings";
import { ConversationsProvider } from "@/lib/store/conversations";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider>
      <SettingsProvider>
        <ConversationsProvider>{children}</ConversationsProvider>
      </SettingsProvider>
    </ThemeProvider>
  );
}
