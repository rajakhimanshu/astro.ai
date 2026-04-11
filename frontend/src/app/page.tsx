"use client";

import React, { useState, useEffect, useRef } from 'react';
import { Sparkles, Moon, Sun, Star, Plus, Check } from 'lucide-react';

const API_BASE = typeof window !== 'undefined' ? `http://${window.location.hostname}:8000/api` : 'http://127.0.0.1:8000/api';

export default function Page() {
  const [users, setUsers] = useState([]);
  const [activeUser, setActiveUser] = useState(null);
  const [profile, setProfile] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [showProfileModal, setShowProfileModal] = useState(false);
  const messagesEndRef = useRef(null);

  // Profile Form State
  const [formData, setFormData] = useState({
    name: "", gender: "Male", year: 2000, month: 1, day: 1, 
    hour: 12, minute: 0, city: "", nation: "IN", timezone: "Asia/Kolkata"
  });

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const res = await fetch(`${API_BASE}/users`);
      if (res.ok) {
        const data = await res.json();
        setUsers(data.users || []);
        if (data.active_user_id) {
          fetchProfile(data.active_user_id);
        } else if (data.users && data.users.length > 0) {
          switchUser(data.users[0].user_id);
        }
      }
    } catch(e) {
      console.error("Backend not running yet", e);
    }
  }

  const fetchProfile = async (userId) => {
    try {
      const res = await fetch(`${API_BASE}/users/${userId}/profile`);
      if (res.ok) {
        const data = await res.json();
        setActiveUser(userId);
        setProfile(data);
        if (messages.length === 0) {
            setMessages([{ role: "bot", content: `Namaste, ${data.meta.name}. I have read your 12-layer planetary chart. How can I guide you today?` }]);
        }
      }
    } catch(e) {
      console.error(e);
    }
  }

  const switchUser = async (userId) => {
    try {
      await fetch(`${API_BASE}/users/active`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId })
      });
      fetchProfile(userId);
      setMessages([]);
    } catch(e) {}
  }

  const handleCreateProfile = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE}/users`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      if (res.ok) {
        const data = await res.json();
        setShowProfileModal(false);
        fetchUsers();
      }
    } catch(e) {}
  };

  const handleChat = async () => {
    if (!input.trim() || isTyping) return;
    const msg = input;
    setInput("");
    setMessages(prev => [...prev, { role: "user", content: msg }]);
    setIsTyping(true);

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg, user_id: activeUser })
      });

      if (!res.body) return;
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let botResponse = "";

      setMessages(prev => [...prev, { role: "bot", content: "" }]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        botResponse += decoder.decode(value);
        setMessages(prev => {
          const newMsg = [...prev];
          newMsg[newMsg.length - 1] = { role: "bot", content: botResponse };
          return newMsg;
        });
      }
    } catch (e) {
      console.error(e);
    }
    setIsTyping(false);
  }

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <main className="relative w-full h-screen flex flex-col md:flex-row overflow-hidden text-[14px]">
      {/* Dynamic Background */}
      <div className="absolute inset-0 z-0 pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-purple-900/30 blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[30%] h-[50%] rounded-full bg-indigo-900/30 blur-[120px]" />
      </div>

      {/* Sidebar */}
      <aside className="w-full md:w-80 h-full border-r border-white/5 bg-black/40 backdrop-blur-md z-10 flex flex-col p-6 space-y-6 shrink-0 relative">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3 text-purple-400 font-semibold text-lg tracking-wide">
            <Sparkles className="w-5 h-5 text-yellow-500" />
            <span>Astro.AI</span>
          </div>
          <select 
            className="bg-purple-900/40 border border-purple-500/30 rounded-lg p-1 text-[11px] text-purple-200 outline-none"
            value={activeUser || ""}
            onChange={(e) => switchUser(e.target.value)}
          >
            <option value="" disabled>Select User</option>
            {users.map((u: any) => <option key={u.user_id} value={u.user_id}>{u.name}</option>)}
          </select>
        </div>

        {profile ? (
          <div className="flex-1 overflow-y-auto pr-2 space-y-6 text-gray-300 custom-scrollbar">
            {profile.remedies && profile.remedies.length > 0 && profile.remedies[0].planet !== "General" && (
              <section className="space-y-3">
                <h3 className="text-[10px] uppercase tracking-widest text-red-400 font-semibold mb-2">Remedy Alerts</h3>
                {profile.remedies.map((rem: any, idx: number) => (
                  <div key={idx} className="glass-panel p-3 border-red-500/20 bg-red-900/10 rounded-xl mb-2 relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-1 h-full bg-red-500/50" />
                    <p className="font-medium text-red-200 text-xs">{rem.planet} ({rem.reason})</p>
                    <p className="text-[10px] text-red-400/80 mt-1 leading-snug">{rem.mantra}</p>
                  </div>
                ))}
            </section>
            )}

            <section className="space-y-3">
               <h3 className="text-[10px] uppercase tracking-widest text-gray-500 font-semibold mb-2">Profile Overview</h3>
               <div className="glass-panel p-4 border-white/5 bg-white/5 rounded-xl text-xs space-y-2 text-gray-300">
                  <p><span className="text-gray-500">Lagna:</span> {profile.lagna.sign}</p>
                  <p><span className="text-gray-500">Moon:</span> {profile.rashi.sign}</p>
                  <p><span className="text-gray-500">Lagna Lord:</span> {profile.lagna.lord} (H{profile.lagna.lord_house})</p>
               </div>
            </section>

            <section className="space-y-3">
              <h3 className="text-[10px] uppercase tracking-widest text-gray-500 font-semibold mb-2">Current Dasha</h3>
              <div className="glass-panel p-4 border-white/5 bg-white/5 rounded-xl">
                <p className="text-[11px] text-gray-400 mb-1 leading-relaxed">{profile.dasha.summary}</p>
                <div className="flex items-center justify-between mt-3">
                  <div className="text-center">
                    <span className="text-purple-300 font-bold block">{profile.dasha.current_md}</span>
                    <span className="text-[10px] text-gray-500">MD</span>
                  </div>
                  <div className="text-center">
                    <span className="text-yellow-300 font-bold block">{profile.dasha.current_ad}</span>
                    <span className="text-[10px] text-gray-500">AD</span>
                  </div>
                  <div className="text-center">
                    <span className="text-gray-300 font-bold block">{profile.dasha.current_pd}</span>
                    <span className="text-[10px] text-gray-500">PD</span>
                  </div>
                </div>
              </div>
            </section>

            <section className="space-y-3">
              <h3 className="text-[10px] uppercase tracking-widest text-gray-500 font-semibold mb-2">Dominant Planets (Shadbala)</h3>
              <div className="space-y-1 bg-white/5 p-2 rounded-xl border border-white/5">
                {Object.entries(profile.shadbala)
                  .sort((a: any,b: any) => b[1] - a[1])
                  .slice(0, 3).map((p: any, i: number) => (
                  <div key={i} className="flex items-center justify-between p-2 rounded-lg hover:bg-white/5">
                    <span className="text-[12px] font-medium text-gray-200">{p[0]}</span>
                    <span className="text-[10px] font-mono text-purple-300/80 bg-purple-900/20 px-2 py-0.5 rounded-full">{p[1]}/10</span>
                  </div>
                ))}
              </div>
            </section>
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-gray-500 text-xs px-4 text-center space-y-2">
             <div className="w-12 h-12 rounded-full bg-white/5 flex items-center justify-center mb-2"><Moon className="text-gray-600" /></div>
             <p>No active profile loaded.</p>
             <p>Ensure Python Backend is running on port 8000.</p>
          </div>
        )}
        
        <div className="mt-auto pt-4 border-t border-white/5">
          <button 
            onClick={() => setShowProfileModal(true)}
            className="w-full flex items-center justify-center space-x-2 py-3 rounded-xl bg-purple-600/20 text-purple-200 hover:bg-purple-600/40 border border-purple-500/20 transition-colors text-xs font-semibold"
          >
            <Plus className="w-4 h-4" />
            <span>Create Profile</span>
          </button>
        </div>
      </aside>

      {/* Main Chat Interface */}
      <section className="flex-1 h-full flex flex-col z-10 bg-black/20 lg:ml-0">
        <header className="h-[72px] border-b border-white/5 flex items-center px-8 justify-between shrink-0 bg-black/20 backdrop-blur-md">
          <h2 className="text-sm font-medium text-white flex items-center space-x-2">
            <span className="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)] animate-pulse" />
            <span>Vedic Consultation</span>
          </h2>
        </header>

        <div className="flex-1 overflow-y-auto p-6 md:p-10 space-y-8 custom-scrollbar scroll-smooth">
          <div className="max-w-3xl mx-auto space-y-8 pb-4">
            {messages.length === 0 && profile && (
                 <div className="text-center text-gray-500 text-xs mt-20">Type a question below to consult Astro.AI about your chart.</div>
            )}
            {messages.map((m: any, i: number) => (
              <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                {m.role === 'bot' && (
                  <div className="w-8 h-8 mr-4 rounded-full bg-gradient-to-br from-purple-600 to-indigo-900 flex items-center justify-center shrink-0 border border-purple-400/30 mt-1 shadow-[0_0_15px_rgba(147,51,234,0.3)]">
                    <Sparkles className="w-4 h-4 text-white" />
                  </div>
                )}
                <div className={`glass-panel p-4 px-5 rounded-2xl text-[14.5px] font-light leading-relaxed max-w-[85%] whitespace-pre-wrap ${m.role === 'user' ? 'bg-purple-900/30 border-purple-500/20 rounded-tr-sm text-purple-50 shadow-lg' : 'bg-black/40 border-white/5 text-gray-200'}`}>
                  {m.content}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        </div>

        <div className="p-4 md:p-8 shrink-0 relative bg-black/40 backdrop-blur-xl border-t border-white/5">
          <div className="max-w-3xl mx-auto relative group flex items-center">
            <input 
              type="text" 
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleChat()}
              placeholder="Ask the Jyotish Oracle about your career, timing, or life..." 
              className="w-full glass-panel bg-white/5 border border-white/10 p-4 pl-6 pr-14 rounded-full text-[14px] text-white font-light placeholder-gray-500 focus:outline-none focus:border-purple-500/50 focus:ring-1 focus:ring-purple-500/50"
            />
            <button onClick={handleChat} disabled={isTyping || !profile} className="absolute right-2.5 top-2.5 bottom-2.5 aspect-square rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center active:scale-95 transition-all outline-none disabled:opacity-50">
              <Check className="w-5 h-5 text-white" />
            </button>
          </div>
        </div>
      </section>

      {/* Profile Creation Modal */}
      {showProfileModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="glass-panel w-full max-w-md p-6 border-purple-500/30 bg-gray-950/90 rounded-2xl shadow-2xl">
            <h3 className="text-lg font-semibold text-white mb-4">Create Birth Profile</h3>
            <form onSubmit={handleCreateProfile} className="space-y-4">
              <input type="text" placeholder="Full Name" className="w-full p-2.5 rounded bg-white/5 border border-white/10 text-white outline-none" required value={formData.name} onChange={e=>setFormData({...formData, name: e.target.value})} />
              <div className="flex space-x-2">
                <input type="text" placeholder="City" className="w-1/2 p-2.5 rounded bg-white/5 border border-white/10 text-white outline-none" required value={formData.city} onChange={e=>setFormData({...formData, city: e.target.value})} />
                <input type="text" placeholder="Country Code (IN, US)" className="w-1/2 p-2.5 rounded bg-white/5 border border-white/10 text-white outline-none" required value={formData.nation} onChange={e=>setFormData({...formData, nation: e.target.value})} />
              </div>
              <div className="flex space-x-2">
                <input type="number" placeholder="YYYY" className="w-1/3 p-2.5 rounded bg-white/5 border border-white/10 text-white outline-none" required value={formData.year} onChange={e=>setFormData({...formData, year: parseInt(e.target.value)})} />
                <input type="number" placeholder="MM" className="w-1/3 p-2.5 rounded bg-white/5 border border-white/10 text-white outline-none" required value={formData.month} onChange={e=>setFormData({...formData, month: parseInt(e.target.value)})} />
                <input type="number" placeholder="DD" className="w-1/3 p-2.5 rounded bg-white/5 border border-white/10 text-white outline-none" required value={formData.day} onChange={e=>setFormData({...formData, day: parseInt(e.target.value)})} />
              </div>
              <div className="flex space-x-2">
                <input type="number" placeholder="HH (0-23)" className="w-1/2 p-2.5 rounded bg-white/5 border border-white/10 text-white outline-none" required value={formData.hour} onChange={e=>setFormData({...formData, hour: parseInt(e.target.value)})} />
                <input type="number" placeholder="MM" className="w-1/2 p-2.5 rounded bg-white/5 border border-white/10 text-white outline-none" required value={formData.minute} onChange={e=>setFormData({...formData, minute: parseInt(e.target.value)})} />
              </div>
              <div className="flex space-x-2 pt-2">
                <button type="button" onClick={()=>setShowProfileModal(false)} className="w-1/2 p-2.5 rounded bg-white/10 hover:bg-white/20 text-white font-medium transition-colors outline-none">Cancel</button>
                <button type="submit" className="w-1/2 p-2.5 rounded bg-purple-600 hover:bg-purple-500 text-white font-medium transition-colors outline-none">Compute Chart</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </main>
  );
}
