"use client";

import { Card, CardContent } from "@/components/ui/card";
import { BarChart3 } from "lucide-react";

export default function AnalyticsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Analytics</h1>
        <p className="text-sm text-zinc-500">
          Unified cross-platform performance analytics
        </p>
      </div>

      <Card>
        <CardContent className="flex flex-col items-center justify-center py-20">
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-zinc-800">
            <BarChart3 className="h-7 w-7 text-zinc-500" />
          </div>
          <h2 className="mt-4 text-lg font-semibold text-zinc-300">
            Coming Soon
          </h2>
          <p className="mt-2 max-w-sm text-center text-sm text-zinc-500">
            Real-time analytics with cross-platform aggregation, AI-generated 
            insights, and performance recommendations are under development.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
