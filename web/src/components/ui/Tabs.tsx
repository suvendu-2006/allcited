"use client";

import React from "react";
import { cn } from "@/lib/utils";

interface TabItem {
  id: string;
  label: string;
  count?: number;
}

interface TabsProps {
  tabs: TabItem[];
  activeTab: string;
  onChange: (id: string) => void;
  className?: string;
}

export function Tabs({ tabs, activeTab, onChange, className }: TabsProps) {
  return (
    <div
      role="tablist"
      className={cn(
        "inline-flex p-1 rounded-interactive bg-bg-sunken border border-border",
        className
      )}
    >
      {tabs.map((tab) => {
        const isActive = activeTab === tab.id;
        return (
          <button
            key={tab.id}
            role="tab"
            aria-selected={isActive}
            type="button"
            onClick={() => onChange(tab.id)}
            className={cn(
              "px-3 py-1.5 text-xs font-medium rounded-[8px] transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-primary",
              isActive
                ? "bg-bg-surface text-ink-primary shadow-sm"
                : "text-gray-warm hover:text-ink-primary hover:bg-bg-surface/50"
            )}
          >
            <span>{tab.label}</span>
            {tab.count !== undefined && (
              <span className="ml-1.5 font-mono text-[10px] px-1.5 py-0.2 rounded-full bg-border text-ink-primary">
                {tab.count}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
