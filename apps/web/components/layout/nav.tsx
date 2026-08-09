import {
  Columns3,
  Database,
  LayoutGrid,
  MessageSquare,
  Search,
  type LucideIcon,
} from "lucide-react";

export interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
}

export const NAV: NavItem[] = [
  { href: "/", label: "Chat", icon: MessageSquare },
  { href: "/lab", label: "Retrieval Lab", icon: Columns3 },
  { href: "/search", label: "Search", icon: Search },
  { href: "/startups", label: "Startups", icon: LayoutGrid },
  { href: "/ingest", label: "Data", icon: Database },
];

export function activeNav(pathname: string): NavItem | undefined {
  const exact = NAV.find((n) => pathname === n.href);
  if (exact) return exact;
  // "/" is a prefix of every path, so the prefix match must skip it or Chat
  // would light up on every route.
  return NAV.find((n) => n.href !== "/" && pathname.startsWith(n.href));
}
