"use client";

import React from "react";
import { cn } from "@/lib/utils";

interface SpinnerProps {
  className?: string;
  size?: "sm" | "md" | "lg";
}

export function Spinner({ className, size = "md" }: SpinnerProps) {
  const dotSize =
    size === "sm" ? "w-1 h-1" : size === "lg" ? "w-2 h-2" : "w-1.5 h-1.5";

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 font-mono select-none",
        className
      )}
      aria-label="Loading..."
    >
      <span className={cn("rounded-full bg-current animate-pulse", dotSize)} />
      <span
        className={cn(
          "rounded-full bg-current animate-pulse [animation-delay:200ms]",
          dotSize
        )}
      />
      <span
        className={cn(
          "rounded-full bg-current animate-pulse [animation-delay:400ms]",
          dotSize
        )}
      />
    </span>
  );
}
