// ==========================================================================
// NLP COMPILER STUDIO — Interactive IDE Core Architecture
// High-Reliability Resizing, Contextual Inspector, Voice & Live Execution
// ==========================================================================

window.ideScriptLoaded = true;

if (window.__ideInitialized) {
    console.warn('[IDE] ide.js already initialized, skipping duplicate execution.');
} else {
    window.__ideInitialized = true;
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initIdeApp);
    } else {
        initIdeApp();
    }
}

function initIdeApp() {
    // Pipeline & Session State
    let currentMode = 'nlp';
    let currentSessionId = '';
    let lastCompiledText = '';
    let socket = null;
    let isProcessRunning = false;

    // Presets definitions
    const PRESETS = {
        user_input: {
            title: 'Natural Language Input',
            placeholder: 'Type instructions in natural English...\nExample: Ask the user for two numbers, add them and display the result.',
            code: ""
        },
        add: {
            title: 'Natural Language Input',
            placeholder: 'Type instructions in natural English...',
            code: "Ask the user for two numbers, add them and display the result."
        },
        even_odd: {
            title: 'Natural Language Input',
            placeholder: 'Type instructions in natural English...',
            code: "Ask the user for a number, if the number % 2 == 0 print 1 else print 0"
        },
        loop_sum: {
            title: 'Natural Language Input',
            placeholder: 'Type instructions in natural English...',
            code: "Create an integer sum, create an integer i, for i from 1 to 5, set sum to sum + i, end for, print sum"
        },
        temperature: {
            title: 'Natural Language Input',
            placeholder: 'Type instructions in natural English...',
            code: "Ask the user for c, set f to c * 9 / 5 + 32, print f"
        }
    };

    // DOM Elements - Navigation & Actions
    const editorInput = document.getElementById('editor-input');
    const panelInputTitle = document.getElementById('panel-input-title');
    const btnRun = document.getElementById('btn-run');
    const btnClear = document.getElementById('btn-clear');
    const exampleSelect = document.getElementById('example-select');
    const pipelineStatusBadge = document.getElementById('pipeline-status-badge');
    const pipelineStatusText = document.getElementById('pipeline-status-text');

    // DOM Elements - Code & Explanation
    const viewCCode = document.getElementById('view-c-code');
    const btnCopyC = document.getElementById('btn-copy-c');
    const copyCText = document.getElementById('copy-c-text');
    const btnExplain = document.getElementById('btn-explain');
    const drawerExplain = document.getElementById('drawer-explain');
    const btnCloseExplain = document.getElementById('btn-close-explain');
    const btnGenerateExplain = document.getElementById('btn-generate-explain');
    const btnCancelExplain = document.getElementById('btn-cancel-explain');
    const viewExplain = document.getElementById('view-explain');
    const explainWelcomeState = document.getElementById('explain-welcome-state');
    const explainBodyOutput = document.getElementById('explain-body-output');

    // DOM Elements - Workbench & Inspection
    const workspaceRoot = document.getElementById('workspace');
    const editorRow = document.getElementById('editor-row');
    const panelInput = document.getElementById('panel-input');
    const panelC = document.getElementById('panel-c');
    const resizerH = document.getElementById('resizer-h');
    const resizerWorkbench = document.getElementById('resizer-workbench');
    const workbenchDock = document.getElementById('workbench-dock');
    const btnToggleWorkbench = document.getElementById('btn-toggle-workbench');
    const btnMinimizeDock = document.getElementById('btn-minimize-dock');
    const workbenchTabs = document.querySelectorAll('.workbench-tab-btn');
    const workbenchPanes = document.querySelectorAll('.workbench-pane');

    // Inspection Views
    const viewCompilerLog = document.getElementById('view-compiler-log');
    const viewIntent = document.getElementById('view-intent');
    const viewIl = document.getElementById('view-il');

    // Terminal Elements
    const termDisplay = document.getElementById('term-display');
    const stdinInput = document.getElementById('term-stdin-input');
    const btnSendStdin = document.getElementById('btn-send-stdin');
    const btnKillProc = document.getElementById('btn-kill-proc');

    // Conversational Programming Elements
    const convDock = document.getElementById('conv-dock');
    const convTurnBadge = document.getElementById('conv-turn-badge');
    const btnConvRun = document.getElementById('btn-conv-run');
    const btnConvUndo = document.getElementById('btn-conv-undo');
    const btnConvReset = document.getElementById('btn-conv-reset');
    const convHistoryFeed = document.getElementById('conv-history-feed');
    const convHistoryEmpty = document.getElementById('conv-history-empty');
    const convTurnsStream = document.getElementById('conv-turns-stream');
    const convInput = document.getElementById('conv-input');
    const btnConvVoice = document.getElementById('btn-conv-voice');
    const btnConvSend = document.getElementById('btn-conv-send');

    // Theme Toggle Elements
    const themeToggle = document.getElementById('theme-toggle');

    // ==========================================================================
    // 1. STATUS BADGE MANAGEMENT
    // ==========================================================================
    function setPipelineStatus(state, label) {
        if (!pipelineStatusBadge || !pipelineStatusText) return;
        pipelineStatusBadge.className = `status-badge status-${state}`;
        pipelineStatusText.textContent = label;
    }

    // ==========================================================================
    // 2. THEME SWITCHING (PERSISTENT)
    // ==========================================================================
    if (themeToggle) {
        const savedTheme = localStorage.getItem('app-theme') || 'dark';
        if (savedTheme === 'light') {
            document.body.classList.remove('dark-theme');
            document.body.classList.add('light-theme');
            updateThemeIcon('light');
        } else {
            document.body.classList.remove('light-theme');
            document.body.classList.add('dark-theme');
            updateThemeIcon('dark');
        }

        themeToggle.addEventListener('click', () => {
            const isLight = document.body.classList.toggle('light-theme');
            if (isLight) {
                document.body.classList.remove('dark-theme');
                localStorage.setItem('app-theme', 'light');
                updateThemeIcon('light');
            } else {
                document.body.classList.add('dark-theme');
                localStorage.setItem('app-theme', 'dark');
                updateThemeIcon('dark');
            }
        });
    }

    function updateThemeIcon(theme) {
        if (!themeToggle) return;
        if (theme === 'light') {
            themeToggle.innerHTML = `<svg class="theme-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>`;
            themeToggle.title = "Switch to Dark Mode";
        } else {
            themeToggle.innerHTML = `<svg class="theme-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/></svg>`;
            themeToggle.title = "Switch to Light Mode";
        }
    }

    // ==========================================================================
    // 3. BULLETPROOF POINTER RESIZING ARCHITECTURE (FIX FOR RESIZE BUG)
    // ==========================================================================

    // Horizontal Split Resizer (Left Input <-> Right C Code)
    if (resizerH && panelInput && panelC && editorRow) {
        let isResizingH = false;

        resizerH.addEventListener('pointerdown', (e) => {
            isResizingH = true;
            resizerH.setPointerCapture(e.pointerId);
            resizerH.classList.add('dragging');
            document.body.classList.add('is-resizing');
            document.body.style.cursor = 'col-resize';
            e.preventDefault();
        });

        resizerH.addEventListener('pointermove', (e) => {
            if (!isResizingH) return;
            const containerRect = editorRow.getBoundingClientRect();
            const offsetLeft = e.clientX - containerRect.left;
            const totalWidth = containerRect.width;

            let leftPct = (offsetLeft / totalWidth) * 100;
            // Constrain between 20% and 80%
            if (leftPct < 20) leftPct = 20;
            if (leftPct > 80) leftPct = 80;

            panelInput.style.flex = `0 0 ${leftPct}%`;
            panelC.style.flex = `0 0 ${100 - leftPct}%`;
        });

        const stopHResize = (e) => {
            if (!isResizingH) return;
            isResizingH = false;
            try { resizerH.releasePointerCapture(e.pointerId); } catch (_) {}
            resizerH.classList.remove('dragging');
            document.body.classList.remove('is-resizing');
            document.body.style.cursor = ''; // Cleanly reset inline cursor so hover works repeatedly
        };

        resizerH.addEventListener('pointerup', stopHResize);
        resizerH.addEventListener('pointercancel', stopHResize);
    }

    // Vertical Split Resizer (Top Editors <-> Bottom Workbench Dock)
    if (resizerWorkbench && workbenchDock && workspaceRoot) {
        let isResizingV = false;

        resizerWorkbench.addEventListener('pointerdown', (e) => {
            isResizingV = true;
            resizerWorkbench.setPointerCapture(e.pointerId);
            resizerWorkbench.classList.add('dragging');
            document.body.classList.add('is-resizing');
            document.body.style.cursor = 'row-resize';
            e.preventDefault();
        });

        resizerWorkbench.addEventListener('pointermove', (e) => {
            if (!isResizingV) return;
            const rootRect = workspaceRoot.getBoundingClientRect();
            let newHeight = rootRect.bottom - e.clientY;

            // Clamping reasonable height
            const minH = 40;
            const maxH = rootRect.height - 140;
            if (newHeight < minH) newHeight = minH;
            if (newHeight > maxH) newHeight = maxH;

            // Auto-expand if was collapsed
            if (newHeight > 45 && workbenchDock.classList.contains('collapsed')) {
                setWorkbenchCollapsed(false);
            }

            workbenchDock.style.height = `${newHeight}px`;
        });

        const stopVResize = (e) => {
            if (!isResizingV) return;
            isResizingV = false;
            try { resizerWorkbench.releasePointerCapture(e.pointerId); } catch (_) {}
            resizerWorkbench.classList.remove('dragging');
            document.body.classList.remove('is-resizing');
            document.body.style.cursor = ''; // Cleanly reset inline cursor
        };

        resizerWorkbench.addEventListener('pointerup', stopVResize);
        resizerWorkbench.addEventListener('pointercancel', stopVResize);
    }

    // ==========================================================================
    // 4. WORKBENCH TABS & COLLAPSE CONTROLS
    // ==========================================================================

    function setWorkbenchCollapsed(collapsed) {
        if (!workbenchDock) return;
        if (collapsed) {
            workbenchDock.classList.add('collapsed');
            if (btnToggleWorkbench) btnToggleWorkbench.classList.remove('active');
            if (btnMinimizeDock) {
                btnMinimizeDock.title = 'Expand Console Workbench';
                btnMinimizeDock.setAttribute('aria-expanded', 'false');
            }
        } else {
            workbenchDock.classList.remove('collapsed');
            if (btnToggleWorkbench) btnToggleWorkbench.classList.add('active');
            if (btnMinimizeDock) {
                btnMinimizeDock.title = 'Minimize Console Workbench';
                btnMinimizeDock.setAttribute('aria-expanded', 'true');
            }
            if (parseInt(workbenchDock.style.height || '0') < 100) {
                workbenchDock.style.height = '240px';
            }
        }
    }

    function toggleWorkbenchCollapse() {
        if (!workbenchDock) return;
        const isCollapsed = workbenchDock.classList.contains('collapsed');
        setWorkbenchCollapsed(!isCollapsed);
    }

    function activateWorkbenchTab(tabId) {
        workbenchTabs.forEach(btn => {
            if (btn.getAttribute('data-tab') === tabId) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });

        workbenchPanes.forEach(pane => {
            if (pane.id === tabId) {
                pane.classList.add('active');
            } else {
                pane.classList.remove('active');
            }
        });

        // If collapsed, expand when user clicks a tab
        if (workbenchDock && workbenchDock.classList.contains('collapsed')) {
            setWorkbenchCollapsed(false);
        }
    }

    workbenchTabs.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.getAttribute('data-tab');
            activateWorkbenchTab(tabId);
        });
    });

    if (btnToggleWorkbench) btnToggleWorkbench.addEventListener('click', toggleWorkbenchCollapse);
    if (btnMinimizeDock) btnMinimizeDock.addEventListener('click', toggleWorkbenchCollapse);

    // ==========================================================================
    // 5. PRESETS & INPUT MANAGEMENT
    // ==========================================================================
    if (exampleSelect) {
        exampleSelect.addEventListener('change', (e) => {
            const val = e.target.value;
            const preset = PRESETS[val];
            if (preset) {
                editorInput.value = preset.code;
                if (panelInputTitle) panelInputTitle.textContent = preset.title;
                if (preset.placeholder) editorInput.placeholder = preset.placeholder;
                editorInput.focus();
            }
        });
    }

    if (editorInput) {
        editorInput.addEventListener('input', () => {
            if (exampleSelect && exampleSelect.value !== 'user_input') {
                exampleSelect.value = 'user_input';
            }
        });
    }

    // Clear Workspace
    if (btnClear) {
        btnClear.addEventListener('click', () => {
            editorInput.value = '';
            if (exampleSelect) exampleSelect.value = 'user_input';
            clearPipelineOutputs();
            setPipelineStatus('idle', 'Ready');
            editorInput.focus();
        });
    }

    function clearPipelineOutputs() {
        viewCompilerLog.textContent = 'No compilation run yet. Execute the pipeline to view lexical tokens, parser AST, symbol table addresses, and three-address quadruples.';
        viewIntent.textContent = 'Qwen 2.5 3B structured intent JSON will appear here.';
        viewIl.textContent = 'Intermediate Language instructions (DECLARE, READ, ASSIGN, PRINT) will appear here.';
        viewCCode.textContent = '/* NLP COMPILER — Deterministic Generated C */\n// Click "Run Pipeline" to synthesize C code from natural language.';
        
        renderDrawerWelcome();

        termDisplay.innerHTML = '<div class="term-greeting">Press <strong>"Run Pipeline"</strong> to compile and execute program with live interactive stdin/stdout.</div>';
        stdinInput.value = '';
        stdinInput.disabled = true;
        btnSendStdin.disabled = true;
        if (btnKillProc) btnKillProc.style.display = 'none';

        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.close();
        }
        isProcessRunning = false;
        renderConvHistory([], false);
    }

    // Copy C Code
    if (btnCopyC) {
        btnCopyC.addEventListener('click', () => {
            const code = viewCCode.textContent;
            navigator.clipboard.writeText(code).then(() => {
                if (copyCText) copyCText.textContent = 'Copied!';
                setTimeout(() => { if (copyCText) copyCText.textContent = 'Copy'; }, 1600);
            });
        });
    }

    // ==========================================================================
    // 6. VOICE-TO-CODE (REFINED COMPACT CONTROL)
    // ==========================================================================
    const btnVoice = document.getElementById('btn-voice');
    const voiceLangSelect = document.getElementById('voice-lang-select');
    const voiceLabel = document.getElementById('voice-label');
    let speechRecognitionInstance = null;
    let isVoiceRecording = false;

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (btnVoice) {
        if (!SpeechRecognition) {
            btnVoice.title = "Speech recognition is not natively supported in this browser (Chrome/Edge recommended)";
            btnVoice.addEventListener('click', () => {
                alert("Speech recognition is not supported natively in your current browser.\n\nFor voice-to-code, please open this app in Google Chrome or Microsoft Edge with microphone access permitted.");
            });
        } else {
            btnVoice.addEventListener('click', () => {
                if (isVoiceRecording) {
                    if (speechRecognitionInstance) speechRecognitionInstance.stop();
                    return;
                }
                startSpeechRecognition();
            });
        }
    }

    function startSpeechRecognition() {
        try {
            speechRecognitionInstance = new SpeechRecognition();
            const langCode = voiceLangSelect ? voiceLangSelect.value : 'en-US';
            speechRecognitionInstance.lang = langCode;
            speechRecognitionInstance.continuous = false;
            speechRecognitionInstance.interimResults = true;
            speechRecognitionInstance.maxAlternatives = 1;

            let existingText = editorInput.value;
            let textPrefix = existingText;
            if (textPrefix.length > 0 && !/\s$/.test(textPrefix)) {
                textPrefix += ' ';
            }

            speechRecognitionInstance.onstart = () => {
                isVoiceRecording = true;
                btnVoice.classList.add('recording');
                if (voiceLabel) voiceLabel.textContent = 'Stop';
                btnVoice.title = "Listening... Speak your programming instructions (click to stop)";
                setPipelineStatus('running', `Listening [${langCode}]`);
            };

            speechRecognitionInstance.onresult = (event) => {
                let currentTranscript = '';
                for (let i = event.resultIndex; i < event.results.length; ++i) {
                    currentTranscript += event.results[i][0].transcript;
                }
                // Transcription only fills the input; NEVER auto-compiles or auto-runs
                editorInput.value = textPrefix + currentTranscript;
                if (exampleSelect && exampleSelect.value !== 'user_input') {
                    exampleSelect.value = 'user_input';
                }
            };

            speechRecognitionInstance.onerror = (event) => {
                console.warn('Speech recognition error event:', event.error);
                let message = `Voice recognition notice: ${event.error}`;
                if (event.error === 'network') {
                    message = "Speech recognition network notice:\n\nIf you are using Brave Browser, Google cloud speech services are blocked by default.\n\nYou can enable 'Use Google services for speech recognition' in Brave Settings (brave://settings/privacy) or open the application in Google Chrome.";
                } else if (event.error === 'not-allowed') {
                    message = "Microphone access was denied. Please allow microphone permissions in your browser address bar.";
                } else if (event.error === 'no-speech') {
                    message = "No speech was detected. Click Speak to try again.";
                }
                alert(message);
                stopSpeechUI();
            };

            speechRecognitionInstance.onend = () => {
                stopSpeechUI();
                setPipelineStatus('idle', 'Ready');
            };

            speechRecognitionInstance.start();
        } catch (err) {
            console.error('Speech recognition error:', err);
            alert(`Could not start speech recognition: ${err.message}`);
            stopSpeechUI();
        }
    }

    function stopSpeechUI() {
        isVoiceRecording = false;
        if (btnVoice) {
            btnVoice.classList.remove('recording');
            if (voiceLabel) voiceLabel.textContent = 'Speak';
            btnVoice.title = "Click to speak natural language instructions";
        }
    }

    // ==========================================================================
    // 7. CONTEXTUAL BILINGUAL CODE EXPLANATION (TWO-STAGE CONFIRMATION FLOW)
    // ==========================================================================

    const LANG_DISPLAY = {
        english: 'English (Technical Breakdown)',
        hindi: 'Hindi (हिंदी)',
        tamil: 'Tamil (தமிழ்)',
        telugu: 'Telugu (తెలుగు)'
    };

    function hasGeneratedCCode() {
        const code = viewCCode ? viewCCode.textContent.trim() : '';
        if (!code) return false;
        if (code.includes('Click "Run Pipeline" to synthesize C code')) return false;
        return code.length > 20 && (code.includes('main') || code.includes('#include') || code.includes('{'));
    }

    function openExplanationDrawer() {
        if (!drawerExplain) return;
        drawerExplain.classList.add('open');
        drawerExplain.setAttribute('aria-hidden', 'false');
    }

    function closeExplanationDrawer() {
        if (!drawerExplain) return;
        drawerExplain.classList.remove('open');
        drawerExplain.setAttribute('aria-hidden', 'true');
    }

    if (btnCloseExplain) {
        btnCloseExplain.addEventListener('click', closeExplanationDrawer);
    }

    if (btnCancelExplain) {
        btnCancelExplain.addEventListener('click', () => {
            closeExplanationDrawer();
        });
    }

    // Close on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && drawerExplain && drawerExplain.classList.contains('open')) {
            closeExplanationDrawer();
        }
        // Ctrl+Enter or Cmd+Enter to Run Pipeline
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            btnRun.click();
        }
    });

    function getSelectedExplanationLanguage() {
        const checkedRadio = document.querySelector('input[name="explain-lang"]:checked');
        return checkedRadio ? checkedRadio.value : 'english';
    }

    function renderDrawerWelcome() {
        if (!viewExplain) return;
        viewExplain.innerHTML = `
            <div class="explain-empty-state">
                <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="36" height="36" style="width:36px;height:36px;max-width:36px;max-height:36px;display:inline-block;vertical-align:middle;flex-shrink:0;"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>
                <p>Select your preferred language above and click <strong>Generate Explanation</strong> to synthesize a beginner-friendly, 4-point breakdown of this C program.</p>
            </div>
        `;
    }

    function renderDrawerNoCodeWarning() {
        if (!viewExplain) return;
        viewExplain.innerHTML = `
            <div class="explain-empty-state" style="padding: 2.5rem 1.25rem;">
                <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="38" height="38" style="color:var(--accent-amber);width:38px;height:38px;max-width:38px;max-height:38px;display:inline-block;vertical-align:middle;flex-shrink:0;"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                <p style="font-weight:700;font-size:1.05rem;color:var(--text-primary);margin-top:0.4rem;">No Generated C Code Found</p>
                <p style="font-size:0.92rem;color:var(--text-secondary);line-height:1.6;max-width:380px;">Please click <strong>"Run Pipeline"</strong> first to compile natural language instructions into C code. Once generated, you can explain it in English, Hindi, Tamil, or Telugu.</p>
            </div>
        `;
    }

    let explainTimerInterval = null;

    function renderDrawerLoading(langName) {
        if (!viewExplain) return;
        let elapsed = 0;
        viewExplain.innerHTML = `
            <div class="explain-loading">
                <div class="explain-spinner"></div>
                <span>Analyzing C code in <strong>${langName}</strong> with Qwen 2.5 3B...</span>
                <span id="explain-timer-label" class="explain-timer-text">Synthesizing explanation (0s)</span>
            </div>
        `;
        if (explainTimerInterval) clearInterval(explainTimerInterval);
        explainTimerInterval = setInterval(() => {
            elapsed++;
            const timerLabel = document.getElementById('explain-timer-label');
            if (timerLabel) {
                timerLabel.textContent = `Synthesizing explanation (${elapsed}s)`;
            }
        }, 1000);
    }

    function renderDrawerResult(langName, markdownText) {
        if (explainTimerInterval) {
            clearInterval(explainTimerInterval);
            explainTimerInterval = null;
        }
        if (!viewExplain) return;
        viewExplain.innerHTML = `
            <div class="explanation-active-pill">
                <span class="active-dot"></span>
                <span>Active Explanation: <strong>${langName}</strong></span>
            </div>
            <div class="explanation-markdown-body">
                ${renderMarkdown(markdownText)}
            </div>
        `;
    }

    function renderDrawerError(errorText) {
        if (explainTimerInterval) {
            clearInterval(explainTimerInterval);
            explainTimerInterval = null;
        }
        if (!viewExplain) return;
        viewExplain.innerHTML = `
            <div class="explain-error-card">
                <strong>Explanation Unavailable</strong>
                <p style="margin-top:0.4rem;line-height:1.6;">${errorText || 'Failed to synthesize code explanation. Ensure Ollama is running.'}</p>
            </div>
        `;
    }

    // STAGE 1: User clicks "Explain Code" in the header
    // Opens the drawer showing language options. DOES NOT call the backend!
    if (btnExplain) {
        btnExplain.addEventListener('click', () => {
            // Automatically collapse/hide the console workbench when explaining code
            setWorkbenchCollapsed(true);

            openExplanationDrawer();
            if (!hasGeneratedCCode()) {
                renderDrawerNoCodeWarning();
                if (btnGenerateExplain) btnGenerateExplain.disabled = true;
            } else {
                if (btnGenerateExplain) btnGenerateExplain.disabled = false;
                // If drawer is currently showing warning or is empty, show welcome state
                if (!viewExplain || !viewExplain.querySelector('.explanation-markdown-body')) {
                    renderDrawerWelcome();
                }
            }
        });
    }

    // STAGE 2: User clicks "Generate Explanation" after selecting language
    // Reads currently displayed C code, sends to backend, displays result
    if (btnGenerateExplain) {
        btnGenerateExplain.addEventListener('click', async () => {
            if (!hasGeneratedCCode()) {
                renderDrawerNoCodeWarning();
                btnGenerateExplain.disabled = true;
                return;
            }

            const code = viewCCode.textContent.trim();
            const lang = getSelectedExplanationLanguage();
            const langName = LANG_DISPLAY[lang] || lang;

            btnGenerateExplain.disabled = true;
            renderDrawerLoading(langName);

            try {
                const response = await fetch('/api/explain', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        c_code: code,
                        language: lang
                    })
                });

                const data = await response.json();

                if (data.success && data.explanation) {
                    renderDrawerResult(langName, data.explanation);
                } else {
                    renderDrawerError(data.error || 'Failed to generate code explanation.');
                }
            } catch (err) {
                renderDrawerError(`Network connection error: ${err.message}`);
            } finally {
                btnGenerateExplain.disabled = false;
            }
        });
    }

    // Markdown Parser for Code Explanations
    function renderMarkdown(md) {
        if (!md) return '';
        let text = md
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');

        // Fenced code blocks
        text = text.replace(/```(?:c|C)?\n([\s\S]*?)```/g, '<pre class="code-editor-view" style="margin:0.5rem 0;padding:0.75rem;border-radius:4px;">$1</pre>');
        // Inline code `...`
        text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
        // Bold **...**
        text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

        const lines = text.split('\n');
        let html = '';
        let inList = false;

        for (let line of lines) {
            const trimmed = line.trim();
            if (!trimmed) {
                if (inList) { html += '</ul>'; inList = false; }
                continue;
            }

            if (trimmed.startsWith('### ')) {
                if (inList) { html += '</ul>'; inList = false; }
                html += `<h4>${trimmed.slice(4)}</h4>`;
            } else if (trimmed.startsWith('## ') || trimmed.startsWith('# ')) {
                if (inList) { html += '</ul>'; inList = false; }
                const levelText = trimmed.replace(/^#+\s*/, '');
                html += `<h3>${levelText}</h3>`;
            } else if (trimmed.startsWith('* ') || trimmed.startsWith('- ')) {
                if (!inList) { html += '<ul>'; inList = true; }
                html += `<li>${trimmed.slice(2)}</li>`;
            } else if (trimmed.startsWith('<pre') || trimmed.endsWith('</pre>')) {
                if (inList) { html += '</ul>'; inList = false; }
                html += trimmed;
            } else {
                if (inList) { html += '</ul>'; inList = false; }
                html += `<p>${trimmed}</p>`;
            }
        }
        if (inList) html += '</ul>';
        return html;
    }

    // ==========================================================================
    // 8. COMPILER PIPELINE TRANSACTION & EXECUTION
    // ==========================================================================

    btnRun.addEventListener('click', async () => {
        const content = editorInput.value.trim();
        if (!content) {
            alert('Please type or speak natural language instructions before running.');
            editorInput.focus();
            return;
        }

        // If the current program is already compiled and up to date, execute it directly in the terminal
        if (currentSessionId && content === lastCompiledText && viewCCode.textContent.trim()) {
            setPipelineStatus('success', 'Executing');
            activateWorkbenchTab('tab-term');
            startLiveTerminal(currentSessionId);
            return;
        }

        currentSessionId = 'sess_' + Math.random().toString(36).substring(2, 10);
        clearPipelineOutputs();

        setPipelineStatus('running', 'Compiling...');
        btnRun.disabled = true;

        try {
            const resp = await fetch('/api/compile', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    mode: currentMode,
                    content: content,
                    session_id: currentSessionId
                })
            });

            const data = await resp.json();

            if (!data.success) {
                setPipelineStatus('error', `Error [${data.stage}]`);
                if (data.compiler_log) viewCompilerLog.textContent = data.compiler_log;
                if (data.intent) viewIntent.textContent = JSON.stringify(data.intent, null, 2);
                if (data.il_code) viewIl.textContent = data.il_code;
                activateWorkbenchTab('tab-stages-log');
                btnRun.disabled = false;
                return;
            }

            // Sync session ID & last compiled text
            currentSessionId = data.session_id || currentSessionId;
            lastCompiledText = content;

            // Populate all inspector panels
            setPipelineStatus('success', 'Executing');
            if (data.intent) viewIntent.textContent = JSON.stringify(data.intent, null, 2);
            viewIl.textContent = data.il_code || '';
            viewCompilerLog.textContent = data.compiler_log || '';
            viewCCode.textContent = data.c_code || '';
            if (btnGenerateExplain) btnGenerateExplain.disabled = false;
            if (btnConvRun) btnConvRun.disabled = false;
            if (drawerExplain && drawerExplain.classList.contains('open')) {
                renderDrawerWelcome();
            }

            // Sync conversational programming turn stream
            if (data.history) {
                renderConvHistory(data.history, data.can_undo);
            }

            activateWorkbenchTab('tab-term');
            startLiveTerminal(currentSessionId);

        } catch (err) {
            setPipelineStatus('error', 'Failed');
            alert(`Compilation transaction failed: ${err.message}`);
        } finally {
            btnRun.disabled = false;
        }
    });

    // ==========================================================================
    // 9. LIVE WEBSOCKET TERMINAL INTERACTION
    // ==========================================================================

    function startLiveTerminal(sessionId) {
        termDisplay.innerHTML = '';
        appendTermOutput('system', `=== PROGRAM SUBPROCESS INITIALIZED [${sessionId}] ===\n`);
        
        stdinInput.disabled = false;
        btnSendStdin.disabled = false;
        if (btnKillProc) btnKillProc.style.display = 'inline-flex';
        stdinInput.focus();
        isProcessRunning = true;

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/exec/${sessionId}`;
        
        socket = new WebSocket(wsUrl);

        socket.onmessage = (event) => {
            const msg = JSON.parse(event.data);
            if (msg.type === 'stdout') {
                appendTermOutput('stdout', msg.data);
            } else if (msg.type === 'stderr') {
                appendTermOutput('stderr', msg.data);
            } else if (msg.type === 'exit') {
                appendTermOutput('system', `\n[Process terminated: exit code ${msg.exit_code}]\n`);
                endSession();
            } else if (msg.type === 'error') {
                appendTermOutput('stderr', `\n[Execution Error: ${msg.message}]\n`);
                endSession();
            }
        };

        socket.onerror = () => {
            appendTermOutput('stderr', '\n[Terminal connection error]\n');
            endSession();
        };

        socket.onclose = () => {
            if (isProcessRunning) {
                endSession();
            }
        };
    }

    function appendTermOutput(type, text) {
        const last = termDisplay.lastElementChild;
        if (last && last.classList.contains(`term-out-${type}`)) {
            last.textContent += text;
        } else {
            const span = document.createElement('span');
            span.className = `term-out-${type}`;
            span.textContent = text;
            termDisplay.appendChild(span);
        }
        termDisplay.scrollTop = termDisplay.scrollHeight;
    }

    function sendStdin() {
        const val = stdinInput.value;
        if (!socket || socket.readyState !== WebSocket.OPEN) return;
        
        appendTermOutput('stdin', val + '\n');
        socket.send(JSON.stringify({ type: 'stdin', data: val }));
        stdinInput.value = '';
    }

    stdinInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') sendStdin();
    });
    btnSendStdin.addEventListener('click', sendStdin);

    if (btnKillProc) {
        btnKillProc.addEventListener('click', () => {
            if (socket && socket.readyState === WebSocket.OPEN) {
                socket.send(JSON.stringify({ type: 'kill' }));
            }
            endSession();
        });
    }

    function endSession() {
        isProcessRunning = false;
        stdinInput.disabled = true;
        btnSendStdin.disabled = true;
        if (btnKillProc) btnKillProc.style.display = 'none';
        setPipelineStatus('idle', 'Ready');
    }

    // ==========================================================================
    // 10. CONVERSATIONAL PROGRAMMING CONTROLLER
    // ==========================================================================

    function escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function renderConvHistory(history, canUndo) {
        if (btnConvUndo) {
            btnConvUndo.disabled = !canUndo;
        }

        if (!convTurnsStream || !convHistoryFeed) return;

        if (!history || history.length === 0) {
            if (convHistoryEmpty) convHistoryEmpty.style.display = 'block';
            convTurnsStream.style.display = 'none';
            convTurnsStream.innerHTML = '';
            if (convTurnBadge) convTurnBadge.style.display = 'none';
            return;
        }

        if (convHistoryEmpty) convHistoryEmpty.style.display = 'none';
        convTurnsStream.style.display = 'block';

        let userTurnCount = 0;
        let html = '';

        history.forEach((turn) => {
            const role = turn.role || 'user';
            const text = turn.text || '';
            const diff = turn.diff || '';
            const success = turn.success !== false;

            if (role === 'user') {
                userTurnCount++;
                html += `
                    <div class="conv-turn-chip">
                        <span class="conv-turn-tag user">Turn ${userTurnCount}</span>
                        <span class="conv-turn-text">${escapeHtml(text)}</span>
                    </div>
                `;
            } else {
                let tagClass = 'assistant';
                let tagLabel = 'Updated';

                if (diff === 'Clarification' || turn.status === 'clarification') {
                    tagClass = 'clarify';
                    tagLabel = 'Clarify';
                } else if (diff === 'Unsupported' || diff === 'Validation Error' || diff === 'Compiler Error' || !success) {
                    tagClass = 'error';
                    tagLabel = 'Notice';
                }

                let diffBadge = '';
                if (diff && diff !== 'Clarification' && diff !== 'Initial Program' && success) {
                    diffBadge = `<span class="conv-diff-pill">${escapeHtml(diff)}</span>`;
                }

                html += `
                    <div class="conv-turn-chip">
                        <span class="conv-turn-tag ${tagClass}">${tagLabel}</span>
                        <span class="conv-turn-text">${escapeHtml(text)} ${diffBadge}</span>
                    </div>
                `;
            }
        });

        convTurnsStream.innerHTML = html;
        if (convTurnBadge) {
            convTurnBadge.style.display = userTurnCount > 0 ? 'inline-block' : 'none';
            convTurnBadge.textContent = `Turn ${userTurnCount}`;
        }
        convHistoryFeed.scrollTop = convHistoryFeed.scrollHeight;
    }

    async function submitConvUpdate() {
        if (!convInput) return;
        const text = convInput.value.trim();
        if (!text) {
            convInput.focus();
            return;
        }

        if (!currentSessionId) {
            const mainPrompt = editorInput.value.trim();
            if (!mainPrompt) {
                editorInput.value = text;
                convInput.value = '';
                btnRun.click();
                return;
            } else {
                setPipelineStatus('running', 'Compiling initial program...');
                currentSessionId = 'sess_' + Math.random().toString(36).substring(2, 10);
                try {
                    const resp = await fetch('/api/compile', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            mode: currentMode,
                            content: mainPrompt,
                            session_id: currentSessionId
                        })
                    });
                    const data = await resp.json();
                    if (!data.success) {
                        setPipelineStatus('error', `Error [${data.stage}]`);
                        if (data.compiler_log) viewCompilerLog.textContent = data.compiler_log;
                        activateWorkbenchTab('tab-stages-log');
                        return;
                    }
                    currentSessionId = data.session_id || currentSessionId;
                    lastCompiledText = mainPrompt;
                    if (data.intent) viewIntent.textContent = JSON.stringify(data.intent, null, 2);
                    viewIl.textContent = data.il_code || '';
                    viewCompilerLog.textContent = data.compiler_log || '';
                    viewCCode.textContent = data.c_code || '';
                    if (btnConvRun) btnConvRun.disabled = false;
                } catch (e) {
                    alert(`Initial compilation failed: ${e.message}`);
                    return;
                }
            }
        }

        convInput.disabled = true;
        if (btnConvSend) btnConvSend.disabled = true;
        if (btnConvVoice) btnConvVoice.disabled = true;

        if (convTurnsStream) {
            if (convHistoryEmpty) convHistoryEmpty.style.display = 'none';
            convTurnsStream.style.display = 'block';
            convTurnsStream.innerHTML += `
                <div class="conv-turn-chip temp-chip">
                    <span class="conv-turn-tag user">User</span>
                    <span class="conv-turn-text">${escapeHtml(text)}</span>
                </div>
                <div class="conv-turn-chip temp-chip">
                    <span class="conv-turn-tag assistant">Compiling</span>
                    <span class="conv-turn-text" style="color:var(--text-muted);font-style:italic;">Synthesizing candidate intent & verifying compiler pipeline...</span>
                </div>
            `;
            convHistoryFeed.scrollTop = convHistoryFeed.scrollHeight;
        }

        setPipelineStatus('running', 'Modifying...');

        try {
            const resp = await fetch('/api/conversation/update', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: currentSessionId,
                    message: text
                })
            });

            const data = await resp.json();

            if (data.history) {
                renderConvHistory(data.history, data.can_undo);
            }

            if (data.success) {
                if (data.c_code) viewCCode.textContent = data.c_code;
                if (data.il_code) viewIl.textContent = data.il_code;
                if (data.intent) viewIntent.textContent = JSON.stringify(data.intent, null, 2);
                if (data.compiler_log) viewCompilerLog.textContent = data.compiler_log;
                if (btnConvRun) btnConvRun.disabled = false;

                if (data.status === 'explanation') {
                    setPipelineStatus('idle', 'Explained');
                    if (data.explanation) {
                        openExplanationDrawer();
                        renderDrawerResult('English', data.explanation);
                    }
                } else {
                    setPipelineStatus('idle', 'Updated & Built');
                    if (editorInput.value.trim()) {
                        editorInput.value = editorInput.value.trim() + '\n' + text;
                    } else {
                        editorInput.value = text;
                    }
                    lastCompiledText = editorInput.value.trim();

                    if (drawerExplain && drawerExplain.classList.contains('open')) {
                        renderDrawerWelcome();
                    }

                    // Auto-launch interactive terminal with the updated binary
                    activateWorkbenchTab('tab-term');
                    startLiveTerminal(currentSessionId);
                }

                convInput.value = '';
                convInput.placeholder = "Ask follow-up (e.g. 'Also print their difference', 'Rename to total', 'Undo')...";
            } else {
                if (data.status === 'clarification') {
                    setPipelineStatus('idle', 'Clarify');
                    convInput.placeholder = data.message || "Please clarify your request...";
                    convInput.value = '';
                } else if (data.status === 'unsupported') {
                    setPipelineStatus('idle', 'Unsupported');
                } else {
                    setPipelineStatus('error', 'Update Rejected');
                    if (data.compiler_log) {
                        viewCompilerLog.textContent = data.compiler_log;
                        activateWorkbenchTab('tab-stages-log');
                    }
                }
            }
        } catch (err) {
            setPipelineStatus('error', 'Network Error');
            alert(`Conversational update failed: ${err.message}`);
        } finally {
            convInput.disabled = false;
            if (btnConvSend) btnConvSend.disabled = false;
            if (btnConvVoice) btnConvVoice.disabled = false;
            convInput.focus();
        }
    }

    async function triggerConvUndo() {
        if (!currentSessionId || (btnConvUndo && btnConvUndo.disabled)) return;

        btnConvUndo.disabled = true;
        setPipelineStatus('running', 'Reverting...');

        try {
            const resp = await fetch('/api/conversation/undo', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: currentSessionId })
            });
            const data = await resp.json();

            if (data.success) {
                if (data.c_code) viewCCode.textContent = data.c_code;
                if (data.il_code) viewIl.textContent = data.il_code;
                if (data.intent) viewIntent.textContent = JSON.stringify(data.intent, null, 2);
                if (data.compiler_log) viewCompilerLog.textContent = data.compiler_log;
                if (data.history) {
                    renderConvHistory(data.history, data.can_undo);
                    const userPrompts = data.history.filter(h => h.sender === 'user').map(h => h.text);
                    if (userPrompts.length > 0) {
                        editorInput.value = userPrompts.join('\n');
                        lastCompiledText = editorInput.value.trim();
                    }
                }
                if (btnConvRun) btnConvRun.disabled = false;
                setPipelineStatus('idle', 'Undone');
            } else {
                alert(data.error || 'Undo failed.');
                setPipelineStatus('idle', 'Ready');
            }
        } catch (err) {
            alert(`Undo failed: ${err.message}`);
            setPipelineStatus('idle', 'Ready');
        }
    }

    async function triggerConvReset() {
        if (currentSessionId) {
            try {
                await fetch('/api/conversation/reset', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ session_id: currentSessionId })
                });
            } catch (e) {
                // non-fatal
            }
        }

        currentSessionId = '';
        lastCompiledText = '';
        if (btnConvRun) btnConvRun.disabled = true;
        renderConvHistory([], false);
        clearPipelineOutputs();
        editorInput.value = '';
        if (exampleSelect) exampleSelect.value = 'user_input';
        setPipelineStatus('idle', 'Ready for new program');
        editorInput.focus();
    }

    // Conversational Mic Voice Support
    let isConvVoiceRecording = false;
    let convSpeechRecognition = null;

    if (btnConvVoice) {
        if (!SpeechRecognition) {
            btnConvVoice.title = "Speech recognition is not supported in this browser";
            btnConvVoice.addEventListener('click', () => {
                alert("Speech recognition is not supported natively in your current browser (Chrome/Edge recommended).");
            });
        } else {
            btnConvVoice.addEventListener('click', () => {
                if (isConvVoiceRecording) {
                    if (convSpeechRecognition) convSpeechRecognition.stop();
                    return;
                }
                startConvSpeechRecognition();
            });
        }
    }

    function startConvSpeechRecognition() {
        try {
            convSpeechRecognition = new SpeechRecognition();
            const langCode = voiceLangSelect ? voiceLangSelect.value : 'en-US';
            convSpeechRecognition.lang = langCode;
            convSpeechRecognition.continuous = false;
            convSpeechRecognition.interimResults = true;
            convSpeechRecognition.maxAlternatives = 1;

            convSpeechRecognition.onstart = () => {
                isConvVoiceRecording = true;
                btnConvVoice.classList.add('recording');
                btnConvVoice.title = "Listening to follow-up instruction (click to stop)...";
            };

            convSpeechRecognition.onresult = (event) => {
                let currentTranscript = '';
                for (let i = event.resultIndex; i < event.results.length; ++i) {
                    currentTranscript += event.results[i][0].transcript;
                }
                convInput.value = currentTranscript;
            };

            convSpeechRecognition.onerror = (event) => {
                console.warn('Conv voice error:', event.error);
                isConvVoiceRecording = false;
                btnConvVoice.classList.remove('recording');
            };

            convSpeechRecognition.onend = () => {
                isConvVoiceRecording = false;
                btnConvVoice.classList.remove('recording');
                btnConvVoice.title = "Speak follow-up instruction";
                convInput.focus();
            };

            convSpeechRecognition.start();
        } catch (e) {
            console.error('Failed to start speech recognition for conversational input:', e);
            isConvVoiceRecording = false;
            btnConvVoice.classList.remove('recording');
        }
    }

    if (btnConvRun) {
        btnConvRun.addEventListener('click', () => {
            if (!currentSessionId) {
                const text = editorInput.value.trim();
                if (text) {
                    btnRun.click();
                } else {
                    alert('Please write instructions or ask a prompt before running.');
                    editorInput.focus();
                }
                return;
            }
            activateWorkbenchTab('tab-term');
            startLiveTerminal(currentSessionId);
        });
    }

    if (btnConvSend) {
        btnConvSend.addEventListener('click', submitConvUpdate);
    }
    if (convInput) {
        convInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                submitConvUpdate();
            }
        });
    }
    if (btnConvUndo) {
        btnConvUndo.addEventListener('click', triggerConvUndo);
    }
    if (btnConvReset) {
        btnConvReset.addEventListener('click', triggerConvReset);
    }

    // Default initialization
    exampleSelect.value = 'user_input';
    currentMode = 'nlp';
    editorInput.value = '';
    editorInput.placeholder = PRESETS.user_input.placeholder;
    editorInput.focus();
}

