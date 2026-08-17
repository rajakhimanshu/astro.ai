"use client";

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Star, Plus, Check, LayoutDashboard, MessageSquare, Shield, Zap, ChevronRight, Menu, X, Clock, Compass, Square, Sun, Moon, User, BookOpen, Calendar, TrendingUp, Heart, AlertCircle, Target } from 'lucide-react';

const API_BASE = "http://127.0.0.1:8001/api";

// ─────────────────────────────────────────────────────────────────────────────
// UI COMPONENTS
// ─────────────────────────────────────────────────────────────────────────────

const Badge = ({ children, color = "neutral" }: { children: React.ReactNode, color?: string }) => {
    const colors: any = {
        gold: "bg-classic-gold/10 text-classic-gold border-classic-gold/30",
        neutral: "bg-ink-900/[0.03] text-ink-600 border-ink-900/10",
        green: "bg-emerald-600/10 text-emerald-700 border-emerald-600/20",
        red: "bg-terracotta/10 text-terracotta border-terracotta/20",
        blue: "bg-deep-navy/10 text-deep-navy border-deep-navy/20",
    };
    return (
        <span className={`px-2 py-0.5 rounded-md text-[9px] font-bold uppercase tracking-[0.2em] border ${colors[color] || colors.neutral}`}>
            {children}
        </span>
    );
};

const NorthIndianChart = ({ chartData, title }: { chartData: any, title: string }) => {
    if (!chartData) return null;

    const lagnaSignIdx = chartData.ASC?.sign_idx ?? 0;
    const getSignForHouse = (h: number) => (lagnaSignIdx + h - 1) % 12 + 1;

    const houseOccupants: Record<number, string[]> = {};
    Object.entries(chartData).forEach(([p, data]: [string, any]) => {
        if (p === 'ASC') return;
        const h = data.house;
        if (!houseOccupants[h]) houseOccupants[h] = [];
        const shortName = p === 'Sun' ? 'Su' : p === 'Moon' ? 'Mo' : p === 'Mars' ? 'Ma' : p === 'Mercury' ? 'Me' : p === 'Jupiter' ? 'Ju' : p === 'Venus' ? 'Ve' : p === 'Saturn' ? 'Sa' : p === 'Rahu' ? 'Ra' : p === 'Ketu' ? 'Ke' : p;
        houseOccupants[h].push(shortName);
    });

    const boxSize = 400;
    const mid = boxSize / 2;

    const housePositions = [
        { h: 1,  x: mid,   y: mid/2,   lx: mid,   ly: mid/4 },
        { h: 2,  x: mid/2, y: mid/4,   lx: mid/4, ly: mid/8 },
        { h: 3,  x: mid/4, y: mid/2,   lx: mid/8, ly: mid/4 },
        { h: 4,  x: mid/2, y: mid,     lx: mid/4, ly: mid },
        { h: 5,  x: mid/4, y: mid*1.5, lx: mid/8, ly: mid*1.75 },
        { h: 6,  x: mid/2, y: mid*1.75,lx: mid/4, ly: mid*1.9 },
        { h: 7,  x: mid,   y: mid*1.5, lx: mid,   ly: mid*1.75 },
        { h: 8,  x: mid*1.5,y: mid*1.75,lx: mid*1.75,ly: mid*1.9},
        { h: 9,  x: mid*1.75,y: mid*1.5, lx: mid*1.9,ly: mid*1.75},
        { h: 10, x: mid*1.5,y: mid,     lx: mid*1.75,ly: mid },
        { h: 11, x: mid*1.75,y: mid/2,   lx: mid*1.9,ly: mid/4 },
        { h: 12, x: mid*1.5,y: mid/4,   lx: mid*1.75,ly: mid/8 },
    ];

    const lineVariants = {
        hidden: { pathLength: 0, opacity: 0 },
        visible: { 
            pathLength: 1, 
            opacity: 1,
            transition: { duration: 1.5, ease: "easeInOut" as const }
        }
    };


    return (
        <div className="flex flex-col items-center w-full group">
            <motion.h4 
                initial={{ opacity: 0, letterSpacing: "0.1em" }}
                animate={{ opacity: 1, letterSpacing: "0.3em" }}
                className="text-[11px] text-ink-600 uppercase font-bold mb-10 text-center"
            >
                {title}
            </motion.h4>
            <div className="relative w-full aspect-square max-w-[360px]">
                <svg viewBox={`0 0 ${boxSize} ${boxSize}`} className="w-full h-full text-ink-900 overflow-visible">
                    {/* Background Glow */}
                    <defs>
                        <radialGradient id="chartGlow" cx="50%" cy="50%" r="50%" fx="50%" fy="50%">
                            <stop offset="0%" stopColor="var(--color-classic-gold)" stopOpacity="0.05" />
                            <stop offset="100%" stopColor="var(--color-classic-gold)" stopOpacity="0" />
                        </radialGradient>
                    </defs>
                    <rect x="-20" y="-20" width={boxSize+40} height={boxSize+40} fill="url(#chartGlow)" />

                    {/* Outer Frame */}
                    <motion.rect 
                        variants={lineVariants} initial="hidden" animate="visible"
                        x="0" y="0" width={boxSize} height={boxSize} 
                        fill="none" stroke="currentColor" strokeWidth="1.5" 
                    />
                    
                    {/* Inner Diamond */}
                    <motion.rect 
                        variants={lineVariants} initial="hidden" animate="visible"
                        x={mid/2} y={mid/2} width={mid} height={mid} 
                        fill="none" stroke="currentColor" strokeWidth="1" 
                        transform={`rotate(45 ${mid} ${mid})`} 
                    />
                    
                    {/* Cross Lines */}
                    <motion.line 
                        variants={lineVariants} initial="hidden" animate="visible"
                        x1="0" y1="0" x2={boxSize} y2={boxSize} 
                        stroke="currentColor" strokeWidth="1" 
                    />
                    <motion.line 
                        variants={lineVariants} initial="hidden" animate="visible"
                        x1={boxSize} y1="0" x2="0" y2={boxSize} 
                        stroke="currentColor" strokeWidth="1" 
                    />
                    
                    {housePositions.map((pos, idx) => {
                        const sign = getSignForHouse(pos.h);
                        const occupants = houseOccupants[pos.h] || [];
                        return (
                            <motion.g 
                                key={pos.h}
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                transition={{ delay: 0.5 + idx * 0.05 }}
                            >
                                {/* Sign Number */}
                                <text x={pos.x} y={pos.y - 5} textAnchor="middle" className="fill-ink-400 font-sans text-[26px] font-medium opacity-20 select-none">{sign}</text>
                                
                                {/* Planets */}
                                {occupants.length > 0 && (
                                    <motion.g
                                        initial={{ scale: 0.5, opacity: 0 }}
                                        animate={{ scale: 1, opacity: 1 }}
                                        transition={{ delay: 1.2 + idx * 0.1, type: "spring" }}
                                    >
                                        <text x={pos.x} y={pos.y + 15} textAnchor="middle" className="fill-ink-900 font-bold text-[14px] tracking-tighter filter drop-shadow-sm">
                                            {occupants.slice(0, 3).join(' ')}
                                        </text>
                                        {occupants.length > 3 && (
                                            <text x={pos.x} y={pos.y + 32} textAnchor="middle" className="fill-ink-900 font-bold text-[14px] tracking-tighter">
                                                {occupants.slice(3, 6).join(' ')}
                                            </text>
                                        )}
                                    </motion.g>
                                )}
                                
                                {/* House Label */}
                                <text x={pos.lx} y={pos.ly} textAnchor="middle" className="fill-ink-400 font-bold text-[8px] uppercase tracking-tighter opacity-40">H{pos.h}</text>
                            </motion.g>
                        );
                    })}
                </svg>
            </div>
        </div>
    );
};

// ─── Toast Notification ─────────────────────────────────────────────────────
const Toast = ({ message, type, onClose }: { message: string; type: 'success' | 'error' | 'info'; onClose: () => void }) => {
  const colors = { success: 'bg-emerald-600', error: 'bg-terracotta', info: 'bg-classic-gold' };
  useEffect(() => { const t = setTimeout(onClose, 3500); return () => clearTimeout(t); }, [onClose]);
  return (
    <motion.div initial={{ opacity: 0, y: 30, scale: 0.95 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: 20 }}
      className={`fixed bottom-8 right-8 z-[200] ${colors[type]} text-white px-6 py-4 rounded-2xl shadow-2xl flex items-center gap-3 max-w-sm`}>
      <Check className="w-5 h-5 shrink-0" />
      <span className="font-bold text-sm">{message}</span>
    </motion.div>
  );
};

