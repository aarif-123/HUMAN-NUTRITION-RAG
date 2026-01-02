// "use client";

// import { useState } from "react";

// type Source = {
//   doc_id: string;
//   chunk_index: number;
//   similarity: number;
//   content?: string; // optional if backend sends snippet later
// };

// export default function Page() {
//   const [message, setMessage] = useState("");
//   const [answer, setAnswer] = useState("");
//   const [sources, setSources] = useState<Source[]>([]);
//   const [loading, setLoading] = useState(false);
//   const [activeSource, setActiveSource] = useState<Source | null>(null);

//   async function sendMessage() {
//     if (!message.trim() || loading) return;

//     setLoading(true);
//     setAnswer("");
//     setSources([]);

//     const res = await fetch("/api/chat", {
//       method: "POST",
//       headers: { "Content-Type": "application/json" },
//       body: JSON.stringify({ message })
//     });

//     const data = await res.json();
//     setAnswer(data.answer);
//     setSources(data.sources || []);
//     setLoading(false);
//   }

//   return (
//     <main className="min-h-screen bg-[#0e0e11] text-[#e6e6eb] flex justify-center px-6 py-10 font-sans">
//       <div className="w-full max-w-3xl space-y-10">

//         {/* Header */}
//         <header className="space-y-2">
//           <h1 className="text-3xl font-semibold tracking-tight">
//             RAG Nutritional Chatbot: Built from Scratch
//           </h1>
//           <p className="text-sm text-[#9a9aa3]">
//             Presented by Vizuara AI Labs
//           </p>
//         </header>

//         {/* Chat Box */}
//         <section className="space-y-6">

//           {/* Input */}
//           <textarea
//             className="w-full bg-[#141418] border border-[#222228] rounded-lg p-4 text-sm resize-none focus:outline-none focus:border-[#3a3a44]"
//             rows={4}
//             placeholder="Ask a research-grade nutrition question…"
//             value={message}
//             onChange={(e) => setMessage(e.target.value)}
//           />

//           <button
//             onClick={sendMessage}
//             disabled={loading}
//             className="px-5 py-2 bg-white text-black text-sm rounded-md hover:opacity-90 disabled:opacity-40"
//           >
//             Ask
//           </button>

//           {/* Answer */}
//           <div className="min-h-[120px]">

//             {loading && (
//               <div className="text-sm text-[#9a9aa3] animate-pulse">
//                 ● ● ●
//               </div>
//             )}

//             {answer && (
//               <div className="space-y-4 text-sm leading-relaxed">
//                 <p>{answer}</p>

//                 {/* Inline citations */}
//                 {sources.length > 0 && (
//                   <div className="flex gap-2 text-xs text-[#7c7c86]">
//                     {sources.map((s, i) => (
//                       <button
//                         key={i}
//                         onClick={() => setActiveSource(s)}
//                         className="hover:text-white underline"
//                       >
//                         [{i + 1}]
//                       </button>
//                     ))}
//                   </div>
//                 )}
//               </div>
//             )}
//           </div>
//         </section>

//         {/* Citation Popup */}
//         {activeSource && (
//           <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
//             <div className="bg-[#141418] border border-[#2a2a32] rounded-lg max-w-xl w-full p-6 space-y-4">
//               <h3 className="text-sm font-semibold">
//                 Source: {activeSource.doc_id}
//               </h3>

//               <p className="text-xs text-[#9a9aa3]">
//                 Chunk {activeSource.chunk_index} · Similarity{" "}
//                 {activeSource.similarity.toFixed(3)}
//               </p>

//               <div className="text-sm bg-[#0e0e11] p-4 rounded border border-[#222228]">
//                 {activeSource.content ||
//                   "Highlighted source text will appear here."}
//               </div>

//               <button
//                 onClick={() => setActiveSource(null)}
//                 className="text-xs text-[#9a9aa3] hover:text-white"
//               >
//                 Close
//               </button>
//             </div>
//           </div>
//         )}
//       </div>
//     </main>
//   );
// }




// "use client";

// import { useState, useRef, useEffect } from "react";
// import { 
//   Send, 
//   BookOpen, 
//   X, 
//   Sparkles, 
//   Search, 
//   Quote, 
//   ArrowRight,
//   Leaf
// } from "lucide-react";
// import { clsx, type ClassValue } from "clsx";
// import { twMerge } from "tailwind-merge";

