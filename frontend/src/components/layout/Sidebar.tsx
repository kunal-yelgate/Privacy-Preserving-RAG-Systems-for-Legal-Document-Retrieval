"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Search,
  FileText,
  Briefcase,
  ShieldAlert,
  Settings,
  HardDrive,
} from "lucide-react";

const NAV_ITEMS = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Research Workspace", href: "/research", icon: Search },
  { name: "Documents", href: "/documents", icon: FileText },
  { name: "Matters", href: "/matters", icon: Briefcase },
  { name: "Security Center", href: "/security", icon: ShieldAlert },
  { name: "Settings", href: "/settings", icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 border-r border-slate-200 bg-white flex flex-col justify-between p-4 min-h-[calc(100vh-4rem)]">
      <div className="space-y-6">
        <div className="space-y-1">
          <p className="px-3 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            Workspace
          </p>
          <nav className="space-y-0.5">
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-slate-900 text-white shadow-sm"
                      : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? "text-white" : "text-slate-500"}`} />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Local Persistence Pill */}
      <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-1.5">
        <div className="flex items-center gap-2 text-slate-700 font-semibold">
          <HardDrive className="w-3.5 h-3.5 text-slate-500" />
          <span>Local Storage</span>
        </div>
        <p className="text-[11px] text-slate-500 leading-snug">
          Vectors: ChromaDB
          <br />
          Metadata: SQLite (WAL)
          <br />
          Files: data/originals/
        </p>
      </div>
    </aside>
  );
}
