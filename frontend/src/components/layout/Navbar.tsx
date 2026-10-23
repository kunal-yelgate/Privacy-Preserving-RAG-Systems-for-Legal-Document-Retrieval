"use client";

import React from "react";
import { ShieldCheck, Lock, User as UserIcon, LogOut, Cpu } from "lucide-react";
import { api } from "@/lib/api/client";
import { useAuth } from "@/contexts/AuthContext";

export default function Navbar() {
  const { user, backendOnline, retryAuth } = useAuth();

  const handleLogout = () => {
    api.logout();
    window.location.reload();
  };

  return (
    <header className="h-16 border-b border-slate-200 bg-white sticky top-0 z-30 px-6 flex items-center justify-between shadow-sm">
      <div className="flex items-center gap-3">
        <div className="bg-slate-900 text-white p-2 rounded-lg flex items-center justify-center font-bold text-lg shadow-sm">
          ⚖️
        </div>
        <div>
          <h1 className="font-bold text-slate-900 tracking-tight text-base leading-none">
            VERITAS LEGAL RAG
          </h1>
          <p className="text-xs text-slate-500 font-medium">Privacy-Preserving Offline Intelligence</p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {/* Offline Security / Backend Status Pill */}
        {backendOnline === false ? (
          <button
            onClick={retryAuth}
            title="Click to reconnect"
            className="flex items-center gap-2 bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-200 px-3 py-1 rounded-full text-xs font-semibold transition-colors"
          >
            <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse"></span>
            <span>Backend Offline (Click to Retry)</span>
          </button>
        ) : (
          <div className="flex items-center gap-2 bg-emerald-50 text-emerald-800 border border-emerald-200 px-3 py-1 rounded-full text-xs font-semibold">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
            <span>Strict Offline Mode Active</span>
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
          </div>
        )}

        {/* Local Model Endpoint */}
        <div className="hidden md:flex items-center gap-1.5 bg-slate-100 text-slate-700 px-2.5 py-1 rounded-md text-xs font-mono border border-slate-200">
          <Cpu className="w-3.5 h-3.5 text-slate-500" />
          <span>127.0.0.1:11434 (Ollama)</span>
        </div>

        {/* User Badge */}
        {user ? (
          <div className="flex items-center gap-3 pl-2 border-l border-slate-200">
            <div className="flex items-center gap-2 text-xs">
              <div className="w-7 h-7 rounded-full bg-slate-200 flex items-center justify-center text-slate-700 font-bold uppercase">
                {user.username[0]}
              </div>
              <div className="hidden sm:block text-left">
                <p className="font-semibold text-slate-800 leading-tight">{user.username}</p>
                <p className="text-[10px] text-slate-500 uppercase">{user.role}</p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              title="Logout"
              className="text-slate-400 hover:text-rose-600 p-1.5 rounded-md hover:bg-slate-100 transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <div className="text-xs text-slate-500 flex items-center gap-1">
            <Lock className="w-3.5 h-3.5 text-slate-400" />
            <span>Local Session</span>
          </div>
        )}
      </div>
    </header>
  );
}

