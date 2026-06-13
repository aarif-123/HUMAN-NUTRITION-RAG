document.addEventListener('DOMContentLoaded', () => {
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const chatFeed = document.getElementById('chat-feed');
    const heroContainer = document.getElementById('hero-container');
    const historyList = document.getElementById('history-list');
    const themeToggle = document.getElementById('theme-toggle');
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sidebar');
    const newChatBtn = document.getElementById('new-chat-btn');
    const modal = document.getElementById('source-modal');
    const modalBody = document.getElementById('modal-body');
    const closeModal = document.getElementById('close-modal');
    const exportBtn = document.getElementById('export-btn');

    // --- State Management ---
    let sessions = JSON.parse(localStorage.getItem('nutri_rag_sessions') || '[]');
    let activeSessionId = localStorage.getItem('nutri_rag_active_session_id') || null;

    // --- Initialization ---
    initApp();

    function initApp() {
        // Load theme
        if (localStorage.getItem('theme') === 'light') {
            document.body.classList.remove('dark-mode');
            themeToggle.innerHTML = '<i data-lucide="moon"></i>';
        } else {
            themeToggle.innerHTML = '<i data-lucide="sun"></i>';
        }

        // Setup active session
        if (sessions.length === 0) {
            createNewSession();
        } else {
            if (!activeSessionId || !sessions.find(s => s.id === activeSessionId)) {
                activeSessionId = sessions[0].id;
            }
            loadSession(activeSessionId);
        }
        renderSessionsList();
        lucide.createIcons();
    }

    // --- Helper: UUID Generation ---
    function generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    // --- Session Actions ---
    function createNewSession() {
        const newId = generateUUID();
        const newSession = {
            id: newId,
            title: "New Research Session",
            messages: []
        };
        sessions.unshift(newSession);
        activeSessionId = newId;
        saveSessions();
        loadSession(newId);
        renderSessionsList();
    }

    function loadSession(id) {
        activeSessionId = id;
        localStorage.setItem('nutri_rag_active_session_id', id);
        
        chatFeed.innerHTML = '';
        const session = sessions.find(s => s.id === id);
        
        if (!session || session.messages.length === 0) {
            chatFeed.appendChild(heroContainer);
            heroContainer.classList.remove('hidden');
            exportBtn.disabled = true;
        } else {
            heroContainer.classList.add('hidden');
            session.messages.forEach(msg => {
                appendMessageToDOM(msg.role, msg.content, msg.sources, msg.intent, msg.proof);
            });
            exportBtn.disabled = false;
        }
        renderSessionsList();
        lucide.createIcons();
    }

    function saveSessions() {
        localStorage.setItem('nutri_rag_sessions', JSON.stringify(sessions));
    }

    function renderSessionsList() {
        historyList.innerHTML = '';
        sessions.forEach(s => {
            const item = document.createElement('div');
            item.className = `history-item ${s.id === activeSessionId ? 'active' : ''}`;
            
            const titleSpan = document.createElement('span');
            titleSpan.innerText = s.title;
            titleSpan.style.overflow = 'hidden';
            titleSpan.style.textOverflow = 'ellipsis';
            titleSpan.style.whiteSpace = 'nowrap';
            titleSpan.style.flex = '1';
            item.appendChild(titleSpan);

            // Delete Session Button
            const delBtn = document.createElement('button');
            delBtn.className = 'action-btn';
            delBtn.style.padding = '2px';
            delBtn.style.marginLeft = '8px';
            delBtn.innerHTML = '<i data-lucide="trash-2" size="14"></i>';
            delBtn.onclick = (e) => {
                e.stopPropagation();
                deleteSession(s.id);
            };
            item.appendChild(delBtn);

            item.onclick = () => loadSession(s.id);
            historyList.appendChild(item);
        });
        lucide.createIcons();
    }

    function deleteSession(id) {
        sessions = sessions.filter(s => s.id !== id);
        saveSessions();
        if (activeSessionId === id) {
            activeSessionId = sessions.length > 0 ? sessions[0].id : null;
        }
        initApp();
    }

    // --- Theme Management ---
    themeToggle.addEventListener('click', () => {
        document.body.classList.toggle('dark-mode');
        const isDark = document.body.classList.contains('dark-mode');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
        themeToggle.innerHTML = isDark ? '<i data-lucide="sun"></i>' : '<i data-lucide="moon"></i>';
        lucide.createIcons();
    });

    // --- Sidebar Toggle ---
    sidebarToggle.addEventListener('click', () => {
        sidebar.classList.toggle('collapsed');
    });

    // --- New Chat Button ---
    newChatBtn.addEventListener('click', createNewSession);

    // --- Input Auto-resize ---
    chatInput.addEventListener('input', () => {
        chatInput.style.height = 'auto';
        chatInput.style.height = Math.min(chatInput.scrollHeight, 180) + 'px';
        sendBtn.disabled = !chatInput.value.trim();
    });

    // --- DOM Rendering ---
    function appendMessageToDOM(role, content, sources = [], intent = null, proof = null) {
        heroContainer.classList.add('hidden');
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${role}-message`;
        
        const avatar = document.createElement('div');
        avatar.className = `avatar ${role}-avatar`;
        avatar.innerHTML = role === 'user' ? '<i data-lucide="user"></i>' : '<i data-lucide="leaf"></i>';
        
        const card = document.createElement('div');
        card.className = 'message-card';

        // Badge & Copy Row (For AI responses)
        if (role === 'ai') {
            const badgeRow = document.createElement('div');
            badgeRow.className = 'badge-row';

            // Intent Badge
            const badge = document.createElement('span');
            badge.className = 'intent-badge';
            if (intent === 'NUTRITION') {
                badge.className += ' badge-nutrition';
                badge.innerHTML = '<i data-lucide="shield-check" style="display:inline-block; vertical-align:middle; margin-right:4px;" size="12"></i>Grounded Research';
            } else if (intent === 'GREETING') {
                badge.className += ' badge-greeting';
                badge.innerHTML = 'Greeting';
            } else if (intent === 'OFFTOPIC') {
                badge.className += ' badge-offtopic';
                badge.innerHTML = 'Off-Topic';
            } else {
                badge.className += ' badge-nutrition';
                badge.innerHTML = 'Response';
            }
            badgeRow.appendChild(badge);

            // Copy to Clipboard
            const copyBtn = document.createElement('button');
            copyBtn.className = 'copy-btn';
            copyBtn.title = 'Copy Answer';
            copyBtn.innerHTML = '<i data-lucide="copy" size="14"></i>';
            copyBtn.onclick = () => {
                navigator.clipboard.writeText(content);
                copyBtn.innerHTML = '<i data-lucide="check" style="color: var(--accent-primary);" size="14"></i>';
                setTimeout(() => {
                    copyBtn.innerHTML = '<i data-lucide="copy" size="14"></i>';
                    lucide.createIcons();
                }, 2000);
            };
            badgeRow.appendChild(copyBtn);
            card.appendChild(badgeRow);
        }

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content prose';
        messageContent.innerHTML = marked.parse(content);
        card.appendChild(messageContent);
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(card);
        
        if (proof && role === 'ai') {
            const proofDiv = document.createElement('div');
            proofDiv.className = 'sources-container';
            proofDiv.innerHTML = `<div class="sources-header">Context Proof</div>
                <div style="font-size:0.82rem; color:var(--text-dim);">
                    grounded: <b>${proof.grounded}</b> | chunks: <b>${proof.retrieved_chunks}</b> | top similarity: <b>${((proof.top_similarity || 0) * 100).toFixed(1)}%</b>
                </div>`;
            card.appendChild(proofDiv);
        }
        if (sources && sources.length > 0) {
            const sourcesDiv = document.createElement('div');
            sourcesDiv.className = 'sources-container';
            sourcesDiv.innerHTML = '<div class="sources-header">Sources & Citations</div>';
            
            const grid = document.createElement('div');
            grid.className = 'sources-grid';
            
            sources.forEach((src, idx) => {
                const pill = document.createElement('div');
                pill.className = 'source-pill';
                pill.innerHTML = `
                    <span style="font-weight: 700; color: var(--accent-secondary); margin-right: 4px;">[${idx + 1}]</span>
                    <span>${src.doc_id.substring(0, 16)}</span>
                `;
                pill.onclick = () => openModal(src);
                grid.appendChild(pill);
            });
            
            sourcesDiv.appendChild(grid);
            card.appendChild(sourcesDiv);
        }
        
        chatFeed.appendChild(messageDiv);
        chatFeed.scrollTop = chatFeed.scrollHeight;
        lucide.createIcons();
    }

    // --- Send Message ---
    async function sendMessage() {
        const message = chatInput.value.trim();
        if (!message) return;

        // Clear input
        chatInput.value = '';
        chatInput.style.height = 'auto';
        sendBtn.disabled = true;

        // Auto-create session if none active
        if (!activeSessionId) {
            const newId = generateUUID();
            const newSession = {
                id: newId,
                title: message.length > 22 ? message.substring(0, 20) + "..." : message,
                messages: []
            };
            sessions.unshift(newSession);
            activeSessionId = newId;
            saveSessions();
            renderSessionsList();
        }

        // Append user query to UI and state
        appendMessageToDOM('user', message);
        saveMessageToActiveSession('user', message);

        // Display Loading
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'chat-message ai-message loading-state';
        loadingDiv.innerHTML = `
            <div class="avatar ai-avatar"><i data-lucide="leaf"></i></div>
            <div class="message-card">
                <div class="shimmer" style="width: 30%; margin-bottom: 12px; background: var(--accent-glow);"></div>
                <div class="shimmer" style="width: 85%"></div>
                <div class="shimmer" style="width: 70%"></div>
                <div class="shimmer" style="width: 50%"></div>
            </div>
        `;
        chatFeed.appendChild(loadingDiv);
        chatFeed.scrollTop = chatFeed.scrollHeight;
        lucide.createIcons();

        try {
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    message: message,
                    session_id: activeSessionId
                })
            });

            if (!res.ok) throw new Error(`HTTP Error ${res.status}`);
            
            const data = await res.json();
            loadingDiv.remove();
            
            const finalAnswer = data.answer && data.answer.trim() ? data.answer.trim() : "*[Empty response received]*";
            
            appendMessageToDOM('ai', finalAnswer, data.sources, data.intent, data.proof_of_context);
            saveMessageToActiveSession('ai', finalAnswer, data.sources, data.intent, data.proof_of_context);
            
            // Enable Markdown download
            exportBtn.disabled = false;

        } catch (error) {
            console.error("Error fetching chat API:", error);
            loadingDiv.remove();
            appendMessageToDOM('ai', `**AI Connection Error:** ${error.message}`, [], 'OFFTOPIC');
        }
    }

    function saveMessageToActiveSession(role, content, sources = [], intent = null, proof = null) {
        const session = sessions.find(s => s.id === activeSessionId);
        if (session) {
            session.messages.push({ role, content, sources, intent, proof });
            // Dynamically rename the session title based on the first user query
            if (session.messages.length === 1 && role === 'user') {
                session.title = content.length > 22 ? content.substring(0, 20) + "..." : content;
            }
            saveSessions();
            renderSessionsList();
        }
    }

    sendBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // --- Export as Markdown ---
    exportBtn.addEventListener('click', () => {
        const activeSession = sessions.find(s => s.id === activeSessionId);
        if (!activeSession || activeSession.messages.length === 0) return;

        let markdown = `# Nutri-RAG Research Transcript: ${activeSession.title}\n`;
        markdown += `*Session ID: ${activeSession.id}*\n\n---\n\n`;

        activeSession.messages.forEach((msg, idx) => {
            const roleName = msg.role === 'user' ? '🧑 User Question' : '🌿 Nutri-RAG Synthesis';
            markdown += `### ${roleName}\n\n${msg.content}\n\n`;

            if (msg.sources && msg.sources.length > 0) {
                markdown += `**References Cited:**\n`;
                msg.sources.forEach((src, sIdx) => {
                    markdown += `${sIdx + 1}. **${src.doc_id}** (Similarity: ${(src.similarity * 100).toFixed(1)}%, Chunk ${src.chunk_index})\n`;
                });
                markdown += `\n`;
            }
            markdown += `\n---\n\n`;
        });

        // Download markdown file
        const blob = new Blob([markdown], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `nutri-rag-${activeSession.title.toLowerCase().replace(/[^a-z0-9]+/g, '-')}.md`;
        a.click();
        URL.revokeObjectURL(url);
    });

    // --- Modal Logic ---
    function openModal(source) {
        let content = source.content || "No detailed source context was returned.";
        content = content.replace(/[‘’]/g, "'").replace(/[“”]/g, '"');

        modalBody.innerHTML = `
            <div style="margin-bottom: 1.5rem; padding: 1rem; background: var(--bg-main); border-radius: 12px; font-size: 0.8rem; border: 1px solid var(--border-dim); display: flex; flex-direction: column; gap: 4px;">
                <div><span style="color: var(--text-dim);">Document:</span> <span style="font-weight: 500;">${source.doc_id}</span></div>
                <div><span style="color: var(--text-dim);">Match Relevance:</span> <span style="font-weight: 500; color: var(--accent-secondary);">${(source.similarity * 100).toFixed(2)}%</span></div>
                <div><span style="color: var(--text-dim);">Chunk Index:</span> <span style="font-weight: 500;">${source.chunk_index}</span></div>
            </div>
            <div class="prose" style="white-space: pre-wrap; font-family: var(--font-inter); line-height: 1.6; font-size: 0.95rem;">${marked.parse(content)}</div>
        `;
        modal.classList.remove('hidden');
    }

    function hideModal() {
        modal.classList.add('hidden');
    }

    closeModal.onclick = hideModal;
    document.querySelector('.modal-overlay').onclick = hideModal;
});
