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
  { href: "/chat", label: "Chat", icon: MessageSquare },
  { href: "/lab", label: "Retrieval Lab", icon: Columns3 },
  { href: "/search", label: "Search", icon: Search },
  { href: "/startups", label: "Startups", icon: LayoutGrid },
  { href: "/ingest", label: "Data", icon: Database },
];

export function activeNav(pathname: string): NavItem | undefined {
  return (
    NAV.find((n) => pathname === n.href) ??
    NAV.find((n) => pathname.startsWith(n.href))
  );
}