// // --- Utility for cleaner tailwind classes ---
// function cn(...inputs: ClassValue[]) {
//   return twMerge(clsx(inputs));
// }

// type Source = {
//   doc_id: string;
//   chunk_index: number;
//   similarity: number;
//   content?: string;
// };

// export default function Page() {
//   const [message, setMessage] = useState("");
//   const [answer, setAnswer] = useState("");
//   const [sources, setSources] = useState<Source[]>([]);
//   const [loading, setLoading] = useState(false);
//   const [activeSource, setActiveSource] = useState<Source | null>(null);
//   const textareaRef = useRef<HTMLTextAreaElement>(null);

//   // Auto-resize textarea
//   useEffect(() => {
//     if (textareaRef.current) {
//       textareaRef.current.style.height = "auto";
//       textareaRef.current.style.height = textareaRef.current.scrollHeight + "px";
//     }
//   }, [message]);

//   async function sendMessage() {
//     if (!message.trim() || loading) return;

//     setLoading(true);
//     setAnswer("");
//     setSources([]);

//     try {
//       const res = await fetch("/api/chat", {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//         body: JSON.stringify({ message }),
//       });

//       const data = await res.json();
//       setAnswer(data.answer);
//       setSources(data.sources || []);
//     } catch (e) {
//       setAnswer("Sorry, something went wrong while fetching the nutritional data.");
//     } finally {
//       setLoading(false);
//     }
//   }

//   const handleKeyDown = (e: React.KeyboardEvent) => {
//     if (e.key === "Enter" && !e.shiftKey) {
//       e.preventDefault();
//       sendMessage();
//     }
//   };

//   return (
//     <main className="min-h-screen bg-[#09090b] text-zinc-100 flex flex-col font-sans selection:bg-emerald-500/30">
      
//       {/* Background Gradients */}
//       <div className="fixed inset-0 z-0 pointer-events-none">
//         <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-emerald-900/10 rounded-full blur-[120px]" />
//         <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-blue-900/10 rounded-full blur-[120px]" />
//       </div>

//       <div className="relative z-10 w-full max-w-4xl mx-auto px-4 py-8 md:py-16 flex flex-col gap-8">
        
//         {/* Header */}
//         <header className="text-center space-y-3 mb-8">
//           <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-900 border border-zinc-800 text-xs font-medium text-emerald-400 mb-2">
//             <Leaf size={12} />
//             <span>Mohammed Aarif</span>
//           </div>
//           <h1 className="text-4xl md:text-5xl font-bold tracking-tight bg-gradient-to-b from-white to-zinc-400 bg-clip-text text-transparent">
//             Nutri-RAG Research
//           </h1>
//           <p className="text-zinc-500 text-sm md:text-base max-w-lg mx-auto">
//             Ask complex questions about nutrition and get answers grounded in verified research papers.
//           </p>
//         </header>

//         {/* Search / Input Area */}
//         <section className="w-full">
//           <div className="relative group rounded-2xl bg-zinc-900/50 border border-zinc-800 focus-within:border-emerald-500/50 focus-within:ring-1 focus-within:ring-emerald-500/50 transition-all duration-300 shadow-lg shadow-black/20">
//             <textarea
//               ref={textareaRef}
//               className="w-full bg-transparent text-lg placeholder:text-zinc-600 px-6 py-5 pr-14 min-h-[80px] max-h-[200px] resize-none focus:outline-none rounded-2xl"
//               placeholder="Ex: How does magnesium affect sleep quality?"
//               value={message}
//               onChange={(e) => setMessage(e.target.value)}
//               onKeyDown={handleKeyDown}
//               disabled={loading}
//             />
            
//             <button
//               onClick={sendMessage}
//               disabled={loading || !message.trim()}
//               className={cn(
//                 "absolute right-3 bottom-3 p-2.5 rounded-xl transition-all duration-200",
//                 message.trim() && !loading
//                   ? "bg-emerald-600 text-white hover:bg-emerald-500 shadow-lg shadow-emerald-900/20"
//                   : "bg-zinc-800 text-zinc-500 cursor-not-allowed"
//               )}
//             >
//               {loading ? (
//                 <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
//               ) : (
//                 <Send size={20} />
//               )}
//             </button>
//           </div>
//         </section>

