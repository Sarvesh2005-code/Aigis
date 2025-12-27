"use client";

import React, { useState, useEffect } from "react";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { motion, AnimatePresence } from "framer-motion";
import { Play, Loader2, CheckCircle, AlertCircle, Wand2, Monitor, Type, Download, Sparkles, Scissors } from "lucide-react";
import { cn } from "@/lib/utils";

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<"clip" | "generate">("clip");
  const [inputVal, setInputVal] = useState("");
  const [jobs, setJobs] = useState<any[]>([]);
  const [genJobs, setGenJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

  const fetchJobs = async () => {
    try {
      // Fetch Clipping Jobs
      const res1 = await fetch(`${API_URL}/jobs`);
      if (!res1.ok) {
        throw new Error(`Failed to fetch clipping jobs: ${res1.status}`);
      }
      const data1 = await res1.json();
      setJobs(Array.isArray(data1) ? data1.reverse() : Object.values(data1).reverse());
      
      // Fetch Generation Jobs
      const res2 = await fetch(`${API_URL}/generate/jobs`);
      if (!res2.ok) {
        throw new Error(`Failed to fetch generation jobs: ${res2.status}`);
      }
      const data2 = await res2.json();
      setGenJobs(Array.isArray(data2) ? data2.reverse() : Object.values(data2).reverse());
    } catch (e) {
      console.error("Failed to fetch jobs", e);
      // Don't show alert on every poll, just log
    }
  };

  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleSubmit = async () => {
    if (!inputVal) return;
    setLoading(true);
    try {
      let response;
      if (activeTab === "clip") {
        response = await fetch(`${API_URL}/jobs`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ url: inputVal }),
        });
      } else {
        response = await fetch(`${API_URL}/generate`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ topic: inputVal }),
        });
      }
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ error: "Unknown error" }));
        throw new Error(error.error || `HTTP ${response.status}`);
      }
      
      setInputVal("");
      fetchJobs();
    } catch (e) {
      const errorMsg = e instanceof Error ? e.message : "Failed to create job";
      alert(`Error: ${errorMsg}`);
      console.error("Job creation failed:", e);
    } finally {
      setLoading(false);
    }
  };

  // Combine jobs for display
  const allJobs = [...genJobs.map(j => ({...j, type: 'gen'})), ...jobs.map(j => ({...j, type: 'clip'}))].sort((a,b) => (b.created_at || 0) - (a.created_at || 0));

  return (
    <main className="min-h-screen bg-[#050505] text-white p-8 font-sans selection:bg-purple-500/30 overflow-hidden">
      {/* Dynamic Background */}
      <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 pointer-events-none"></div>
      <div className="absolute top-[-20%] left-[20%] w-[60%] h-[60%] bg-purple-900/20 rounded-full blur-[180px] pointer-events-none animate-pulse"></div>

      <div className="max-w-5xl mx-auto relative z-10 space-y-12 pb-20">

        {/* Header */}
        <header className="text-center space-y-6 pt-16">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="inline-block"
          >
            <h1 className="text-7xl font-extrabold tracking-tighter bg-gradient-to-b from-white via-white/80 to-white/40 bg-clip-text text-transparent">
              Aigis
            </h1>
            <div className="h-1 w-24 bg-gradient-to-r from-purple-500 to-blue-500 mx-auto mt-2 rounded-full" />
          </motion.div>
          <p className="text-xl text-white/50 max-w-lg mx-auto leading-relaxed">
            The autonomous video intelligence. <br/>
            <span className="text-white font-medium">Clip Podcasts</span> or <span className="text-white font-medium">Generate Shorts</span> instantly.
          </p>
        </header>

        {/* Action Tabs */}
        <div className="flex justify-center gap-4">
          <TabButton 
            active={activeTab === "clip"} 
            onClick={() => setActiveTab("clip")}
            icon={<Scissors className="w-4 h-4" />}
            label="AI Clipper"
          />
           <TabButton 
            active={activeTab === "generate"} 
            onClick={() => setActiveTab("generate")}
            icon={<Sparkles className="w-4 h-4" />}
            label="Auto Generator"
          />
        </div>

        {/* Input Section */}
        <section className="max-w-2xl mx-auto relative">
          <AnimatePresence mode="wait">
            <motion.div 
              key={activeTab}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
            >
              <GlassCard className="p-3 flex gap-3 shadow-2xl shadow-purple-900/20 border-white/10">
                <input
                  type="text"
                  placeholder={activeTab === "clip" ? "Paste YouTube Link (e.g. Podcast)..." : "Enter a Topic (e.g. 'Future of Storage')"}
                  value={inputVal}
                  onChange={(e) => setInputVal(e.target.value)}
                  className="flex-1 bg-transparent border-none outline-none px-6 text-lg placeholder:text-white/20 font-light"
                />
                <Button
                  size="lg"
                  variant="glass"
                  onClick={handleSubmit}
                  disabled={loading}
                  className="rounded-xl px-8 h-12 font-semibold tracking-wide hover:scale-105 transition-transform"
                >
                  {loading ? <Loader2 className="animate-spin" /> : (activeTab === "clip" ? "Clip It" : "Create")}
                </Button>
              </GlassCard>
            </motion.div>
          </AnimatePresence>
        </section>

        {/* Feature Grid */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <FeatureCard
            icon={<Monitor className="w-6 h-6 text-blue-400" />}
            title="Auto-Framing"
            desc="Intelligently tracks speakers and shifts camera focus dynamically."
          />
          <FeatureCard
            icon={<Type className="w-6 h-6 text-pink-400" />}
            title="AI Captions"
            desc="Generates word-accurate subtitles to boost engagement."
          />
          <FeatureCard
            icon={<Wand2 className="w-6 h-6 text-purple-400" />}
            title="Viral Magic"
            desc="Identifies or creates the most engaging moments automatically."
          />
        </section>

        {/* Jobs List */}
        <section className="space-y-6">
          <h2 className="text-2xl font-semibold tracking-tight px-2 flex items-center gap-2">
            Recent Creations <div className="h-px bg-white/10 flex-1 ml-4" />
          </h2>
          {allJobs.length === 0 && (
            <div className="text-center py-20 opacity-30 border border-dashed border-white/10 rounded-2xl">
              <p>No creations yet. Start by pasting a URL or entering a topic.</p>
            </div>
          )}
          <div className="grid grid-cols-1 gap-4">
            {allJobs.map((job) => (
              <JobCard key={job.id} job={job} />
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}

function TabButton({ active, onClick, icon, label }: any) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "flex items-center gap-2 px-6 py-3 rounded-full text-sm font-medium transition-all",
        active 
          ? "bg-white text-black shadow-lg shadow-white/20 scale-105" 
          : "bg-white/5 text-white/60 hover:bg-white/10"
      )}
    >
      {icon}
      {label}
    </button>
  );
}

