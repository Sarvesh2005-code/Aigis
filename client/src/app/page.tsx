"use client";

import React, { useState, useEffect } from "react";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input"; // We need to create this
import { motion } from "framer-motion";
import { Play, Loader2, CheckCircle, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

export default function Dashboard() {
  const [url, setUrl] = useState("");
  const [jobs, setJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const API_URL = "http://localhost:8000/api";

  const fetchJobs = async () => {
    try {
      const res = await fetch(`${API_URL}/jobs`);
      const data = await res.json();
      // Convert dict to array
      setJobs(Object.values(data).reverse());
    } catch (e) {
      console.error("Failed to fetch jobs", e);
    }
  };

  useEffect(() => {
    const interval = setInterval(fetchJobs, 2000); // Poll every 2s
    return () => clearInterval(interval);
  }, []);

  const handleSubmit = async () => {
    if (!url) return;
    setLoading(true);
    try {
      await fetch(`${API_URL}/jobs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });
      setUrl("");
      fetchJobs();
    } catch (e) {
      alert("Failed to submit job");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-black text-white p-8 font-sans selection:bg-purple-500/30">
      <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 pointer-events-none"></div>
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-purple-600/30 rounded-full blur-[128px] pointer-events-none"></div>
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-blue-600/30 rounded-full blur-[128px] pointer-events-none"></div>

      <div className="max-w-4xl mx-auto relative z-10 space-y-12">
        <header className="text-center space-y-4 pt-10">
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-6xl font-bold tracking-tighter bg-gradient-to-br from-white to-white/50 bg-clip-text text-transparent"
          >
            Aigis
          </motion.h1>
          <p className="text-xl text-white/60">Autonomous Video Intelligence</p>
        </header>

        <section className="space-y-6">
          <GlassCard className="p-2 flex gap-2">
            <input
              type="text"
              placeholder="Paste YouTube Link..."
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="flex-1 bg-transparent border-none outline-none px-6 text-lg placeholder:text-white/20"
            />
            <Button
              size="lg"
              variant="glass"
              onClick={handleSubmit}
              disabled={loading}
              className="rounded-xl px-8"
            >
              {loading ? <Loader2 className="animate-spin" /> : "Initiate"}
            </Button>
          </GlassCard>
        </section>

        <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {jobs.map((job) => (
            <motion.div layout key={job.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
              <GlassCard className="p-6 space-y-4">
                <div className="flex justify-between items-start">
                  <div className="space-y-1">
                    <h3 className="font-semibold text-lg line-clamp-1 text-white/90">{job.url}</h3>
                    <p className="text-xs text-white/40 uppercase tracking-widest">{job.id.slice(0, 8)}</p>
                  </div>
                  <StatusBadge status={job.status} />
                </div>

                <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-white/80"
                    initial={{ width: 0 }}
                    animate={{ width: `${job.progress}%` }}
                  />
                </div>
              </GlassCard>
            </motion.div>
          ))}
        </section>
      </div>
    </main>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: any = {
    pending: "text-yellow-400 bg-yellow-400/10",
    processing: "text-blue-400 bg-blue-400/10",
    completed: "text-green-400 bg-green-400/10",
    failed: "text-red-400 bg-red-400/10",
  };

  return (
    <span className={cn("px-3 py-1 rounded-full text-xs font-medium border border-white/5", styles[status] || styles.pending)}>
      {status}
    </span>
  );
}