//         {/* Results Area */}
//         {(answer || loading) && (
//           <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 space-y-8">
            
//             {/* Answer Block */}
//             <div className="space-y-4">
//               <div className="flex items-center gap-2 text-emerald-400 text-sm font-medium uppercase tracking-wider">
//                 <Sparkles size={16} />
//                 <span>AI Synthesis</span>
//               </div>
              
//               <div className="prose prose-invert prose-p:text-zinc-300 prose-headings:text-zinc-100 max-w-none leading-relaxed bg-zinc-900/30 p-6 rounded-2xl border border-zinc-800/50">
//                 {loading ? (
//                   <div className="space-y-3 animate-pulse">
//                     <div className="h-4 bg-zinc-800 rounded w-3/4" />
//                     <div className="h-4 bg-zinc-800 rounded w-full" />
//                     <div className="h-4 bg-zinc-800 rounded w-5/6" />
//                   </div>
//                 ) : (
//                   <p className="whitespace-pre-wrap">{answer}</p>
//                 )}
//               </div>
//             </div>

//             {/* Sources Block */}
//             {!loading && sources.length > 0 && (
//               <div className="space-y-4">
//                 <div className="flex items-center gap-2 text-zinc-500 text-sm font-medium uppercase tracking-wider">
//                   <BookOpen size={16} />
//                   <span>Referenced Sources</span>
//                 </div>
                
//                 <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
//                   {sources.map((s, i) => (
//                     <button
//                       key={i}
//                       onClick={() => setActiveSource(s)}
//                       className="group flex items-start gap-3 p-4 text-left bg-zinc-900/50 hover:bg-zinc-800/80 border border-zinc-800 hover:border-zinc-700 rounded-xl transition-all duration-200"
//                     >
//                       <div className="mt-1 min-w-[24px] h-6 flex items-center justify-center rounded bg-emerald-900/30 text-emerald-400 text-xs font-bold border border-emerald-900/50">
//                         {i + 1}
//                       </div>
//                       <div className="space-y-1">
//                         <h4 className="text-sm font-medium text-zinc-200 line-clamp-1 group-hover:text-emerald-400 transition-colors">
//                           {s.doc_id}
//                         </h4>
//                         <div className="flex items-center gap-2 text-xs text-zinc-500">
//                           <span>Sim: {(s.similarity * 100).toFixed(1)}%</span>
//                           <span>•</span>
//                           <span>Chunk {s.chunk_index}</span>
//                         </div>
//                       </div>
//                       <ArrowRight size={16} className="ml-auto text-zinc-600 opacity-0 group-hover:opacity-100 transition-opacity" />
//                     </button>
//                   ))}
//                 </div>
//               </div>
//             )}
//           </div>
//         )}
        
//         {/* Empty State / Suggestions */}
//         {!answer && !loading && (
//           <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
//             {[
//               "Protein absorption rates",
//               "Vitamin D and depression",
//               "Caffeine half-life effects"
//             ].map((suggestion, i) => (
//               <button
//                 key={i}
//                 onClick={() => setMessage(suggestion)}
//                 className="p-4 rounded-xl bg-zinc-900/30 border border-zinc-800 hover:bg-zinc-800/50 hover:border-zinc-700 text-sm text-zinc-400 hover:text-zinc-200 transition-all text-left"
//               >
//                 <div className="flex items-center gap-2 mb-2">
//                     <Search size={14} />
//                     <span className="font-semibold">Sample Query</span>
//                 </div>
//                 "{suggestion}"
//               </button>
//             ))}
//           </div>
//         )}

//       </div>

//       {/* Source Modal */}
//       {activeSource && (
//         <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
//             {/* Backdrop */}
//           <div 
//             className="absolute inset-0 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200" 
//             onClick={() => setActiveSource(null)}
//           />
          
//           {/* Content */}
//           <div className="relative w-full max-w-2xl bg-[#0e0e11] border border-zinc-800 rounded-2xl shadow-2xl animate-in zoom-in-95 duration-200 overflow-hidden flex flex-col max-h-[80vh]">
            
