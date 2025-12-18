import { cn } from "@/lib/utils";
import React from "react";

interface GlassCardProps extends React.HTMLAttributes<HTMLDivElement> {
    children: React.ReactNode;
    className?: string;
    intensity?: "low" | "medium" | "high";
}

export function GlassCard({ children, className, intensity = "medium", ...props }: GlassCardProps) {
    const intensities = {
        low: "bg-white/5 border-white/5",
        medium: "bg-white/10 border-white/10",
        high: "bg-white/20 border-white/20",
    };

    return (
        <div
            className={cn(
                "relative overflow-hidden rounded-2xl border backdrop-blur-xl shadow-xl",
                intensities[intensity],
                className
            )}
            {...props}
        >
            {children}
        </div>
    );
}
