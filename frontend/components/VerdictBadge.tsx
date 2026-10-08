"use client";

import React from "react";
import { CheckCircle2, XCircle, Clock, AlertTriangle, HelpCircle, LucideIcon } from "lucide-react";
import { VerdictType } from "@/lib/api";

interface VerdictBadgeProps {
  verdict: VerdictType;
  size?: "sm" | "md" | "lg";
  className?: string;
}

export const VERDICT_CONFIG: Record<
  VerdictType,
  {
    label: string;
    icon: LucideIcon;
    bgClass: string;
    borderClass: string;
    textClass: string;
    description: string;
  }
> = {
  Verified: {
    label: "Verified",
    icon: CheckCircle2,
    bgClass: "bg-emerald-50",
    borderClass: "border-emerald-200",
    textClass: "text-emerald-800",
    description: "Official sources and records confirm this claim.",
  },
  False: {
    label: "False",
    icon: XCircle,
    bgClass: "bg-rose-50",
    borderClass: "border-rose-200",
    textClass: "text-rose-800",
    description: "Official sources or certified fact-checks directly contradict this claim.",
  },
  Outdated: {
    label: "Outdated",
    icon: Clock,
    bgClass: "bg-amber-50",
    borderClass: "border-amber-200",
    textClass: "text-amber-800",
    description: "This statement was true in the past, but is no longer valid today.",
  },
  "Partly supported": {
    label: "Partly supported",
    icon: AlertTriangle,
    bgClass: "bg-yellow-50",
    borderClass: "border-yellow-200",
    textClass: "text-yellow-900",
    description: "Some elements are accurate, but key parts are missing or misleading.",
  },
  "Cannot be confirmed": {
    label: "Cannot be confirmed",
    icon: HelpCircle,
    bgClass: "bg-slate-100",
    borderClass: "border-slate-300",
    textClass: "text-slate-800",
    description: "No reliable source found in official records or allowlisted fact-checkers.",
  },
};

export default function VerdictBadge({ verdict, size = "md", className = "" }: VerdictBadgeProps) {
  const config = VERDICT_CONFIG[verdict] || VERDICT_CONFIG["Cannot be confirmed"];
  const Icon = config.icon;

  const sizeClasses = {
    sm: "px-2 py-0.5 text-xs gap-1.5",
    md: "px-2.5 py-1 text-sm gap-2",
    lg: "px-3 py-1.5 text-base gap-2.5 font-medium",
  };

  const iconSizes = {
    sm: "w-3.5 h-3.5",
    md: "w-4 h-4",
    lg: "w-5 h-5",
  };

  return (
    <span
      className={`inline-flex items-center rounded-md border font-sans select-none ${config.bgClass} ${config.borderClass} ${config.textClass} ${sizeClasses[size]} ${className}`}
      title={config.description}
      role="status"
    >
      <Icon className={`${iconSizes[size]} flex-shrink-0`} />
      <span>{config.label}</span>
    </span>
  );
}