//             {/* Modal Header */}
//             <div className="flex items-center justify-between p-4 border-b border-zinc-800 bg-zinc-900/50">
//               <div className="flex items-center gap-3">
//                 <div className="w-8 h-8 rounded-lg bg-emerald-900/20 flex items-center justify-center text-emerald-500">
//                    <Quote size={16} />
//                 </div>
//                 <div>
//                   <h3 className="text-sm font-semibold text-zinc-100">Source Material</h3>
//                   <p className="text-xs text-zinc-500 font-mono">{activeSource.doc_id}</p>
//                 </div>
//               </div>
//               <button
//                 onClick={() => setActiveSource(null)}
//                 className="p-2 text-zinc-500 hover:text-zinc-100 hover:bg-zinc-800 rounded-lg transition-colors"
//               >
//                 <X size={20} />
//               </button>
//             </div>

//             {/* Modal Body */}
//             <div className="p-6 overflow-y-auto">
//               <div className="text-sm leading-7 text-zinc-300 font-serif">
//                 {activeSource.content || "Source content is pending retrieval..."}
//               </div>
//             </div>

//             {/* Modal Footer */}
//             <div className="p-4 border-t border-zinc-800 bg-zinc-900/30 flex justify-between items-center text-xs text-zinc-500">
//                <span>Match Score: {activeSource.similarity.toFixed(4)}</span>
//                <span>Chunk Index: {activeSource.chunk_index}</span>
//             </div>
//           </div>
//         </div>
//       )}
//     </main>
//   );
// }




"use client";