function JobCard({ job }: { job: any }) {
  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
  const isGen = job.type === 'gen'; // Heuristic
  const title = job.topic || job.url;
  const viralityScore = job.virality_score;
  
  const getViralityColor = (score: number | null | undefined) => {
    if (!score) return "text-white/40";
    if (score >= 80) return "text-green-400";
    if (score >= 60) return "text-yellow-400";
    if (score >= 40) return "text-orange-400";
    return "text-red-400";
  };
  
  return (
    <motion.div layout initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
      <GlassCard className="p-6 flex items-center justify-between group hover:bg-white/5 transition-colors">
        <div className="flex items-center gap-4">
          <div className={cn("h-12 w-12 rounded-lg flex items-center justify-center", isGen ? "bg-purple-500/20" : "bg-blue-500/20")}>
            {isGen ? <Sparkles className="w-5 h-5 text-purple-400" /> : <Play className="w-5 h-5 text-blue-400" />}
          </div>
          <div className="space-y-1">
            <h3 className="font-medium text-white/90 line-clamp-1 max-w-md">{title}</h3>
            <div className="flex items-center gap-3 flex-wrap">
              <p className="text-xs text-white/40 font-mono flex items-center gap-1">
                 {isGen ? "GENERATED" : "CLIPPED"} • {job.id.slice(0, 8)}
              </p>
              {job.status === "completed" && (
                <span className="text-xs text-green-400/80 flex items-center gap-1">
                  <CheckCircle className="w-3 h-3" /> Ready
                </span>
              )}
              {viralityScore !== null && viralityScore !== undefined && (
                <span className={cn("text-xs font-semibold flex items-center gap-1", getViralityColor(viralityScore))} title="Virality Score">
                  ⭐ {Math.round(viralityScore)}
                </span>
              )}
              {job.error && (
                <span className="text-xs text-red-400/80 flex items-center gap-1" title={job.error}>
                  <AlertCircle className="w-3 h-3" /> Error
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <StatusBadge status={job.status} />
          {job.status === "completed" && job.output_url && (
             <a href={`${API_URL.replace('/api', '')}${job.output_url}`} target="_blank" download>
              <Button size="sm" variant="outline" className="h-9 w-9 p-0 rounded-full border-white/10 bg-transparent hover:bg-white/10">
                <Download className="w-4 h-4" />
              </Button>
            </a>
          )}
        </div>
      </GlassCard>
      {/* Progress Bar */}
      {job.status !== 'completed' && job.status !== 'failed' && (
        <div className="h-0.5 w-full bg-white/5 mt-[-1px] relative z-20 overflow-hidden rounded-b-xl">
          <motion.div
            className={cn("h-full", isGen ? "bg-gradient-to-r from-pink-500 to-purple-500" : "bg-gradient-to-r from-blue-500 to-cyan-500")}
            initial={{ width: 0 }}
            animate={{ width: `${job.progress || 10}%` }}
          />
        </div>
      )}
    </motion.div>
  )
}

function FeatureCard({ icon, title, desc }: { icon: any, title: string, desc: string }) {
  return (
    <GlassCard className="p-6 space-y-3 hover:bg-white/5 transition-colors cursor-default">
      <div className="h-10 w-10 rounded-full bg-white/5 flex items-center justify-center border border-white/5">
        {icon}
      </div>
      <h3 className="font-semibold text-lg">{title}</h3>
      <p className="text-sm text-white/50 leading-relaxed">{desc}</p>
    </GlassCard>
  )
}

function StatusBadge({ status }: { status: string }) {
  const styles: any = {
    pending: "text-zinc-400 bg-zinc-400/10 border-zinc-500/20",
    downloading: "text-blue-400 bg-blue-400/10 border-blue-500/20",
    processing: "text-purple-400 bg-purple-400/10 border-purple-500/20",
    completed: "text-emerald-400 bg-emerald-400/10 border-emerald-500/20",
    failed: "text-red-400 bg-red-400/10 border-red-500/20",
  };

  return (
    <span className={cn("px-3 py-1 rounded-full text-xs font-medium border uppercase tracking-wider", styles[status] || styles.pending)}>
      {status}
    </span>
  );
}