export default function Page() {
  const [users, setUsers] = useState<any[]>([]);
  const [activeUser, setActiveUser] = useState<string | null>(null);
  const [profile, setProfile] = useState<any>(null);
  const [messages, setMessages] = useState<any[]>([]);
  const [llmMode, setLlmMode] = useState<string>("Ollama");
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [activeView, setActiveView] = useState("reading");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [darkMode, setDarkMode] = useState(false);
  const [selectedChart, setSelectedChart] = useState<any>(null);
  const [selectedChartTitle, setSelectedChartTitle] = useState("");
  // Conversation history (multi-turn memory)
  const [conversationHistory, setConversationHistory] = useState<any[]>([]);
  // Life Events
  const [events, setEvents] = useState<any[]>([]);
  const [eventForm, setEventForm] = useState({ date: new Date().toISOString().split('T')[0], title: '', description: '', domain: 'career', emotion_score: 0, outcome: '' });
  const [eventsLoading, setEventsLoading] = useState(false);
  const [predictions, setPredictions] = useState<any[]>([]);
  const [accuracy, setAccuracy] = useState<any>(null);
  const [predictionsLoading, setPredictionsLoading] = useState(false);
  const [knowledgeStats, setKnowledgeStats] = useState<any>(null);
  const [youtubeUrls, setYoutubeUrls] = useState("");
  const [knowledgeLoading, setKnowledgeLoading] = useState(false);
  const [ingestResult, setIngestResult] = useState<any>(null);
  // Toast
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null);
  const showToast = useCallback((message: string, type: 'success' | 'error' | 'info' = 'success') => {
    setToast({ message, type });
  }, []);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatScrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const isDark = localStorage.getItem('jyotish_theme') === 'dark';
    setDarkMode(isDark);
    if (isDark) document.documentElement.classList.add('dark');
    // Restore conversation history from localStorage
    try {
      const saved = localStorage.getItem('jyotish_conv_history');
      if (saved) setConversationHistory(JSON.parse(saved));
      const savedMsgs = localStorage.getItem('jyotish_messages');
      if (savedMsgs) setMessages(JSON.parse(savedMsgs));
    } catch (_) {}
  }, []);

  // Persist conversation history to localStorage whenever it changes
  useEffect(() => {
    if (conversationHistory.length > 0)
      localStorage.setItem('jyotish_conv_history', JSON.stringify(conversationHistory.slice(-30)));
  }, [conversationHistory]);

  useEffect(() => {
    if (messages.length > 0)
      localStorage.setItem('jyotish_messages', JSON.stringify(messages.slice(-40)));
  }, [messages]);

  const toggleDarkMode = () => {
    const nextDark = !darkMode;
    setDarkMode(nextDark);
    if (nextDark) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('jyotish_theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('jyotish_theme', 'light');
    }
  };
  const abortControllerRef = useRef<AbortController | null>(null);

  const [formData, setFormData] = useState({
    name: "", gender: "Male", year: 2000, month: 1, day: 1, 
    hour: 12, minute: 0, city: "", nation: "IN", timezone: "Asia/Kolkata"
  });

  const [editBirth, setEditBirth] = useState<any>(null);
  const [userStory, setUserStory] = useState("");

  useEffect(() => {
    if (profile?.meta?.birth) {
        setEditBirth({
            ...profile.meta.birth,
            name: profile.meta.name
        });
    }
  }, [profile]);

  const fetchProfile = async (userId: string) => {
    try {
      const res = await fetch(`${API_BASE}/users/${userId}/profile`, { mode: 'cors' });
      if (res.ok) {
        const data = await res.json();
        setActiveUser(userId);
        setProfile(data);
        fetchEvents(userId);
        fetchPredictions(userId);
        if (messages.length === 0) {
          setMessages([{ role: "bot", content: `Greetings, ${data.meta?.name || 'Consultant'}.\n\nThe celestial archive is ready. What would you like to explore today?` }]);
        }
      }
    } catch(e) { console.error(e); }
  }

  const fetchUsers = async () => {
    try {
      const res = await fetch(`${API_BASE}/users`, { mode: 'cors' });
      if (res.ok) {
        const data = await res.json();
        setUsers(data.users || []);
        if (data.llm_mode) setLlmMode(data.llm_mode);
        if (data.active_user_id) fetchProfile(data.active_user_id);
      }
    } catch(e) { console.error(e); }
  }

  useEffect(() => { fetchUsers(); fetchKnowledgeStats(); }, []);

  const fetchKnowledgeStats = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/knowledge/stats`, { mode: 'cors' });
      if (res.ok) { const d = await res.json(); setKnowledgeStats(d.data || null); }
    } catch (_) {}
  }, []);

  const ingestYoutube = async () => {
    const urls = youtubeUrls.split(/[\n,]+/).map(u => u.trim()).filter(Boolean);
    if (!urls.length) { showToast('Paste at least one YouTube URL.', 'error'); return; }
    setKnowledgeLoading(true);
    setIngestResult(null);
    try {
      const res = await fetch(`${API_BASE}/knowledge/youtube`, {
        method: 'POST', mode: 'cors',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ urls, force: false }),
      });
      const data = await res.json();
      if (res.ok) {
        setIngestResult(data);
        showToast(`Indexed ${data.indexed} video(s), ${data.total_chunks} chunks added.`, 'success');
        fetchKnowledgeStats();
      } else {
        showToast(data.detail || 'Ingest failed. Is Ollama running?', 'error');
      }
    } catch (_) { showToast('Network error — is backend on port 8001?', 'error'); }
    setKnowledgeLoading(false);
  };

  // Reset scroll on view change
  useEffect(() => {
    if (chatScrollRef.current) chatScrollRef.current.scrollTop = 0;
  }, [activeView]);

  const switchUser = async (userId: string) => {
    try {
      await fetch(`${API_BASE}/users/active`, {
        method: 'POST', mode: 'cors',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId })
      });
      fetchProfile(userId);
      setMessages([]);
      setConversationHistory([]);
      localStorage.removeItem('jyotish_conv_history');
      localStorage.removeItem('jyotish_messages');
    } catch(e) { console.error(e); }
  }

  const toggleLlmMode = async () => {
    const newMode = llmMode.toLowerCase() === "ollama" ? "groq" : "ollama";
    try {
        const res = await fetch(`${API_BASE}/config`, {
            method: 'POST',
            mode: 'cors',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ llm_mode: newMode })
        });
        if (res.ok) {
            setLlmMode(newMode.charAt(0).toUpperCase() + newMode.slice(1));
        }
    } catch (e) { console.error(e); }
  }

  const handleStopChat = () => {
    if (abortControllerRef.current) {
        abortControllerRef.current.abort();
        abortControllerRef.current = null;
        setIsTyping(false);
    }
  };

  const handleChat = async () => {
    if (!input.trim() || isTyping) return;
    const msg = input;
    setInput("");
    const userMsg = { role: "user", content: msg };
    setMessages((prev: any) => [...prev, userMsg]);
    setIsTyping(true);

    // Build history to send (exclude the message we just added)
    const historyToSend = conversationHistory.slice(-20);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        mode: 'cors',
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: msg,
          user_id: activeUser,
          conversation_history: historyToSend
        }),
        signal: controller.signal
      });
      if (!res.ok) throw new Error(`Server status ${res.status}`);
      if (!res.body) throw new Error("Divine channel is empty.");

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let botResponse = "";
      setMessages((prev: any) => [...prev, { role: "bot", content: "" }]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        botResponse += decoder.decode(value);
        setMessages((prev: any) => {
          const newMsg = [...prev];
          newMsg[newMsg.length - 1] = { role: "bot", content: botResponse };
          return newMsg;
        });
      }

      // Update conversation history after successful response
      setConversationHistory(prev => [
        ...prev,
        { role: "user", content: msg },
        { role: "bot", content: botResponse }
      ]);
    } catch (e: any) {
      if (e.name !== 'AbortError') {
        console.error("Chat error:", e);
        setMessages((prev: any) => [...prev, { role: "bot", content: `Network error. Mode: ${llmMode}. Error: ${e.message}` }]);
      }
    } finally {
      setIsTyping(false);
      abortControllerRef.current = null;
    }
  }

  useEffect(() => {
    if (messagesEndRef.current && !isTyping) {
        messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, isTyping]);

  const fetchPredictions = useCallback(async (uid: string) => {
    try {
      const [predRes, accRes] = await Promise.all([
        fetch(`${API_BASE}/users/${uid}/predictions`, { mode: 'cors' }),
        fetch(`${API_BASE}/users/${uid}/accuracy`, { mode: 'cors' }),
      ]);
      if (predRes.ok) { const d = await predRes.json(); setPredictions(d.predictions || []); }
      if (accRes.ok) { const d = await accRes.json(); setAccuracy(d.data || null); }
    } catch (_) {}
  }, []);

  const verifyPrediction = async (predictionId: number, happened: boolean) => {
    if (!activeUser) return;
    setPredictionsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/users/${activeUser}/predictions/${predictionId}/verify`, {
        method: 'POST', mode: 'cors',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ happened, outcome_note: happened ? 'Confirmed by user' : 'Did not happen' }),
      });
      if (res.ok) {
        showToast(happened ? 'Prediction marked as HIT — system learned!' : 'Prediction marked as miss — calibration updated.', 'success');
        fetchPredictions(activeUser);
        fetchEvents(activeUser);
      } else {
        showToast('Failed to verify prediction.', 'error');
      }
    } catch (_) { showToast('Network error.', 'error'); }
    setPredictionsLoading(false);
  };

  const fetchEvents = useCallback(async (uid: string) => {
    try {
      const res = await fetch(`${API_BASE}/users/${uid}/events`, { mode: 'cors' });
      if (res.ok) { const d = await res.json(); setEvents(d.events || []); }
    } catch (_) {}
  }, []);

  const logEvent = async () => {
    if (!eventForm.title || !eventForm.date || !activeUser) return;
    setEventsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/users/${activeUser}/events`, {
        method: 'POST', mode: 'cors',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(eventForm)
      });
      if (res.ok) {
        showToast('Life event logged! The system has learned from this.', 'success');
        setEventForm({ date: new Date().toISOString().split('T')[0], title: '', description: '', domain: 'career', emotion_score: 0, outcome: '' });
        fetchEvents(activeUser);
      } else {
        showToast('Failed to log event.', 'error');
      }
    } catch (e) { showToast('Network error logging event.', 'error'); }
    setEventsLoading(false);
  };

  const clearHistory = () => {
    setConversationHistory([]);
    setMessages([]);
    localStorage.removeItem('jyotish_conv_history');
    localStorage.removeItem('jyotish_messages');
    showToast('Conversation cleared.', 'info');
  };

  const navigation = [
    { id: 'reading', label: 'Consultation', icon: MessageSquare },
    { id: 'charts', label: 'Horoscopes', icon: LayoutDashboard },
    { id: 'analysis', label: 'Synthesis', icon: Zap },
    { id: 'timeline', label: 'Timeline', icon: Clock },
    { id: 'events', label: 'Events', icon: Calendar },
    { id: 'predictions', label: 'Predictions', icon: Target },
    { id: 'knowledge', label: 'Knowledge', icon: BookOpen },
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'remedies', label: 'Prescriptions', icon: Shield },
  ];

  return (
    <main className="flex w-full h-full bg-cream-100 text-ink-900 overflow-hidden font-sans selection:bg-classic-gold/20 paper-texture">
      <aside className={`transition-all duration-500 ease-in-out ${sidebarOpen ? 'w-[340px] opacity-100' : 'w-0 opacity-0'} h-full border-r border-ink-900/10 bg-cream-50 flex flex-col shrink-0 overflow-hidden relative z-30 shadow-lg`}>
        <div className="p-8 flex items-center justify-between border-b border-ink-900/5">
           <div className="flex items-center space-x-4"><Compass className="w-6 h-6 text-terracotta" strokeWidth={1.5} /><span className="font-bold tracking-[0.25em] text-ink-900 text-[13px] uppercase">Jyotish Oracle</span></div>
           <button onClick={() => setSidebarOpen(false)} className="md:hidden text-ink-400 hover:text-ink-900"><X className="w-5 h-5" /></button>
        </div>
        <div className="flex-1 overflow-y-auto p-8 space-y-12 custom-scrollbar">
            <section><label className="text-[10px] font-bold text-ink-400 uppercase tracking-[0.2em] block mb-3">Client Manifest</label>
                <div className="relative group">
                    <select className="w-full bg-transparent border-b border-ink-900/10 pb-2 text-[15px] font-semibold text-ink-900 outline-none focus:border-terracotta transition-all appearance-none cursor-pointer hover:border-ink-600 rounded-none" value={activeUser || ""} onChange={(e) => switchUser(e.target.value)}>{users.map((u: any) => <option key={u.user_id} value={u.user_id}>{u.name}</option>)}</select>
                    <ChevronRight className="w-4 h-4 absolute right-0 top-0 text-ink-400 transform rotate-90 pointer-events-none" />
                </div>
            </section>
            <AnimatePresence>{profile && (
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-12">
                    <section className="p-6 bg-white dark:bg-zinc-900/40 border border-ink-900/5 dark:border-white/5 shadow-sm rounded-xl space-y-6">
                        <div className="flex items-center justify-between border-b border-ink-900/5 dark:border-white/5 pb-4"><span className="text-[10px] font-bold text-ink-400 uppercase tracking-[0.2em]">Ascendant</span><Badge color="gold">{profile.lagna?.sign || "Unknown"}</Badge></div>
                        <div className="space-y-4 text-xs">
                            <div className="flex justify-between font-medium"><span>Degree</span><span className="font-bold">{profile.lagna?.degree ?? "?"}°</span></div>
                            <div className="flex justify-between font-medium"><span>Nakshatra</span><span className="font-bold">{profile.lagna?.nakshatra || "?"}</span></div>
                            <div className="flex justify-between font-medium"><span>Lagna Lord</span><span className="font-bold">{profile.lagna?.lord || "?"} (H{profile.lagna?.lord_house ?? "?"})</span></div>
                        </div>
                    </section>

                    {profile.panchanga && (
                        <section className="p-6 bg-cream-50 dark:bg-white/5 border border-ink-900/5 dark:border-white/5 shadow-sm rounded-xl space-y-6">
                            <div className="flex items-center justify-between border-b border-ink-900/5 dark:border-white/5 pb-4">
                                <span className="text-[10px] font-bold text-ink-400 uppercase tracking-[0.2em]">Birth Panchanga</span>
                                <Sun className="w-3 h-3 text-classic-gold" />
                            </div>
                            <div className="grid grid-cols-2 gap-4 text-[10px]">
                                <div className="space-y-1">
                                    <p className="text-ink-400 uppercase tracking-tighter">Tithi</p>
                                    <p className="font-bold text-ink-900 dark:text-white">{profile.panchanga.tithi?.name} ({profile.panchanga.tithi?.paksha})</p>
                                </div>
                                <div className="space-y-1">
                                    <p className="text-ink-400 uppercase tracking-tighter">Vara</p>
                                    <p className="font-bold text-ink-900 dark:text-white">{profile.panchanga.vara?.name}</p>
                                </div>
                                <div className="space-y-1">
                                    <p className="text-ink-400 uppercase tracking-tighter">Nakshatra</p>
                                    <p className="font-bold text-ink-900 dark:text-white">{profile.panchanga.nakshatra?.lord} ({profile.panchanga.nakshatra?.pada}P)</p>
                                </div>
                                <div className="space-y-1">
                                    <p className="text-ink-400 uppercase tracking-tighter">Yoga</p>
                                    <p className="font-bold text-ink-900 dark:text-white">{profile.panchanga.yoga?.name}</p>
                                </div>
                            </div>
                        </section>
                    )}
                    <section><label className="text-[10px] font-bold text-ink-400 uppercase tracking-[0.2em] block mb-5">Current Dasha Timeline</label>
                        <div className="space-y-3">
                            {[{ label: 'Mahadasha', lord: profile.dasha?.current_md, end: profile.dasha?.md_end_display || profile.dasha?.md_end, highlight: true }, { label: 'Antardasha', lord: profile.dasha?.current_ad, end: profile.dasha?.ad_end_display || profile.dasha?.ad_end, highlight: false }, { label: 'Pratyantar', lord: profile.dasha?.current_pd, end: profile.dasha?.pd_end_display || profile.dasha?.pd_end, highlight: false }].map((d, i) => (
                                <div key={i} className={`flex items-center justify-between p-4 rounded-xl border transition-all ${d.highlight ? 'bg-cream-100 dark:bg-terracotta/5 border-classic-gold/30 shadow-sm' : 'bg-white dark:bg-zinc-900/40 border-ink-900/5 dark:border-white/5'}`}><div><p className="text-[9px] text-ink-400 font-bold uppercase tracking-[0.15em]">{d.label}</p><p className={`text-[15px] mt-1 font-bold ${d.highlight ? 'text-terracotta' : 'text-ink-900 dark:text-white'}`}>{d.lord || "?"}</p></div><div className="text-right"><p className="text-[8px] text-ink-400 font-bold uppercase tracking-widest">Until</p><p className="text-[11px] text-ink-600 dark:text-ink-300 mt-1 font-medium">{d.end ? new Date(d.end.includes('T') ? d.end : d.end + 'T12:00:00').toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' }) : "?"}</p></div></div>
                            ))}
                        </div>
                    </section>
                    {profile.chara_dasha && (
                        <section><label className="text-[10px] font-bold text-ink-400 uppercase tracking-[0.2em] block mb-5">Jaimini Sign Clock</label>
                            <div className="p-4 bg-white dark:bg-zinc-900/40 border border-ink-900/5 dark:border-white/5 rounded-xl space-y-2">
                                <div className="flex justify-between items-baseline">
                                    <span className="text-[15px] font-black text-terracotta uppercase">{profile.chara_dasha.current_md?.sign} MD</span>
                                    <span className="text-[11px] font-bold text-ink-900 dark:text-white">{profile.chara_dasha.current_md?.years} Years</span>
                                </div>
                                <p className="text-[10px] text-ink-400 font-bold uppercase tracking-widest">Active: {new Date(profile.chara_dasha.current_md?.start).getFullYear()} — {new Date(profile.chara_dasha.current_md?.end).getFullYear()}</p>
                            </div>
                        </section>
                    )}
                    <section><label className="text-[10px] font-bold text-ink-400 uppercase tracking-[0.2em] block mb-5">Planetary Potency (Rupas)</label>
                        <div className="space-y-4 bg-white dark:bg-zinc-900/40 p-6 rounded-xl border border-ink-900/5 dark:border-white/5 shadow-sm">
                            {['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'].map((name) => {
                                const score = profile.shadbala?.[name] || 0;
                                const full = profile.shadbala_full?.[name] || {};
                                const isPass = full.status === 'PASS';
                                
                                return (
                                    <div key={name} className="space-y-2 group">
                                        <div className="flex justify-between items-baseline">
                                            <span className="text-[11px] text-ink-800 font-bold tracking-tight">{name}</span>
                                            <div className="flex items-center gap-2">
                                                <span className={`text-[10px] font-black ${isPass ? 'text-emerald-600' : 'text-terracotta'}`}>{score.toFixed(1)}/10</span>
                                                <div className={`w-1.5 h-1.5 rounded-full ${isPass ? 'bg-emerald-500' : 'bg-terracotta'} opacity-40`} />
                                            </div>
                                        </div>
                                        <div className="w-full h-[2px] bg-cream-200 dark:bg-white/10 rounded-full overflow-hidden">
                                            <motion.div 
                                                initial={{ width: 0 }}
                                                animate={{ width: `${Math.min(score * 10, 100)}%` }}
                                                className={`h-full ${isPass ? 'bg-emerald-500' : 'bg-terracotta'}`} 
                                            />
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </section>
                </motion.div>
            )}</AnimatePresence>
        </div>
        <div className="p-8 border-t border-ink-900/10 bg-cream-50"><button onClick={() => setShowProfileModal(true)} className="w-full flex items-center justify-center space-x-3 py-4 bg-ink-900 text-white rounded-xl hover:bg-ink-800 active:scale-[0.98] transition-all font-bold text-[11px] uppercase tracking-[0.2em] shadow-lg"><Plus className="w-4 h-4" strokeWidth={2.5}/><span>New Archives</span></button></div>
      </aside>

      <div className="flex-1 flex flex-col h-full overflow-hidden relative">
        <nav className="h-24 border-b border-ink-900/10 flex items-center justify-between px-12 bg-cream-100/90 backdrop-blur-xl shrink-0 z-20">
            <div className="flex space-x-12 h-full">{navigation.map((nav) => (
                    <button key={nav.id} onClick={() => setActiveView(nav.id)} className={`relative flex items-center h-full transition-all text-[11px] font-bold uppercase tracking-[0.2em] ${activeView === nav.id ? 'text-ink-900' : 'text-ink-400 hover:text-ink-600'}`}><span>{nav.label}</span>{activeView === nav.id && <motion.div layoutId="nav-indicator" className="absolute bottom-0 left-0 right-0 h-[2px] bg-terracotta" />}</button>
                ))}</div>
            <div className="flex items-center space-x-6">
                <button 
                    onClick={toggleDarkMode}
                    className="p-3 rounded-full hover:bg-ink-900/5 dark:hover:bg-white/5 transition-colors"
                    title={darkMode ? "Switch to Light Mode" : "Switch to Dark Mode"}
                >
                    {darkMode ? <Sun className="w-5 h-5 text-classic-gold" /> : <Moon className="w-5 h-5 text-ink-600" />}
                </button>
                <button 
                    onClick={toggleLlmMode}
                    className="flex flex-col items-end hover:opacity-70 transition-opacity"
                    title="Click to switch LLM Engine"
                >
                    <span className="text-[8px] font-black text-ink-400 uppercase tracking-widest">Engine</span>
                    <span className={`text-[10px] font-bold uppercase tracking-wider ${llmMode.toLowerCase() === 'groq' ? 'text-terracotta' : 'text-classic-gold'}`}>
                        {llmMode}
                    </span>
                </button>
                {!sidebarOpen && <button onClick={() => setSidebarOpen(true)} className="text-ink-600 hover:text-ink-900 transition-colors ml-4"><Menu className="w-6 h-6" /></button>}
            </div>
        </nav>

        <div ref={chatScrollRef} className="flex-1 overflow-y-auto custom-scrollbar relative">
            <AnimatePresence mode="wait">
                <motion.div key={activeView} initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -15 }} transition={{ duration: 0.3 }} className="min-h-full">
                    {activeView === 'reading' && (
                        <div className="flex flex-col min-h-full max-w-4xl mx-auto w-full">
                            <div className="flex-1 p-10 md:p-16 space-y-12 pb-32">{messages.map((m: any, i: number) => (
                                    <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                                        {m.role === 'bot' && <div className="w-10 h-10 mr-5 rounded-full border border-ink-900/10 dark:border-white/10 flex items-center justify-center shrink-0 mt-1 bg-white dark:bg-zinc-900 shadow-sm"><Compass className="w-5 h-5 text-terracotta" /></div>}
                                        <div className={`p-7 text-[16px] leading-[1.8] max-w-[85%] whitespace-pre-wrap shadow-sm rounded-2xl ${m.role === 'user' ? 'bg-ink-900 dark:bg-zinc-800 border border-ink-900 dark:border-zinc-700 text-white font-medium rounded-tr-sm shadow-md' : 'bg-white dark:bg-zinc-900/60 border border-ink-900/10 dark:border-white/10 text-ink-800 dark:text-ink-900 font-medium'}`}>{m.content}</div>
                                    </div>
                                ))}<div ref={messagesEndRef} className="h-8" /></div>
                            <div className="sticky bottom-0 p-8 bg-gradient-to-t from-cream-100 via-cream-100 dark:from-cream-100 dark:via-cream-100 to-transparent pt-16 z-20">
                                <div className="flex items-center relative group">
                                    <input type="text" value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && handleChat()} placeholder="Ask about transits or karma..." className="w-full bg-white dark:bg-zinc-900/80 border border-ink-900/10 dark:border-white/10 p-6 pl-8 pr-32 rounded-full text-[16px] font-medium text-ink-900 placeholder-ink-400 focus:outline-none shadow-md focus:border-terracotta/40 dark:focus:border-terracotta/40 transition-colors" />
                                    <div className="absolute right-3 flex items-center space-x-2">
                                        {isTyping ? <button onClick={handleStopChat} className="p-4 bg-terracotta/10 text-terracotta rounded-full hover:bg-terracotta hover:text-white transition-all border border-terracotta/20"><Square className="w-4 h-4 fill-current" /></button> : <button onClick={handleChat} disabled={!profile} className="p-4 bg-ink-900 dark:bg-zinc-800 text-white rounded-full hover:bg-terracotta transition-all disabled:opacity-50 shadow-lg"><ChevronRight className="w-6 h-6" strokeWidth={2.5} /></button>}
                                     {!isTyping && messages.length > 1 && (
                                       <button onClick={clearHistory} title="Clear conversation" className="p-4 bg-ink-900/5 dark:bg-white/10 text-ink-400 rounded-full hover:bg-terracotta/10 hover:text-terracotta transition-all" >
                                         <X className="w-4 h-4" />
                                       </button>
                                     )}
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                    {activeView === 'charts' && profile && (
                        <div className="p-10 md:p-14 max-w-7xl mx-auto space-y-24">
                            <div className="grid grid-cols-1 xl:grid-cols-2 gap-12 md:gap-16">
                                <motion.div 
                                    initial={{ opacity: 0, x: -20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    className="p-12 md:p-16 bg-white dark:bg-zinc-900/40 border border-ink-900/10 dark:border-white/5 rounded-[3rem] flex flex-col items-center shadow-xl relative overflow-hidden group hover:border-classic-gold/30 transition-colors"
                                >
                                    <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-classic-gold/20 to-transparent" />
                                    <NorthIndianChart chartData={profile.planets} title="D1 Rashi • Root Destiny" />
                                </motion.div>
                                <motion.div 
                                    initial={{ opacity: 0, x: 20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: 0.2 }}
                                    className="p-12 md:p-16 bg-white dark:bg-zinc-900/40 border border-ink-900/10 dark:border-white/5 rounded-[3rem] flex flex-col items-center shadow-xl relative overflow-hidden group hover:border-terracotta/30 transition-colors"
                                >
                                    <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-terracotta/20 to-transparent" />
                                    <NorthIndianChart chartData={profile.divisional_charts?.['9']} title="D9 Navamsa • Soul Essence" />
                                </motion.div>
                            </div>

                            <div className="space-y-12">
                                <div className="flex items-center justify-between border-b border-ink-900/10 dark:border-white/5 pb-6">
                                    <div className="space-y-1">
                                        <h3 className="text-[13px] font-black text-ink-900 uppercase tracking-[0.3em] flex items-center gap-4">
                                            <Compass className="w-5 h-5 text-terracotta" strokeWidth={1.5} />
                                            Shodashvarga Matrix
                                        </h3>
                                        <p className="text-[10px] text-ink-400 font-bold uppercase tracking-widest ml-9">Harmonic Divisional Blueprints</p>
                                    </div>
                                </div>
                                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
                                    {Object.entries(profile.divisional_charts || {}).map(([code, chart]: any, idx: number) => (
                                        <motion.div 
                                            key={code} 
                                            initial={{ opacity: 0, y: 20 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            transition={{ delay: 0.1 * idx }}
                                            onClick={() => { setSelectedChart(chart); setSelectedChartTitle(`D${code}`); }} 
                                            className="bg-white dark:bg-zinc-900/40 p-8 rounded-[2rem] border border-ink-900/5 dark:border-white/5 hover:border-classic-gold/40 hover:shadow-2xl transition-all cursor-pointer group shadow-sm transform hover:-translate-y-2 relative overflow-hidden"
                                        >
                                            <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity">
                                                <Star className="w-12 h-12 text-ink-900 dark:text-white" />
                                            </div>
                                            <div className="flex justify-between items-baseline mb-8 border-b border-cream-200 dark:border-white/5 pb-4">
                                                <h5 className="text-[13px] font-black text-ink-900 tracking-wider">D{code} Chart</h5>
                                                <span className="text-[10px] font-bold text-terracotta uppercase tracking-tighter bg-terracotta/5 px-2 py-0.5 rounded">v{code}</span>
                                            </div>
                                            <div className="grid grid-cols-2 gap-3 text-[11px]">
                                                {['ASC', 'Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'].map(p => chart[p] && (
                                                    <div key={p} className="flex justify-between items-center bg-cream-50/50 dark:bg-white/5 px-3 py-2 rounded-xl border border-transparent group-hover:border-cream-200 dark:group-hover:border-white/10 transition-colors">
                                                        <span className="text-ink-500 dark:text-ink-400 font-bold text-[9px] uppercase tracking-tighter">{p === 'ASC' ? 'Lg' : p.slice(0, 2)}</span>
                                                        <span className="text-ink-900 dark:text-white font-black">{chart[p].sign}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </motion.div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}
                    {activeView === 'analysis' && profile && (
                        <div className="p-10 md:p-14 max-w-7xl mx-auto space-y-24">
                            {/* KARMIC NARRATIVE INTRO */}
                            {profile.karmic_story && (
                                <motion.section 
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className="bg-white dark:bg-zinc-900/40 border border-ink-900/10 dark:border-white/5 rounded-[3rem] p-12 md:p-16 shadow-2xl relative overflow-hidden group"
                                >
                                    <div className="absolute top-0 right-0 p-8 opacity-5 group-hover:opacity-10 transition-opacity">
                                        <Star className="w-24 h-24 text-ink-900 dark:text-white" />
                                    </div>
                                    <div className="max-w-4xl space-y-8 relative z-10">
                                        <span className="text-[11px] font-black text-terracotta uppercase tracking-[0.4em] bg-terracotta/5 px-4 py-1.5 rounded-full border border-terracotta/10">Soul Archetype</span>
                                        <h2 className="text-4xl font-black text-ink-900 dark:text-white tracking-tight uppercase italic leading-tight">The Archival Purpose</h2>
                                        <p className="text-xl md:text-2xl text-ink-700 dark:text-ink-400 font-medium leading-relaxed italic">
                                            &ldquo;{profile.karmic_story}&rdquo;
                                        </p>
                                    </div>
                                </motion.section>
                            )}

                            {/* MICRO-TIMING GRID */}
                            {profile.micro_timing && (
                                <section className="space-y-10">
                                    <div className="flex items-center justify-between border-b border-ink-900/10 dark:border-white/5 pb-6">
                                        <div className="space-y-1">
                                            <h3 className="text-[13px] font-black text-ink-900 dark:text-white uppercase tracking-[0.3em] flex items-center gap-4">
                                                <Clock className="w-5 h-5 text-classic-gold" />
                                                Weekly Micro-Timing (Jaimini Padas)
                                            </h3>
                                        </div>
                                    </div>
                                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                                        {Object.entries(profile.micro_timing).map(([p, data]: any, idx: number) => (
                                            <motion.div 
                                                key={p}
                                                initial={{ opacity: 0, scale: 0.9 }}
                                                animate={{ opacity: 1, scale: 1 }}
                                                transition={{ delay: idx * 0.05 }}
                                                className="bg-white dark:bg-zinc-900/40 p-6 rounded-[2rem] border border-ink-900/5 dark:border-white/5 shadow-sm hover:shadow-lg transition-all"
                                            >
                                                <div className="flex justify-between items-baseline mb-4">
                                                    <span className="text-[12px] font-black text-ink-900 dark:text-white uppercase">{p}</span>
                                                    <span className="text-[10px] font-bold text-terracotta uppercase">Pada {data.pada}</span>
                                                </div>
                                                <div className="space-y-2">
                                                    <p className="text-[14px] font-black text-ink-800 dark:text-ink-300">{data.sign} &rarr; {data.nav_sign}</p>
                                                    <p className="text-[10px] text-ink-400 font-bold uppercase tracking-widest">Navamsha Influence</p>
                                                </div>
                                            </motion.div>
                                        ))}
                                    </div>
                                </section>
                            )}
                            
                            {/* DOSHAS & ARUDHAS */}
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-16">
                                <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="space-y-8">
                                    <h3 className="text-[11px] font-black text-terracotta uppercase tracking-[0.4em] px-4 flex items-center gap-3">
                                        <AlertCircle className="w-4 h-4" />
                                        Critical Doshas
                                    </h3>
                                    <div className="bg-white dark:bg-zinc-900/40 border border-ink-900/10 dark:border-white/5 rounded-[2.5rem] p-10 shadow-xl space-y-6">
                                        {profile.doshas?.length > 0 ? (
                                            profile.doshas.map((d: any, idx: number) => (
                                                <div key={idx} className="p-6 bg-terracotta/5 border border-terracotta/10 rounded-2xl space-y-2">
                                                    <div className="flex justify-between items-center">
                                                        <h5 className="font-black text-terracotta uppercase text-sm tracking-widest">{d.name}</h5>
                                                        {d.severity && <Badge color="red">{d.severity}</Badge>}
                                                    </div>
                                                    <p className="text-[12px] text-ink-600 dark:text-ink-400 font-medium italic">
                                                        Active in House {d.house} {d.planets ? `(${d.planets.join(' + ')})` : `(${d.planet})`}
                                                    </p>
                                                    {d.cancellation?.length > 0 && (
                                                        <div className="mt-3 pt-3 border-t border-terracotta/10">
                                                            <p className="text-[10px] font-bold text-emerald-600 uppercase tracking-tighter">Cancellation Active: {d.cancellation.join(', ')}</p>
                                                        </div>
                                                    )}
                                                </div>
                                            ))
                                        ) : (
                                            <div className="text-center py-10 text-ink-400 italic">No major doshas detected in the primary layers.</div>
                                        )}
                                    </div>
                                </motion.div>

                                <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="space-y-8">
                                    <h3 className="text-[11px] font-black text-ink-400 uppercase tracking-[0.4em] px-4 flex items-center gap-3">
                                        <Compass className="w-4 h-4" />
                                        Arudha Matrix (Reflections)
                                    </h3>
                                    <div className="bg-white dark:bg-zinc-900/40 border border-ink-900/10 dark:border-white/5 rounded-[2.5rem] p-10 shadow-xl">
                                        <div className="grid grid-cols-4 gap-4">
                                            {['AL', 'UL', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'A10', 'A11'].map((key) => (
                                                <div key={key} className="text-center py-5 bg-cream-50 dark:bg-white/5 rounded-2xl border border-ink-900/5 transition-all hover:border-classic-gold/30">
                                                    <p className="text-[10px] text-ink-400 font-black uppercase mb-1">{key}</p>
                                                    <p className="text-xl font-black text-ink-900 dark:text-white">H{profile.arudhas?.[key] || "?"}</p>
                                                </div>
                                            ))}
                                        </div>
                                        <div className="mt-8 text-[11px] text-ink-500 italic leading-relaxed text-center px-4">
                                            Arudhas show how the world perceives your houses (AL = Status, UL = Marriage).
                                        </div>
                                    </div>
                                </motion.div>
                            </div>
                            
                            <motion.section 
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="space-y-8"
                            >
                                <div className="flex items-center gap-4 px-2">
                                    <div className="h-px flex-1 bg-ink-900/10 dark:bg-white/10" />
                                    <h3 className="text-[12px] font-black text-ink-400 dark:text-ink-500 uppercase tracking-[0.4em]">Celestial Geometries</h3>
                                    <div className="h-px flex-1 bg-ink-900/10 dark:bg-white/10" />
                                </div>
                                <div className="border border-ink-900/10 dark:border-white/5 rounded-[2.5rem] overflow-hidden bg-white dark:bg-zinc-900/40 shadow-xl">
                                    <table className="w-full text-left text-sm border-collapse">
                                        <thead className="bg-cream-50 dark:bg-white/5 text-ink-400 dark:text-ink-500 uppercase tracking-[0.2em] text-[10px] font-black border-b border-ink-900/10 dark:border-white/5">
                                            <tr>
                                                <th className="p-8">Entity</th>
                                                <th className="p-8">Rashi (H)</th>
                                                <th className="p-8">Bhava (C)</th>
                                                <th className="p-8">Avastha</th>
                                                <th className="p-8">Ishta/Kashta</th>
                                                <th className="p-8">Dignity</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-ink-900/5 dark:divide-white/5">
                                            {['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'].map((p, idx) => {
                                                const pd = profile.planets?.[p];
                                                if (!pd) return null;
                                                const bhava = profile.bhava_chalit?.[p] || pd.house;
                                                const avastha = pd.avasthas?.[0]?.state || "N/A";
                                                const ik = pd.ishta_kashta || { ishta: 0, kashta: 0, ratio: 0.5 };
                                                
                                                return (
                                                    <motion.tr 
                                                        key={p} 
                                                        initial={{ opacity: 0, x: -10 }}
                                                        animate={{ opacity: 1, x: 0 }}
                                                        transition={{ delay: 0.05 * idx }}
                                                        className="hover:bg-cream-50/50 dark:hover:bg-white/5 transition-colors group"
                                                    >
                                                        <td className="p-8 font-black text-ink-900 dark:text-white text-[15px]">{p}</td>
                                                        <td className="p-8 font-black text-ink-600 dark:text-ink-400">H{pd.house}</td>
                                                        <td className="p-8 font-black text-terracotta">H{bhava}</td>
                                                        <td className="p-8 text-[11px] font-bold text-ink-500 uppercase tracking-widest">{avastha}</td>
                                                        <td className="p-8">
                                                            <div className="flex items-center gap-2">
                                                                <span className="text-[10px] font-bold text-emerald-600">I:{ik.ishta.toFixed(0)}</span>
                                                                <span className="text-[10px] font-bold text-terracotta">K:{ik.kashta.toFixed(0)}</span>
                                                            </div>
                                                        </td>
                                                        <td className="p-8">
                                                            <Badge color={pd.dignity === 'Debilitated' ? 'red' : (pd.dignity === 'Exalted' ? 'gold' : 'blue')}>
                                                                {pd.dignity}
                                                            </Badge>
                                                        </td>
                                                    </motion.tr>
                                                );
                                            })}
                                        </tbody>
                                    </table>
                                </div>
                            </motion.section>

                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-16">
                                <motion.div 
                                    initial={{ opacity: 0, scale: 0.95 }}
                                    whileInView={{ opacity: 1, scale: 1 }}
                                    viewport={{ once: true }}
                                    className="space-y-8"
                                >
                                    <h3 className="text-[11px] font-black text-ink-400 uppercase tracking-[0.4em] px-4 flex items-center gap-3">
                                        <div className="w-1.5 h-1.5 rounded-full bg-terracotta" />
                                        Temporal Significators
                                    </h3>
                                    <div className="bg-white dark:bg-zinc-900/40 border border-ink-900/10 dark:border-white/5 rounded-[2rem] overflow-hidden shadow-xl">
                                        <table className="w-full text-left text-xs border-collapse">
                                            <thead className="bg-cream-50 dark:bg-white/5 text-[10px] font-black uppercase tracking-[0.2em] text-ink-400 border-b border-ink-900/10 dark:border-white/5">
                                                <tr>
                                                    <th className="p-6">Significator</th>
                                                    <th className="p-6">Planet</th>
                                                    <th className="p-6">Arc</th>
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-ink-900/5 dark:divide-white/5">
                                                {profile.karakas?.chara?.map((k: any, i: number) => (
                                                    <tr key={i} className="hover:bg-cream-50 dark:hover:bg-white/5 transition-colors">
                                                        <td className="p-6 font-bold text-ink-600 dark:text-ink-400 uppercase tracking-wider">{k.label}</td>
                                                        <td className="p-6 font-black uppercase text-terracotta text-[14px]">{k.planet}</td>
                                                        <td className="p-6 font-bold font-mono text-ink-400">{k.degree}°</td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </motion.div>

                                <motion.div 
                                    initial={{ opacity: 0, scale: 0.95 }}
                                    whileInView={{ opacity: 1, scale: 1 }}
                                    viewport={{ once: true }}
                                    className="space-y-8"
                                >
                                    <h3 className="text-[11px] font-black text-ink-400 uppercase tracking-[0.4em] px-4 flex items-center gap-3">
                                        <div className="w-1.5 h-1.5 rounded-full bg-classic-gold" />
                                        Bhava Strength (Bala)
                                    </h3>
                                    <div className="bg-white dark:bg-zinc-900/40 border border-ink-900/10 dark:border-white/5 rounded-[2rem] p-10 shadow-xl">
                                        <div className="grid grid-cols-3 gap-6">
                                            {Object.entries(profile.bhava_bala || {}).map(([h, data]: any) => (
                                                <div key={h} className="text-center p-6 bg-cream-50 dark:bg-white/5 rounded-[1.5rem] border border-ink-900/5 dark:border-white/5 flex flex-col items-center group hover:bg-white dark:hover:bg-zinc-800 hover:border-classic-gold/20 transition-all hover:shadow-lg">
                                                    <p className="text-[10px] text-ink-400 font-black uppercase mb-2 tracking-widest">H{h}</p>
                                                    <p className="text-2xl font-black text-ink-900 dark:text-white">{data?.rupas ?? "?"}</p>
                                                    <div className="mt-2 px-2 py-0.5 bg-ink-900 dark:bg-white text-white dark:text-ink-900 text-[8px] font-black rounded uppercase tracking-tighter">Rank {data?.rank ?? "?"}</div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </motion.div>
                            </div>

                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-16">
                                <motion.div 
                                    initial={{ opacity: 0, y: 20 }}
                                    whileInView={{ opacity: 1, y: 0 }}
                                    viewport={{ once: true }}
                                    className="space-y-8"
                                >
                                    <h3 className="text-[11px] font-black text-ink-400 uppercase tracking-[0.4em] px-4">Potency Matrix (Shadbala)</h3>
                                    <div className="bg-white dark:bg-zinc-900/40 border border-ink-900/10 dark:border-white/5 rounded-[2.5rem] overflow-hidden shadow-xl">
                                        <table className="w-full text-left text-[11px] border-collapse">
                                            <thead className="bg-cream-50 dark:bg-white/5 font-black uppercase tracking-[0.2em] text-ink-400 border-b border-ink-900/10 dark:border-white/5">
                                                <tr>
                                                    <th className="p-6">Planet</th>
                                                    <th className="p-6 text-right">Actual</th>
                                                    <th className="p-6 text-right">Min</th>
                                                    <th className="p-6 text-center">Ratio</th>
                                                    <th className="p-6">Status</th>
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-ink-900/5 dark:divide-white/5">
                                                {['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'].map(p => { 
                                                    const sd = profile.shadbala_full?.[p]; 
                                                    if (!sd) return null; 
                                                    return (
                                                        <tr key={p} className="hover:bg-cream-50 dark:hover:bg-white/5 transition-colors group">
                                                            <td className="p-6 font-black text-ink-900 dark:text-white">{p}</td>
                                                            <td className="p-6 text-right font-black text-ink-900 dark:text-ink-800">{sd.rupas}</td>
                                                            <td className="p-6 text-right text-ink-400 font-bold">{sd.required}</td>
                                                            <td className="p-6 text-center">
                                                                <span className={`px-2 py-1 rounded-lg font-black ${sd.ratio >= 1.0 ? 'text-emerald-600 bg-emerald-50 dark:bg-emerald-900/20' : 'text-amber-600 bg-amber-50 dark:bg-amber-900/20'}`}>
                                                                    {sd.ratio}
                                                                </span>
                                                            </td>
                                                            <td className="p-6">
                                                                <Badge color={sd.status === 'PASS' ? 'green' : 'red'}>
                                                                    {sd.status === 'PASS' ? 'Optimal' : 'Deficient'}
                                                                </Badge>
                                                            </td>
                                                        </tr>
                                                    ); 
                                                })}
                                            </tbody>
                                        </table>
                                    </div>
                                </motion.div>

                                <motion.div 
                                    initial={{ opacity: 0, y: 20 }}
                                    whileInView={{ opacity: 1, y: 0 }}
                                    viewport={{ once: true }}
                                    className="space-y-8"
                                >
                                    <h3 className="text-[11px] font-black text-ink-400 uppercase tracking-[0.4em] px-4">SAV Energy Resonance</h3>
                                    <div className="bg-white dark:bg-zinc-900/40 p-10 rounded-[2.5rem] border border-ink-900/10 dark:border-white/5 shadow-xl relative overflow-hidden">
                                        <div className="grid grid-cols-4 gap-4">
                                            {Object.entries({ 1: "Ari", 2: "Tau", 3: "Gem", 4: "Can", 5: "Leo", 6: "Vir", 7: "Lib", 8: "Sco", 9: "Sag", 10: "Cap", 11: "Aqu", 12: "Pis" }).map(([num, sign]) => { 
                                                const score = profile.ashtakavarga?.sarvashtakavarga_by_sign?.[num]; 
                                                const lagnaIdx = profile.lagna?.sign_idx ?? 5; 
                                                const houseNum = (Number(num) - 1 - lagnaIdx + 12) % 12 + 1; 
                                                return (
                                                    <div key={num} className="text-center py-6 bg-cream-50 dark:bg-white/5 rounded-2xl border border-ink-900/5 dark:border-white/5 group hover:bg-ink-900 dark:hover:bg-zinc-800 hover:text-white transition-all">
                                                        <p className="text-[10px] text-ink-400 font-black uppercase group-hover:text-ink-300">{sign}</p>
                                                        <p className={`text-2xl font-black my-1 ${score >= 30 ? 'text-emerald-600 group-hover:text-emerald-400' : (score < 25 ? 'text-terracotta group-hover:text-terracotta' : 'text-ink-800 dark:text-white')}`}>{score ?? "?"}</p>
                                                        <p className="text-[9px] text-ink-400 font-black group-hover:text-ink-400">H{houseNum}</p>
                                                    </div>
                                                ); 
                                            })}
                                        </div>
                                        <div className="mt-8 pt-8 border-t border-ink-900/5 dark:border-white/5 italic">
                                            <p className="text-[13px] text-ink-600 dark:text-ink-400 font-medium leading-relaxed">
                                                <span className="text-terracotta font-black mr-3 uppercase tracking-widest text-[10px] bg-terracotta/5 px-2 py-1 rounded-md">Analysis</span>
                                                {profile.ashtakavarga?.interpretation}
                                            </p>
                                        </div>
                                    </div>
                                </motion.div>
                            </div>
                        </div>
                    )}
                    {activeView === 'timeline' && profile && (
                        <div className="p-10 md:p-14 max-w-5xl mx-auto space-y-16">
                            {/* BHRIGU NADI WINDOWS */}
                            {profile.bhrigu_nadi && (
                                <section className="space-y-10">
                                    <div className="flex items-center justify-between border-b border-ink-900/10 dark:border-white/5 pb-6">
                                        <div className="space-y-1">
                                            <h3 className="text-[13px] font-black text-ink-900 dark:text-white uppercase tracking-[0.3em] flex items-center gap-4">
                                                <Compass className="w-5 h-5 text-terracotta" />
                                                Lifecycle Windows (Bhrigu Nadi)
                                            </h3>
                                        </div>
                                    </div>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                        {profile.bhrigu_nadi.career?.map((item: any, idx: number) => (
                                            <motion.div key={idx} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="bg-white dark:bg-zinc-900/40 p-8 rounded-[2.5rem] border-l-4 border-l-classic-gold border border-ink-900/10 dark:border-white/5 shadow-xl relative overflow-hidden">
                                                <div className="flex justify-between items-center mb-4">
                                                    <h5 className="text-[13px] font-black text-ink-900 dark:text-white uppercase tracking-widest">{item.event}</h5>
                                                    <Badge color="gold">Career Peak</Badge>
                                                </div>
                                                <p className="text-2xl font-black text-ink-900 dark:text-ink-300 my-4">{item.window}</p>
                                                <p className="text-[12px] text-ink-600 dark:text-ink-400 font-medium italic leading-relaxed">{item.reason}</p>
                                            </motion.div>
                                        ))}
                                        {profile.bhrigu_nadi.marriage?.map((item: any, idx: number) => (
                                            <motion.div key={idx} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="bg-white dark:bg-zinc-900/40 p-8 rounded-[2.5rem] border-l-4 border-l-terracotta border border-ink-900/10 dark:border-white/5 shadow-xl relative overflow-hidden">
                                                <div className="flex justify-between items-center mb-4">
                                                    <h5 className="text-[13px] font-black text-ink-900 dark:text-white uppercase tracking-widest">{item.event}</h5>
                                                    <Badge color="blue">Partnership</Badge>
                                                </div>
                                                <p className="text-2xl font-black text-ink-900 dark:text-ink-300 my-4">Age {item.approx_age}</p>
                                                <p className="text-[12px] text-ink-600 dark:text-ink-400 font-medium italic leading-relaxed">Trigger: {item.indicator}</p>
                                            </motion.div>
                                        ))}
                                    </div>
                                </section>
                            )}

                            <motion.div 
                                initial={{ opacity: 0, y: -20 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="text-center space-y-4"
                            >
                                <span className="text-[11px] font-black text-classic-gold uppercase tracking-[0.5em] bg-classic-gold/5 px-6 py-2 rounded-full border border-classic-gold/20">Temporal Archival</span>
                                <h2 className="text-5xl font-black text-ink-900 dark:text-white tracking-tighter uppercase italic">Karmic Timeline</h2>
                                <p className="text-ink-400 text-sm font-medium tracking-widest uppercase">The 120-Year Vimshottari Lifecycle</p>
                            </motion.div>

                            <div className="space-y-6">
                                {profile.dasha?.full_timeline?.map((md: any, idx: number) => (
                                    <motion.div 
                                        key={idx}
                                        initial={{ opacity: 0, x: -20 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        transition={{ delay: idx * 0.05 }}
                                        className="bg-white dark:bg-zinc-900/40 border border-ink-900/10 dark:border-white/5 rounded-[2rem] overflow-hidden shadow-sm hover:shadow-xl transition-all group"
                                    >
                                        <div className="p-8 md:p-10 flex flex-col md:flex-row md:items-center justify-between space-y-4 md:space-y-0">
                                            <div className="flex items-center space-x-8">
                                                <div className="w-16 h-16 rounded-2xl bg-cream-50 dark:bg-white/5 flex items-center justify-center border border-ink-900/5 dark:border-white/10 group-hover:scale-110 transition-transform">
                                                    <span className="text-2xl font-black text-terracotta">{md.lord[0]}</span>
                                                </div>
                                                <div>
                                                    <h4 className="text-2xl font-black text-ink-900 dark:text-white uppercase tracking-wider">{md.lord} Mahadasha</h4>
                                                    <p className="text-[11px] text-ink-400 font-bold uppercase tracking-[0.2em] mt-1">{new Date(md.start).getFullYear()} — {new Date(md.end).getFullYear()}</p>
                                                </div>
                                            </div>
                                            <div className="text-right">
                                                <p className="text-[10px] font-black text-ink-400 uppercase tracking-widest mb-1">Window</p>
                                                <p className="text-sm font-bold text-ink-900 dark:text-ink-300 italic">{new Date(md.start).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })} — {new Date(md.end).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })}</p>
                                            </div>
                                        </div>
                                        
                                        <div className="bg-cream-50/50 dark:bg-black/20 border-t border-ink-900/5 dark:border-white/5 p-8 md:p-10">
                                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                                                {md.antardashas?.map((ad: any, aidx: number) => {
                                                    const isCurrent = new Date() >= new Date(ad.start) && new Date() < new Date(ad.end);
                                                    return (
                                                        <div key={aidx} className={`p-5 rounded-2xl border transition-all ${isCurrent ? 'bg-terracotta/10 border-terracotta/30 shadow-md ring-1 ring-terracotta/20' : 'bg-white dark:bg-zinc-800/40 border-ink-900/5 dark:border-white/5'}`}>
                                                            <div className="flex justify-between items-center mb-3">
                                                                <span className="text-[10px] font-black text-ink-400 uppercase tracking-widest">Antardasha</span>
                                                                {isCurrent && <span className="text-[8px] font-black bg-terracotta text-white px-2 py-0.5 rounded-full uppercase animate-pulse">Active</span>}
                                                            </div>
                                                            <div className="flex items-baseline space-x-2">
                                                                <span className="text-[15px] font-black text-ink-900 dark:text-white uppercase">{ad.lord}</span>
                                                                <span className="text-[9px] text-ink-400 font-bold italic">Until {new Date(ad.end).toLocaleDateString('en-GB', { month: 'short', year: 'numeric' })}</span>
                                                            </div>
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        </div>
                                    </motion.div>
                                ))}
                            </div>
                        </div>
                    )}
                    {activeView === 'events' && (
                        <div className="p-10 md:p-14 max-w-5xl mx-auto space-y-16">
                            <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="text-center space-y-4">
                                <span className="text-[11px] font-black text-classic-gold uppercase tracking-[0.5em] bg-classic-gold/5 px-6 py-2 rounded-full border border-classic-gold/20">ML Feedback Engine</span>
                                <h2 className="text-5xl font-black text-ink-900 dark:text-white tracking-tighter uppercase italic">Life Events</h2>
                                <p className="text-ink-400 text-sm font-medium tracking-widest uppercase">Log Your Story — The System Learns From It</p>
                            </motion.div>

                            {/* EVENT FORM */}
                            <motion.section initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="bg-white dark:bg-zinc-900/40 border border-ink-900/10 dark:border-white/5 rounded-[3rem] p-12 shadow-xl space-y-10">
                                <div className="flex items-center gap-4">
                                    <TrendingUp className="w-6 h-6 text-classic-gold" />
                                    <h3 className="text-xl font-black text-ink-900 dark:text-white uppercase tracking-widest">Log a Life Event</h3>
                                </div>
                                <p className="text-sm text-ink-500 italic">Every event you log trains the empirical feedback engine — Guruji will reference real patterns from your life, not just theory.</p>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                    <div className="space-y-3">
                                        <label className="text-[9px] font-black text-ink-500 uppercase tracking-widest">Date</label>
                                        <input type="date" className="w-full bg-cream-50 dark:bg-black/20 border border-ink-900/10 dark:border-white/5 p-4 rounded-xl text-ink-900 dark:text-white font-bold focus:outline-none focus:border-terracotta/40" value={eventForm.date} onChange={e => setEventForm({...eventForm, date: e.target.value})} />
                                    </div>
                                    <div className="space-y-3">
                                        <label className="text-[9px] font-black text-ink-500 uppercase tracking-widest">Domain</label>
                                        <select className="w-full bg-cream-50 dark:bg-black/20 border border-ink-900/10 dark:border-white/5 p-4 rounded-xl text-ink-900 dark:text-white font-bold focus:outline-none focus:border-terracotta/40" value={eventForm.domain} onChange={e => setEventForm({...eventForm, domain: e.target.value})}>
                                            {['career', 'finance', 'relationship', 'health', 'spiritual', 'family', 'travel', 'general'].map(d => <option key={d} value={d}>{d.charAt(0).toUpperCase() + d.slice(1)}</option>)}
                                        </select>
                                    </div>
                                </div>

                                <div className="space-y-3">
                                    <label className="text-[9px] font-black text-ink-500 uppercase tracking-widest">Event Title</label>
                                    <input type="text" placeholder="e.g. Got promoted to Senior Engineer" className="w-full bg-cream-50 dark:bg-black/20 border border-ink-900/10 dark:border-white/5 p-4 rounded-xl text-ink-900 dark:text-white font-bold focus:outline-none focus:border-terracotta/40" value={eventForm.title} onChange={e => setEventForm({...eventForm, title: e.target.value})} />
                                </div>

                                <div className="space-y-3">
                                    <label className="text-[9px] font-black text-ink-500 uppercase tracking-widest">Description</label>
                                    <textarea rows={3} placeholder="Describe what happened and the context..." className="w-full bg-cream-50 dark:bg-black/20 border border-ink-900/10 dark:border-white/5 p-4 rounded-xl text-ink-900 dark:text-white font-medium focus:outline-none focus:border-terracotta/40 resize-none" value={eventForm.description} onChange={e => setEventForm({...eventForm, description: e.target.value})} />
                                </div>

                                <div className="space-y-3">
                                    <label className="text-[9px] font-black text-ink-500 uppercase tracking-widest">Outcome / Result</label>
                                    <input type="text" placeholder="e.g. Got a 40% raise, moved to a new city" className="w-full bg-cream-50 dark:bg-black/20 border border-ink-900/10 dark:border-white/5 p-4 rounded-xl text-ink-900 dark:text-white font-medium focus:outline-none focus:border-terracotta/40" value={eventForm.outcome} onChange={e => setEventForm({...eventForm, outcome: e.target.value})} />
                                </div>

                                <div className="space-y-4">
                                    <div className="flex items-center justify-between">
                                        <label className="text-[9px] font-black text-ink-500 uppercase tracking-widest">Emotional Impact</label>
                                        <span className={`text-[13px] font-black px-4 py-1 rounded-full ${
                                            eventForm.emotion_score > 2 ? 'bg-emerald-100 text-emerald-700' :
                                            eventForm.emotion_score > 0 ? 'bg-green-50 text-green-600' :
                                            eventForm.emotion_score < -2 ? 'bg-red-100 text-terracotta' :
                                            eventForm.emotion_score < 0 ? 'bg-orange-50 text-orange-600' :
                                            'bg-cream-100 text-ink-500'
                                        }`}>
                                            {eventForm.emotion_score > 2 ? '✦ Very Positive' : eventForm.emotion_score > 0 ? '↑ Positive' : eventForm.emotion_score < -2 ? '✗ Very Negative' : eventForm.emotion_score < 0 ? '↓ Difficult' : '— Neutral'}
                                        </span>
                                    </div>
                                    <input type="range" min="-5" max="5" step="1" className="w-full h-2 rounded-full accent-terracotta cursor-pointer" value={eventForm.emotion_score} onChange={e => setEventForm({...eventForm, emotion_score: parseInt(e.target.value)})} />
                                    <div className="flex justify-between text-[9px] text-ink-400 font-bold uppercase">
                                        <span>Very Difficult (-5)</span><span>Neutral (0)</span><span>Very Positive (+5)</span>
                                    </div>
                                </div>

                                <button onClick={logEvent} disabled={eventsLoading || !eventForm.title} className="w-full py-5 bg-ink-900 dark:bg-terracotta text-white rounded-2xl font-black uppercase tracking-[0.2em] text-[12px] hover:bg-terracotta transition-all shadow-lg active:scale-[0.98] disabled:opacity-50">
                                    {eventsLoading ? 'Logging...' : 'Log Event & Train the System'}
                                </button>
                            </motion.section>

                            {/* EVENT HISTORY */}
                            {events.length > 0 && (
                                <section className="space-y-8">
                                    <h3 className="text-[13px] font-black text-ink-900 dark:text-white uppercase tracking-[0.3em] flex items-center gap-4">
                                        <Heart className="w-5 h-5 text-terracotta" />
                                        Logged Events ({events.length})
                                    </h3>
                                    <div className="space-y-4">
                                        {events.map((ev: any, idx: number) => (
                                            <motion.div key={ev.id} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: idx * 0.04 }}
                                                className={`bg-white dark:bg-zinc-900/40 p-8 rounded-[2rem] border-l-4 border border-ink-900/5 dark:border-white/5 shadow-sm ${
                                                    ev.emotion_score > 2 ? 'border-l-emerald-500' : ev.emotion_score < -2 ? 'border-l-terracotta' : 'border-l-classic-gold'
                                                }`}>
                                                <div className="flex justify-between items-start">
                                                    <div>
                                                        <div className="flex items-center gap-3 mb-2">
                                                            <span className="text-[9px] font-black text-ink-400 uppercase tracking-widest bg-cream-100 dark:bg-white/10 px-2 py-1 rounded">{ev.domain}</span>
                                                            <span className="text-[10px] text-ink-400">{ev.date}</span>
                                                        </div>
                                                        <h4 className="text-[16px] font-black text-ink-900 dark:text-white">{ev.title}</h4>
                                                        {ev.description && <p className="text-[13px] text-ink-600 dark:text-ink-400 mt-2 font-medium">{ev.description}</p>}
                                                        {ev.dasha && <p className="text-[10px] text-ink-400 mt-3 italic">Dasha: {ev.dasha.slice(0, 80)}...</p>}
                                                    </div>
                                                    <span className={`text-[20px] font-black ml-4 ${ ev.emotion_score > 0 ? 'text-emerald-500' : ev.emotion_score < 0 ? 'text-terracotta' : 'text-ink-300' }`}>
                                                        {ev.emotion_score > 0 ? `+${ev.emotion_score}` : ev.emotion_score}
                                                    </span>
                                                </div>
                                            </motion.div>
                                        ))}
                                    </div>
                                </section>
                            )}
                            {events.length === 0 && (
                                <div className="text-center py-20 text-ink-400">
                                    <Calendar className="w-16 h-16 mx-auto mb-6 opacity-20" />
                                    <p className="font-bold uppercase tracking-widest text-[12px]">No events logged yet</p>
                                    <p className="text-[13px] mt-2 italic">Start logging life events to enable the ML feedback engine</p>
                                </div>
                            )}
                        </div>
                    )}
                    {activeView === 'predictions' && (
                        <div className="p-10 md:p-14 max-w-5xl mx-auto space-y-16">
                            <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="text-center space-y-4">
                                <span className="text-[11px] font-black text-emerald-600 uppercase tracking-[0.5em] bg-emerald-600/5 px-6 py-2 rounded-full border border-emerald-600/20">Prediction Ledger</span>
                                <h2 className="text-5xl font-black text-ink-900 dark:text-white tracking-tighter uppercase italic">Accuracy</h2>
                                <p className="text-ink-400 text-sm font-medium tracking-widest uppercase">Verify outcomes — the system learns from hits & misses</p>
                            </motion.div>

                            {accuracy && (
                                <motion.section initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="bg-white dark:bg-zinc-900/40 border border-ink-900/10 dark:border-white/5 rounded-[3rem] p-12 shadow-xl">
                                    <div className="flex flex-wrap items-center justify-between gap-6">
                                        <div>
                                            <p className="text-[9px] font-black text-ink-400 uppercase tracking-widest mb-2">Grade</p>
                                            <p className="text-2xl font-black text-terracotta">{accuracy.grade}</p>
                                        </div>
                                        {accuracy.hit_rate_pct != null && (
                                            <div className="text-center">
                                                <p className="text-[9px] font-black text-ink-400 uppercase tracking-widest mb-2">Hit Rate</p>
                                                <p className="text-4xl font-black text-emerald-600">{accuracy.hit_rate_pct}%</p>
                                                <p className="text-[10px] text-ink-400 mt-1">{accuracy.hit_count} hits / {accuracy.miss_count} misses</p>
                                            </div>
                                        )}
                                        <div className="text-right">
                                            <p className="text-[9px] font-black text-ink-400 uppercase tracking-widest mb-2">Pending</p>
                                            <p className="text-3xl font-black text-ink-900 dark:text-white">{accuracy.pending_count}</p>
                                        </div>
                                    </div>
                                    {accuracy.recommendation && (
                                        <p className="mt-8 text-sm text-ink-500 italic border-t border-ink-900/5 pt-6">{accuracy.recommendation}</p>
                                    )}
                                </motion.section>
                            )}

                            <section className="space-y-6">
                                <h3 className="text-[13px] font-black text-ink-900 dark:text-white uppercase tracking-[0.3em] flex items-center gap-4">
                                    <Target className="w-5 h-5 text-classic-gold" />
                                    All Predictions ({predictions.length})
                                </h3>
                                {predictions.length === 0 ? (
                                    <div className="text-center py-20 text-ink-400">
                                        <Target className="w-16 h-16 mx-auto mb-6 opacity-20" />
                                        <p className="font-bold uppercase tracking-widest text-[12px]">No predictions yet</p>
                                        <p className="text-[13px] mt-2 italic">Ask timing questions in Consultation — predictions auto-log here</p>
                                    </div>
                                ) : (
                                    <div className="space-y-4">
                                        {predictions.map((p: any, idx: number) => (
                                            <motion.div key={p.id} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: idx * 0.03 }}
                                                className={`bg-white dark:bg-zinc-900/40 p-8 rounded-[2rem] border border-ink-900/5 dark:border-white/5 shadow-sm border-l-4 ${
                                                    p.status === 'hit' ? 'border-l-emerald-500' : p.status === 'miss' ? 'border-l-terracotta' : 'border-l-classic-gold'
                                                }`}>
                                                <div className="flex flex-col md:flex-row md:justify-between gap-6">
                                                    <div className="flex-1">
                                                        <div className="flex flex-wrap items-center gap-3 mb-3">
                                                            <Badge color={p.status === 'hit' ? 'green' : p.status === 'miss' ? 'red' : 'gold'}>{p.status}</Badge>
                                                            <Badge>{p.topic}</Badge>
                                                            <span className="text-[10px] text-ink-400">conf {p.confidence}%</span>
                                                            <span className="text-[10px] text-ink-400">{p.window_start} → {p.window_end}</span>
                                                        </div>
                                                        <p className="text-[14px] font-bold text-ink-900 dark:text-white">{p.prediction_text}</p>
                                                        {p.question && <p className="text-[12px] text-ink-500 mt-2 italic">Q: {p.question.slice(0, 120)}</p>}
                                                        {p.outcome && <p className="text-[12px] text-ink-600 mt-2">Outcome: {p.outcome}</p>}
                                                    </div>
                                                    {p.status === 'pending' && (
                                                        <div className="flex gap-3 shrink-0">
                                                            <button onClick={() => verifyPrediction(p.id, true)} disabled={predictionsLoading}
                                                                className="px-6 py-3 bg-emerald-600 text-white rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-emerald-700 disabled:opacity-50">
                                                                Yes — Happened
                                                            </button>
                                                            <button onClick={() => verifyPrediction(p.id, false)} disabled={predictionsLoading}
                                                                className="px-6 py-3 bg-ink-900/10 text-ink-700 rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-terracotta/10 disabled:opacity-50">
                                                                No — Miss
                                                            </button>
                                                        </div>
                                                    )}
                                                </div>
                                            </motion.div>
                                        ))}
                                    </div>
                                )}
                            </section>
                        </div>
                    )}
                    {activeView === 'knowledge' && (
                        <div className="p-10 md:p-14 max-w-5xl mx-auto space-y-16">
                            <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="text-center space-y-4">
                                <span className="text-[11px] font-black text-deep-navy uppercase tracking-[0.5em] bg-deep-navy/5 px-6 py-2 rounded-full border border-deep-navy/20">RAG Knowledge Base</span>
                                <h2 className="text-5xl font-black text-ink-900 dark:text-white tracking-tighter uppercase italic">Learn from YouTube</h2>
                                <p className="text-ink-400 text-sm font-medium tracking-widest uppercase">Hindi · English · Hinglish captions → Guruji&apos;s memory</p>
                            </motion.div>

                            {knowledgeStats && (
                                <motion.section initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="grid grid-cols-3 gap-6">
                                    <div className="bg-white dark:bg-zinc-900/40 p-8 rounded-2xl border border-ink-900/5 text-center">
                                        <p className="text-[9px] font-black text-ink-400 uppercase tracking-widest">Total Chunks</p>
                                        <p className="text-3xl font-black text-ink-900 dark:text-white mt-2">{knowledgeStats.total_chunks?.toLocaleString() ?? 0}</p>
                                    </div>
                                    <div className="bg-white dark:bg-zinc-900/40 p-8 rounded-2xl border border-ink-900/5 text-center">
                                        <p className="text-[9px] font-black text-ink-400 uppercase tracking-widest">Sources</p>
                                        <p className="text-3xl font-black text-terracotta mt-2">{knowledgeStats.source_count ?? 0}</p>
                                    </div>
                                    <div className="bg-white dark:bg-zinc-900/40 p-8 rounded-2xl border border-ink-900/5 text-center">
                                        <p className="text-[9px] font-black text-ink-400 uppercase tracking-widest">YouTube Videos</p>
                                        <p className="text-3xl font-black text-classic-gold mt-2">{knowledgeStats.youtube_videos ?? 0}</p>
                                    </div>
                                </motion.section>
                            )}

                            <motion.section initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="bg-white dark:bg-zinc-900/40 border border-ink-900/10 dark:border-white/5 rounded-[3rem] p-12 shadow-xl space-y-8">
                                <div className="flex items-center gap-4">
                                    <BookOpen className="w-6 h-6 text-classic-gold" />
                                    <h3 className="text-xl font-black text-ink-900 dark:text-white uppercase tracking-widest">Paste Links</h3>
                                </div>
                                <p className="text-sm text-ink-500 italic">
                                    One video or full playlist per line. Uses YouTube captions (auto or manual).
                                    Hindi is translated for search; Hinglish is kept bilingual. Requires Ollama running with <code className="text-terracotta">nomic-embed-text</code>.
                                </p>
                                <textarea
                                    rows={6}
                                    placeholder={"https://www.youtube.com/watch?v=...\nhttps://www.youtube.com/playlist?list=..."}
                                    className="w-full bg-cream-50 dark:bg-black/20 border border-ink-900/10 dark:border-white/5 p-6 rounded-2xl text-ink-900 dark:text-white font-mono text-sm focus:outline-none focus:border-terracotta/40 resize-none"
                                    value={youtubeUrls}
                                    onChange={e => setYoutubeUrls(e.target.value)}
                                />
                                <button onClick={ingestYoutube} disabled={knowledgeLoading || !youtubeUrls.trim()}
                                    className="w-full py-5 bg-ink-900 dark:bg-terracotta text-white rounded-2xl font-black uppercase tracking-[0.2em] text-[12px] hover:bg-terracotta transition-all shadow-lg active:scale-[0.98] disabled:opacity-50">
                                    {knowledgeLoading ? 'Fetching captions & indexing...' : 'Ingest & Learn'}
                                </button>
                            </motion.section>

                            {ingestResult?.results && (
                                <section className="space-y-4">
                                    <h3 className="text-[13px] font-black uppercase tracking-widest text-ink-900 dark:text-white">Last ingest</h3>
                                    {ingestResult.results.map((r: any, i: number) => (
                                        <div key={i} className={`p-6 rounded-2xl border text-sm ${r.status === 'success' ? 'bg-emerald-50 border-emerald-200' : r.status === 'skipped' ? 'bg-cream-100 border-ink-900/10' : 'bg-red-50 border-terracotta/20'}`}>
                                            <span className="font-black">{r.title || r.video_id}</span>
                                            <span className="text-ink-500 ml-3">{r.status} — {r.chunks ?? 0} chunks {r.lang ? `(${r.lang})` : ''}</span>
                                            {r.reason && r.status === 'failed' && <p className="text-ink-500 mt-2 text-xs">{r.reason}</p>}
                                        </div>
                                    ))}
                                </section>
                            )}
                        </div>
                    )}
                    {activeView === 'profile' && profile && (
                        <div className="p-10 md:p-14 max-w-5xl mx-auto space-y-16">
                            <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="text-center space-y-4">
                                <span className="text-[11px] font-black text-terracotta uppercase tracking-[0.5em] bg-terracotta/5 px-6 py-2 rounded-full border border-terracotta/20">Archival Manifest</span>
                                <h2 className="text-5xl font-black text-ink-900 dark:text-white tracking-tighter uppercase italic">User Profile</h2>
                                <p className="text-ink-400 text-sm font-medium tracking-widest uppercase">Qualitative Context & Lived Experience</p>
                            </motion.div>

                            <div className="grid grid-cols-1 gap-12">
                                {/* BIRTH DATA MANAGEMENT */}
                                {editBirth && (
                                <motion.section initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="bg-white dark:bg-zinc-900/40 border border-ink-900/10 dark:border-white/5 rounded-[3rem] p-12 shadow-xl space-y-10">
                                    <div className="flex items-center gap-4">
                                        <Compass className="w-6 h-6 text-classic-gold" />
                                        <h3 className="text-xl font-black text-ink-900 dark:text-white uppercase tracking-widest">Birth Coordinates</h3>
                                    </div>
                                    <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-6">
                                        {[
                                            { label: 'Day', key: 'day' },
                                            { label: 'Month', key: 'month' },
                                            { label: 'Year', key: 'year' },
                                            { label: 'Hour', key: 'hour' },
                                            { label: 'Minute', key: 'minute' },
                                        ].map((f) => (
                                            <div key={f.key} className="space-y-3">
                                                <label className="text-[9px] font-black text-ink-500 uppercase tracking-widest block text-center">{f.label}</label>
                                                <input 
                                                    type="number" 
                                                    className="w-full bg-cream-50 dark:bg-black/20 border border-ink-900/10 dark:border-white/5 p-4 rounded-xl text-center text-ink-900 dark:text-white font-black focus:outline-none focus:border-terracotta/40"
                                                    value={editBirth[f.key] || ""}
                                                    onChange={(e) => setEditBirth({...editBirth, [f.key]: parseInt(e.target.value)})}
                                                />
                                            </div>
                                        ))}
                                    </div>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                        <div className="space-y-3">
                                            <label className="text-[9px] font-black text-ink-500 uppercase tracking-widest">City of Origin</label>
                                            <input type="text" className="w-full bg-cream-50 dark:bg-black/20 border border-ink-900/10 dark:border-white/5 p-4 rounded-xl text-ink-900 dark:text-white font-bold focus:outline-none focus:border-terracotta/40" value={editBirth.city || ""} onChange={(e) => setEditBirth({...editBirth, city: e.target.value})} />
                                        </div>
                                        <div className="space-y-3">
                                            <label className="text-[9px] font-black text-ink-500 uppercase tracking-widest">Nation Code</label>
                                            <input type="text" className="w-full bg-cream-50 dark:bg-black/20 border border-ink-900/10 dark:border-white/5 p-4 rounded-xl text-ink-900 dark:text-white font-bold focus:outline-none focus:border-terracotta/40" value={editBirth.nation || ""} onChange={(e) => setEditBirth({...editBirth, nation: e.target.value})} />
                                        </div>
                                    </div>
                                    <button 
                                        onClick={async () => {
                                            const res = await fetch(`${API_BASE}/users`, {
                                                method: 'POST',
                                                headers: { 'Content-Type': 'application/json' },
                                                body: JSON.stringify(editBirth)
                                            });
                                            if (res.ok) {
                                                showToast('Archive updated and recalibrated!');
                                                fetchProfile(activeUser!);
                                            } else {
                                                showToast('Failed to update archive.', 'error');
                                            }
                                        }}
                                        className="w-full py-5 border-2 border-ink-900 dark:border-terracotta text-ink-900 dark:text-terracotta rounded-2xl font-black uppercase tracking-[0.2em] text-[12px] hover:bg-ink-900 hover:text-white dark:hover:bg-terracotta dark:hover:text-white transition-all active:scale-[0.98]"
                                    >
                                        Re-Archive & Recalculate
                                    </button>
                                </motion.section>
                                )}

                                {/* SOUL STORY SECTION */}
                                <motion.section initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} className="bg-white dark:bg-zinc-900/40 border border-ink-900/10 dark:border-white/5 rounded-[3rem] p-12 shadow-xl space-y-8">
                                    <div className="flex items-center gap-4">
                                        <BookOpen className="w-6 h-6 text-terracotta" />
                                        <h3 className="text-xl font-black text-ink-900 dark:text-white uppercase tracking-widest">Your Soul Narrative</h3>
                                    </div>
                                    <p className="text-sm text-ink-600 dark:text-ink-400 leading-relaxed italic">
                                        Write your story here. Mention your work, what's feeling stuck, and your ambitions. 
                                        The system will "read" this narrative to understand your current karmic chapter.
                                    </p>
                                    <textarea 
                                        className="w-full h-64 bg-cream-50 dark:bg-black/20 border border-ink-900/10 dark:border-white/5 p-8 rounded-[2rem] text-ink-900 dark:text-white text-[16px] font-medium placeholder-ink-300 focus:outline-none focus:border-terracotta/40 transition-all resize-none shadow-inner"
                                        placeholder="I am currently working as a software engineer..."
                                        value={userStory}
                                        onChange={(e) => setUserStory(e.target.value)}
                                    ></textarea>
                                    <button 
                                        onClick={async () => {
                                            if (!userStory) return;
                                            const res = await fetch(`${API_BASE}/users/${activeUser}/story`, {
                                                method: 'POST',
                                                headers: { 'Content-Type': 'application/json' },
                                                body: JSON.stringify({ story: userStory })
                                            });
                                            if (res.ok) {
                                                showToast('Story synthesized! Guruji now knows your context.');
                                                fetchProfile(activeUser!);
                                                setUserStory("");
                                            } else {
                                                showToast('Failed to process story.', 'error');
                                            }
                                        }}
                                        className="w-full py-5 bg-ink-900 dark:bg-terracotta text-white rounded-2xl font-black uppercase tracking-[0.2em] text-[12px] hover:bg-terracotta transition-all shadow-lg active:scale-[0.98]"
                                    >
                                        Synthesize Narrative
                                    </button>
                                </motion.section>

                                {/* STRUCTURED DATA SECTION */}
                                <motion.section initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.1 }} className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                    {[
                                        { label: 'Profession', key: 'profession', icon: Zap },
                                        { label: 'Current Struggles', key: 'struggles', icon: Shield },
                                        { label: 'Goals & Ambitions', key: 'goals', icon: Star },
                                        { label: 'Recent Life Events', key: 'life_events', icon: Clock },
                                    ].map((f) => (
                                        <div key={f.key} className="bg-white dark:bg-zinc-900/40 border border-ink-900/10 dark:border-white/5 rounded-[2.5rem] p-8 space-y-4 shadow-sm group hover:border-classic-gold/30 transition-colors">
                                            <div className="flex items-center gap-3">
                                                <f.icon className="w-4 h-4 text-classic-gold" />
                                                <label className="text-[10px] font-black text-ink-500 uppercase tracking-widest">{f.label}</label>
                                            </div>
                                            <input 
                                                type="text" 
                                                className="w-full bg-transparent border-b border-ink-900/5 dark:border-white/5 pb-2 text-[15px] font-bold text-ink-900 dark:text-white focus:outline-none focus:border-terracotta transition-colors"
                                                value={profile.lived_experience?.[f.key] || ""}
                                                onChange={async (e) => {
                                                    const newVal = e.target.value;
                                                    setProfile((prev: any) => ({
                                                        ...prev,
                                                        lived_experience: {
                                                            ...prev.lived_experience,
                                                            [f.key]: newVal
                                                        }
                                                    }));
                                                }}
                                                onBlur={async (e) => {
                                                    await fetch(`${API_BASE}/users/${activeUser}/experience`, {
                                                        method: 'POST',
                                                        headers: { 'Content-Type': 'application/json' },
                                                        body: JSON.stringify({ [f.key]: e.target.value })
                                                    });
                                                }}
                                            />
                                        </div>
                                    ))}
                                </motion.section>
                            </div>
                        </div>
                    )}
                    {activeView === 'remedies' && profile && (
                        <div className="p-10 md:p-20 max-w-6xl mx-auto space-y-20">
                            <motion.div 
                                initial={{ opacity: 0, y: -20 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="text-center space-y-6"
                            >
                                <span className="text-[11px] font-black text-classic-gold uppercase tracking-[0.5em] bg-classic-gold/5 px-6 py-2 rounded-full border border-classic-gold/20">Harmonic Alignment</span>
                                <h2 className="text-5xl font-black text-ink-900 tracking-tighter uppercase italic">Karmic Balancers</h2>
                                <p className="text-ink-400 text-sm font-medium tracking-widest uppercase">Temporal Prescriptions for Archival Equilibrium</p>
                            </motion.div>
                            
                            <div className="grid grid-cols-1 gap-12">
                                {profile.remedies?.map((rem: any, idx: number) => (
                                    <motion.div 
                                        key={idx} 
                                        initial={{ opacity: 0, y: 30 }}
                                        whileInView={{ opacity: 1, y: 0 }}
                                        viewport={{ once: true }}
                                        transition={{ delay: idx * 0.1 }}
                                        className="bg-white border border-ink-900/10 rounded-[3rem] p-12 flex flex-col md:flex-row md:items-center space-y-10 md:space-y-0 md:space-x-16 hover:shadow-2xl transition-all group relative overflow-hidden"
                                    >
                                        <div className="absolute top-0 left-0 w-2 h-full bg-ink-900/5 group-hover:bg-terracotta/20 transition-colors" />
                                        <div className="w-28 h-28 rounded-full bg-cream-50 flex items-center justify-center shrink-0 border border-ink-900/5 shadow-inner group-hover:scale-110 transition-transform duration-500">
                                            <span className="text-4xl font-black text-ink-900 group-hover:text-terracotta transition-colors">{rem.planet[0]}</span>
                                        </div>
                                        <div className="flex-1 space-y-10">
                                            <div className="flex items-center justify-between border-b border-ink-900/5 pb-6">
                                                <div className="flex items-center space-x-6">
                                                    <h4 className="text-2xl font-black text-ink-900 uppercase tracking-widest">{rem.planet}</h4>
                                                    <Badge color={rem.planet === "General" ? "green" : "gold"}>{rem.reason}</Badge>
                                                </div>
                                            </div>
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
                                                <div className="space-y-4">
                                                    <p className="text-[10px] font-black text-ink-400 uppercase tracking-[0.3em]">Vibration (Mantra)</p>
                                                    <p className="text-[17px] font-black text-terracotta italic leading-relaxed">&quot;{rem.mantra}&quot;</p>
                                                </div>
                                                <div className="space-y-4">
                                                    <p className="text-[10px] font-black text-ink-400 uppercase tracking-[0.3em]">Action (Ritual)</p>
                                                    <p className="text-[15px] text-ink-800 font-bold leading-relaxed">{rem.charity}</p>
                                                </div>
                                            </div>
                                            <div className="pt-4 flex items-center gap-4 text-[11px] font-black text-ink-500 uppercase tracking-[0.2em]">
                                                <span className="opacity-40">Mineral Resonance:</span>
                                                <span className="text-ink-900 px-3 py-1 bg-cream-50 rounded-lg">{rem.gemstone}</span>
                                            </div>
                                        </div>
                                    </motion.div>
                                ))}
                            </div>
                        </div>
                    )}
                </motion.div>
            </AnimatePresence>
        </div>
      </div>

      <AnimatePresence>{selectedChart && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-[110] bg-ink-900/40 dark:bg-black/60 backdrop-blur-xl flex items-center justify-center p-6" onClick={() => setSelectedChart(null)}><motion.div initial={{ scale: 0.95, opacity: 0, y: 20 }} animate={{ scale: 1, opacity: 1, y: 0 }} exit={{ scale: 0.95, opacity: 0, y: 20 }} transition={{ type: 'spring', damping: 25, stiffness: 300 }} className="bg-cream-50 dark:bg-zinc-900 border border-ink-900/10 dark:border-white/10 p-14 rounded-3xl relative shadow-2xl w-full max-w-[550px] flex flex-col items-center paper-texture" onClick={e => e.stopPropagation()}><button onClick={() => setSelectedChart(null)} className="absolute top-6 right-6 text-ink-400 hover:text-ink-900 dark:hover:text-white transition-colors bg-white dark:bg-zinc-800 p-2 rounded-full border border-ink-900/10 dark:border-white/10 shadow-sm"><X className="w-5 h-5" /></button><NorthIndianChart chartData={selectedChart} title={`${selectedChartTitle} Blueprint`} /></motion.div></motion.div>
          )}</AnimatePresence>

      <AnimatePresence>{showProfileModal && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-[100] bg-ink-900/40 dark:bg-black/60 backdrop-blur-md flex items-center justify-center p-6">
              <motion.div initial={{ scale: 0.95, opacity: 0, y: 20 }} animate={{ scale: 1, opacity: 1, y: 0 }} exit={{ scale: 0.95, opacity: 0, y: 20 }} className="bg-cream-50 dark:bg-zinc-900 w-full max-w-3xl p-16 border border-ink-900/10 dark:border-white/10 rounded-[2rem] relative shadow-2xl paper-texture"><button onClick={() => setShowProfileModal(false)} className="absolute top-8 right-8 text-ink-400 hover:text-ink-900 dark:hover:text-white transition-colors bg-white dark:bg-zinc-800 p-2 border border-ink-900/10 dark:border-white/10 rounded-full shadow-sm"><X className="w-6 h-6" /></button>
                <div className="mb-14 text-center border-b border-ink-900/10 dark:border-white/10 pb-8"><h3 className="text-3xl font-black text-ink-900 dark:text-white tracking-widest uppercase italic">New Enrollment</h3><p className="text-ink-500 dark:text-ink-400 text-[14px] mt-4 font-medium max-w-lg mx-auto italic">Provide coordinates for temporal archivation.</p></div>
                <form onSubmit={async (e) => { e.preventDefault(); const submissionData = { ...formData, year: Number(formData.year), month: Number(formData.month), day: Number(formData.day), hour: Number(formData.hour), minute: Number(formData.minute) }; const res = await fetch(`${API_BASE}/users`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(submissionData) }); if (res.ok) { setShowProfileModal(false); fetchUsers(); showToast('Profile created successfully.'); } else { showToast('Failed to create profile.', 'error'); } }} className="space-y-10">
                  <div className="space-y-3"><label className="text-[10px] font-black text-ink-500 dark:text-ink-400 uppercase tracking-widest px-1">Identity</label><input type="text" placeholder="Subject Name" className="w-full bg-white dark:bg-zinc-800 border border-ink-900/10 dark:border-white/10 p-5 rounded-2xl text-ink-900 dark:text-white text-[15px] font-bold outline-none focus:border-terracotta dark:focus:border-terracotta transition-all shadow-sm placeholder-ink-300 dark:placeholder-zinc-600" required value={formData.name} onChange={e=>setFormData({...formData, name: e.target.value})} /></div>
                  <div className="grid grid-cols-2 gap-8"><div className="space-y-3"><label className="text-[10px] font-black text-ink-500 dark:text-ink-400 uppercase tracking-widest px-1">Origin (City)</label><input type="text" placeholder="Birth City" className="w-full bg-white dark:bg-zinc-800 border border-ink-900/10 dark:border-white/10 p-5 rounded-2xl text-ink-900 dark:text-white text-[15px] font-bold outline-none focus:border-terracotta dark:focus:border-terracotta transition-all shadow-sm placeholder-ink-300 dark:placeholder-zinc-600" required value={formData.city} onChange={e=>setFormData({...formData, city: e.target.value})} /></div><div className="space-y-3"><label className="text-[10px] font-black text-ink-500 dark:text-ink-400 uppercase tracking-widest px-1">Region Code</label><input type="text" placeholder="IN" className="w-full bg-white dark:bg-zinc-800 border border-ink-900/10 dark:border-white/10 p-5 rounded-2xl text-ink-900 dark:text-white text-[15px] font-bold outline-none focus:border-terracotta dark:focus:border-terracotta transition-all shadow-sm placeholder-ink-300 dark:placeholder-zinc-600" required value={formData.nation} onChange={e=>setFormData({...formData, nation: e.target.value})} /></div></div>
                  <div className="grid grid-cols-5 gap-4">{[{ l: 'DD', k: 'day' }, { l: 'MM', k: 'month' }, { l: 'YYYY', k: 'year' }, { l: 'HH', k: 'hour' }, { l: 'Min', k: 'minute' }].map(f => (<div key={f.k} className="space-y-3 col-span-1"><label className="text-[9px] font-black text-ink-500 dark:text-ink-400 uppercase tracking-widest text-center block">{f.l}</label><input type="number" placeholder={f.l} className="w-full bg-white dark:bg-zinc-800 border border-ink-900/10 dark:border-white/10 p-5 rounded-2xl text-ink-900 dark:text-white text-center text-[15px] font-black outline-none focus:border-terracotta dark:focus:border-terracotta transition-all shadow-sm" required value={isNaN((formData as any)[f.k]) ? "" : (formData as any)[f.k]} onChange={e=>setFormData({...formData, [f.k]: e.target.value === "" ? NaN : parseInt(e.target.value)})} /></div>))}</div>
                  <button type="submit" className="w-full mt-4 py-6 bg-ink-900 dark:bg-terracotta text-white rounded-2xl font-black uppercase tracking-[0.3em] text-[12px] hover:bg-terracotta dark:hover:bg-terracotta/80 transition-all shadow-xl active:scale-[0.98]">Compile Matrix</button>
                </form>
              </motion.div>
            </motion.div>
          )}</AnimatePresence>

      <AnimatePresence>
        {toast && (
          <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />
        )}
      </AnimatePresence>
    </main>
  );
}
