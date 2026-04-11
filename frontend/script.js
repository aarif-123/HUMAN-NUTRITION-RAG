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

    let history = JSON.parse(localStorage.getItem('nutri_rag_history') || '[]');

    // --- Initialization ---
    renderHistory();
    lucide.createIcons();

    // --- Theme Management ---
    themeToggle.addEventListener('click', () => {
        document.body.classList.toggle('dark-mode');
        const isDark = document.body.classList.contains('dark-mode');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
        updateIcons();
    });

    if (localStorage.getItem('theme') === 'light') {
        document.body.classList.remove('dark-mode');
    }

    // --- Sidebar Toggle ---
    sidebarToggle.addEventListener('click', () => {
        sidebar.classList.toggle('collapsed');
    });

    // --- New Chat ---
    newChatBtn.addEventListener('click', () => {
        chatFeed.innerHTML = '';
        chatFeed.appendChild(heroContainer);
        heroContainer.classList.remove('hidden');
    });

    // --- Input Auto-resize ---
    chatInput.addEventListener('input', () => {
        chatInput.style.height = 'auto';
        chatInput.style.height = Math.min(chatInput.scrollHeight, 200) + 'px';
        sendBtn.disabled = !chatInput.value.trim();
    });

    // --- Message Rendering ---
    function appendMessage(role, content, sources = []) {
        heroContainer.classList.add('hidden');
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${role}-message`;
        
        const avatar = document.createElement('div');
        avatar.className = `avatar ${role}-avatar`;
        avatar.innerHTML = role === 'user' ? '<i data-lucide="user"></i>' : '<i data-lucide="sparkles" class="text-blue"></i>';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content prose';
        messageContent.innerHTML = marked.parse(content);
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);
        
        if (sources.length > 0) {
            const sourcesDiv = document.createElement('div');
            sourcesDiv.className = 'sources-container';
            sourcesDiv.innerHTML = '<div class="sources-header">Sources</div>';
            
            const grid = document.createElement('div');
            grid.className = 'sources-grid';
            
            sources.forEach(src => {
                const pill = document.createElement('div');
                pill.className = 'source-pill';
                pill.innerHTML = `
                    <i data-lucide="file-text" size="14"></i>
                    <span>${src.doc_id.substring(0, 15)}...</span>
                `;
                pill.onclick = () => openModal(src);
                grid.appendChild(pill);
            });
            
            sourcesDiv.appendChild(grid);
            messageContent.appendChild(sourcesDiv);
        }
        
        chatFeed.appendChild(messageDiv);
        chatFeed.scrollTop = chatFeed.scrollHeight;
        lucide.createIcons();
    }

    // --- Communication ---
    async function sendMessage() {
        const message = chatInput.value.trim();
        if (!message) return;

        appendMessage('user', message);
        chatInput.value = '';
        chatInput.style.height = 'auto';
        sendBtn.disabled = true;

        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'chat-message ai-message loading-state';
        loadingDiv.innerHTML = `
            <div class="avatar ai-avatar"><i data-lucide="sparkles" class="text-blue"></i></div>
            <div class="message-content">
                <div id="loading-status" class="history-label" style="margin-bottom: 10px; color: var(--accent-blue);">Searching research database...</div>
                <div class="shimmer" style="width: 80%"></div>
                <div class="shimmer" style="width: 60%"></div>
            </div>
        `;
        chatFeed.appendChild(loadingDiv);
        chatFeed.scrollTop = chatFeed.scrollHeight;
        lucide.createIcons();

        try {
            console.log("Fetching chat API...");
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message })
            });

            if (!res.ok) throw new Error(`Server returned status ${res.status}`);
            
            const data = await res.json();
            console.log("API Response received:", data);
            
            loadingDiv.remove();
            
            const finalAnswer = data.answer && data.answer.trim() ? data.answer.trim() : "*[The AI returned an empty response]*";
            appendMessage('ai', finalAnswer, data.sources);
            
            saveToHistory(message, data.answer);
        } catch (error) {
            console.error("Chat error:", error);
            loadingDiv.remove();
            appendMessage('ai', `**Error:** ${error.message}`);
        }
    }

    sendBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // --- History Logic ---
    function saveToHistory(query, answer) {
        const item = { query, answer, id: Date.now() };
        history.unshift(item);
        if (history.length > 15) history.pop();
        localStorage.setItem('nutri_rag_history', JSON.stringify(history));
        renderHistory();
    }

    function renderHistory() {
        historyList.innerHTML = '';
        history.forEach(item => {
            const div = document.createElement('div');
            div.className = 'history-item';
            div.innerText = item.query;
            div.onclick = () => loadHistoryItem(item);
            historyList.appendChild(div);
        });
    }

    function loadHistoryItem(item) {
        chatFeed.innerHTML = '';
        appendMessage('user', item.query);
        appendMessage('ai', item.answer);
    }

    // --- Modal Logic ---
    function openModal(source) {
        // Clean and structure the raw content
        let content = source.content;
        
        // If it contains bullet points, let's make them real lists
        if (content.includes('â€¢')) {
            content = content.split('â€¢').join('\n- ');
        }
        
        modalBody.innerHTML = `
            <div class="source-info" style="margin-bottom: 2rem; padding: 1rem; background: rgba(255,255,255,0.03); border-radius: 12px; font-size: 0.85rem; border: 1px solid var(--border-dim);">
                <div style="display: flex; gap: 2rem;">
                    <div><span style="color: var(--text-dim);">Document ID:</span> <br>${source.doc_id}</div>
                    <div><span style="color: var(--text-dim);">Relevance:</span> <br>${(source.similarity * 100).toFixed(1)}%</div>
                </div>
            </div>
            <div class="prose" style="white-space: pre-wrap;">${marked.parse(content)}</div>
        `;
        modal.classList.remove('hidden');
    }

    function hideModal() {
        modal.classList.add('hidden');
    }

    closeModal.onclick = hideModal;
    document.querySelector('.modal-overlay').onclick = hideModal;

    function updateIcons() {
        // Just refresh lucide
        lucide.createIcons();
    }
});