import { useState, useRef, useEffect } from "react";
import { 
  Send, BookOpen, X, Sparkles, Quote, ArrowRight, Leaf, 
  Copy, Check, Sun, Moon, ExternalLink
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm"; // Needed for Tables
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

// --- Utility: Class Merger ---
function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// --- Types ---
type Source = {
  doc_id: string;
  chunk_index: number;
  similarity: number;
  content?: string;
};

export default function Page() {
  // Theme State
  const [isDarkMode, setIsDarkMode] = useState(true);
  
  // Chat State
  const [message, setMessage] = useState("");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeSource, setActiveSource] = useState<Source | null>(null);
  const [copied, setCopied] = useState(false);
  
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Initialize Theme based on preference or default to dark
  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, [isDarkMode]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = textareaRef.current.scrollHeight + "px";
    }
  }, [message]);

  async function sendMessage() {
    if (!message.trim() || loading) return;

    setLoading(true);
    setAnswer("");
    setSources([]);
    setCopied(false);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });

      const data = await res.json();
      setAnswer(data.answer);
      setSources(data.sources || []);
    } catch (e) {
      setAnswer("Error: Unable to fetch nutritional data. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(answer);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <main className="min-h-screen transition-colors duration-300 bg-zinc-50 dark:bg-[#09090b] text-zinc-900 dark:text-zinc-100 flex flex-col font-sans selection:bg-emerald-500/30">
      
      {/* --- Ambient Background (Dynamic) --- */}
      <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden opacity-50 dark:opacity-100 transition-opacity">
        <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-emerald-500/10 dark:bg-emerald-900/10 rounded-full blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-blue-500/10 dark:bg-blue-900/05 rounded-full blur-[120px]" />
      </div>

      <div className="relative z-10 w-full max-w-4xl mx-auto px-4 py-8 md:py-12 flex flex-col gap-6">
        
        {/* --- Top Bar --- */}
        <div className="flex justify-end w-full">
            <button 
                onClick={() => setIsDarkMode(!isDarkMode)}
                className="p-2 rounded-full bg-zinc-200 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white transition-all"
            >
                {isDarkMode ? <Sun size={20} /> : <Moon size={20} />}
            </button>
        </div>

        {/* --- Header --- */}
        <header className="flex flex-col items-center justify-center space-y-4 mb-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white dark:bg-zinc-900/80 border border-zinc-200 dark:border-zinc-800 text-xs font-medium text-emerald-600 dark:text-emerald-400 shadow-sm backdrop-blur-md">
            <Leaf size={12} />
            <span>BY MOHAMMED AARIF</span>
          </div>
          <h1 className="text-3xl md:text-4xl font-bold tracking-tight text-center text-zinc-800 dark:text-transparent dark:bg-gradient-to-b dark:from-white dark:to-zinc-400 dark:bg-clip-text">
            Nutri-RAG Research
          </h1>
        </header>

        {/* --- Input Section --- */}
        <section className="sticky top-4 z-20 w-full">
          <div className="relative group rounded-2xl bg-white/80 dark:bg-[#121215]/90 backdrop-blur-xl border border-zinc-200 dark:border-zinc-800 shadow-xl dark:shadow-black/50 focus-within:border-emerald-500/50 focus-within:ring-1 focus-within:ring-emerald-500/50 transition-all duration-300">
            <textarea
              ref={textareaRef}
              className="w-full bg-transparent text-lg text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 dark:placeholder:text-zinc-600 px-6 py-5 pr-14 min-h-[70px] max-h-[200px] resize-none focus:outline-none rounded-2xl"
              placeholder="Ask a nutrition question (e.g., 'Compare Vitamin D sources in a table')..."
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={loading}
            />
            
            <button
              onClick={sendMessage}
              disabled={loading || !message.trim()}
              className={cn(
                "absolute right-3 bottom-3 p-2.5 rounded-xl transition-all duration-200",
                message.trim() && !loading
                  ? "bg-emerald-600 text-white hover:bg-emerald-500 shadow-lg shadow-emerald-600/20"
                  : "bg-zinc-100 dark:bg-zinc-800 text-zinc-400 dark:text-zinc-500 cursor-not-allowed"
              )}
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-zinc-400 border-t-transparent rounded-full animate-spin" />
              ) : (
                <Send size={20} />
              )}
            </button>
          </div>
        </section>

        {/* --- Results Section --- */}
        {(answer || loading) && (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 space-y-8 pb-20">
            
            {/* 1. Answer Block */}
            <div className="space-y-4">
              <div className="flex items-center justify-between px-2">
                <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 text-sm font-medium uppercase tracking-wider">
                  <Sparkles size={16} />
                  <span>AI Synthesis</span>
                </div>
                {!loading && answer && (
                  <button 
                    onClick={copyToClipboard}
                    className="flex items-center gap-2 text-xs text-zinc-500 hover:text-emerald-600 dark:hover:text-white transition-colors"
                  >
                    {copied ? <Check size={14} /> : <Copy size={14} />}
                    {copied ? "Copied" : "Copy"}
                  </button>
                )}
              </div>
              
              <div className="relative group bg-white dark:bg-zinc-900/40 p-6 md:p-8 rounded-2xl border border-zinc-200 dark:border-zinc-800/60 shadow-sm">
                {loading ? (
                  <div className="space-y-4 animate-pulse max-w-2xl">
                    <div className="h-4 bg-zinc-200 dark:bg-zinc-800 rounded w-3/4" />
                    <div className="h-4 bg-zinc-200 dark:bg-zinc-800 rounded w-full" />
                    <div className="h-4 bg-zinc-200 dark:bg-zinc-800 rounded w-5/6" />
                  </div>
                ) : (
                  <article className="prose prose-zinc dark:prose-invert max-w-none leading-relaxed">
                    <ReactMarkdown 
                        remarkPlugins={[remarkGfm]}
                        components={{
                            // 1. Custom Link Rendering
                            a: ({node, ...props}) => (
                                <a 
                                    {...props} 
                                    target="_blank" 
                                    rel="noopener noreferrer"
                                    className="text-blue-600 dark:text-blue-400 hover:underline inline-flex items-center gap-1 font-medium"
                                >
                                    {props.children}
                                    <ExternalLink size={12} />
                                </a>
                            ),
                            // 2. Custom Table Rendering
                            table: ({node, ...props}) => (
                                <div className="overflow-x-auto my-6 rounded-lg border border-zinc-200 dark:border-zinc-800">
                                    <table {...props} className="w-full text-sm text-left" />
                                </div>
                            ),
                            thead: ({node, ...props}) => (
                                <thead {...props} className="bg-zinc-100 dark:bg-zinc-800/50 text-zinc-700 dark:text-zinc-300 uppercase font-semibold" />
                            ),
                            th: ({node, ...props}) => (
                                <th {...props} className="px-6 py-3" />
                            ),
                            tr: ({node, ...props}) => (
                                <tr {...props} className="border-b border-zinc-100 dark:border-zinc-800 last:border-none hover:bg-zinc-50 dark:hover:bg-zinc-800/30" />
                            ),
                            td: ({node, ...props}) => (
                                <td {...props} className="px-6 py-4" />
                            ),
                        }}
                    >
                        {answer}
                    </ReactMarkdown>
                  </article>
                )}
              </div>
            </div>

            {/* 2. Sources Block */}
            {!loading && sources.length > 0 && (
              <div className="space-y-4">
                <div className="flex items-center justify-between px-2">
                  <div className="flex items-center gap-2 text-zinc-500 text-sm font-medium uppercase tracking-wider">
                    <BookOpen size={16} />
                    <span>Reference Material</span>
                  </div>
                  <span className="text-xs text-zinc-500 bg-zinc-100 dark:bg-zinc-900 px-2 py-1 rounded border border-zinc-200 dark:border-zinc-800">
                    {sources.length} citations
                  </span>
                </div>
                
                {/* Source Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {sources.map((s, i) => (
                    <button
                      key={i}
                      onClick={() => setActiveSource(s)}
                      className="group flex flex-col text-left bg-white dark:bg-[#121215] hover:bg-zinc-50 dark:hover:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 hover:border-emerald-500/30 rounded-xl transition-all duration-200 overflow-hidden h-full shadow-sm hover:shadow-md"
                    >
                      {/* Card Header */}
                      <div className="p-4 w-full border-b border-zinc-100 dark:border-zinc-800/50 bg-zinc-50/50 dark:bg-zinc-900/30 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-6 h-6 flex items-center justify-center rounded bg-zinc-200 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 text-xs font-bold group-hover:bg-emerald-100 dark:group-hover:bg-emerald-900/50 group-hover:text-emerald-700 dark:group-hover:text-emerald-400 transition-colors">
                            {i + 1}
                          </div>
                          <span className="text-xs font-medium text-zinc-600 dark:text-zinc-400 uppercase tracking-wide truncate max-w-[150px]">
                            {s.doc_id}
                          </span>
                        </div>
                        <span className="text-[10px] font-mono text-zinc-500">
                           Sim: {(s.similarity * 100).toFixed(0)}%
                        </span>
                      </div>
                      
                      {/* Card Preview Snippet */}
                      <div className="p-4 flex-1 w-full">
                         <p className="text-sm text-zinc-600 dark:text-zinc-400 leading-relaxed line-clamp-3 font-serif">
                           {s.content 
                             ? s.content 
                             : <span className="italic opacity-50">No preview text available...</span>}
                         </p>
                      </div>

                      <div className="px-4 pb-4 pt-0 w-full flex justify-end">
                        <span className="text-xs text-emerald-600 dark:text-emerald-500 opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
                          Read Full <ArrowRight size={12} />
                        </span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* --- Source Modal (Reader) --- */}
      {activeSource && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6">
          <div 
            className="absolute inset-0 bg-black/60 dark:bg-black/80 backdrop-blur-sm animate-in fade-in duration-200" 
            onClick={() => setActiveSource(null)}
          />
          
          <div className="relative w-full max-w-3xl bg-white dark:bg-[#0e0e11] border border-zinc-200 dark:border-zinc-700 rounded-2xl shadow-2xl animate-in zoom-in-95 duration-200 flex flex-col max-h-[85vh]">
            
            {/* Modal Header */}
            <div className="flex items-center justify-between p-5 border-b border-zinc-100 dark:border-zinc-800 bg-zinc-50 dark:bg-[#121215]">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-emerald-100 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-500">
                   <Quote size={18} />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">Source Context</h3>
                  <div className="flex items-center gap-2 text-xs text-zinc-500">
                    <span>{activeSource.doc_id}</span>
                    <span>•</span>
                    <span>Chunk Index: {activeSource.chunk_index}</span>
                  </div>
                </div>
              </div>
              <button
                onClick={() => setActiveSource(null)}
                className="p-2 text-zinc-500 hover:text-zinc-900 dark:hover:text-white hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-lg transition-colors"
              >
                <X size={20} />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 md:p-8 overflow-y-auto custom-scrollbar">
              <div className="prose prose-sm md:prose-base prose-zinc dark:prose-invert max-w-none font-serif leading-7">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {activeSource.content || "Source content unavailable."}
                </ReactMarkdown>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-zinc-100 dark:border-zinc-800 bg-zinc-50 dark:bg-[#121215] flex justify-between items-center text-xs text-zinc-500">
               <span className="flex items-center gap-2">
                 <Leaf size={12} className="text-emerald-600"/> 
                 Processed by Vector Engine and Supabase
               </span>
               <span className="font-mono">Score: {activeSource.similarity.toFixed(4)}</span>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}