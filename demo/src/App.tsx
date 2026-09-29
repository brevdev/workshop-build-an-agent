import { useState, useCallback, useEffect, useRef } from 'react';
import { DndContext, DragOverlay } from '@dnd-kit/core';
import type { DragEndEvent, DragStartEvent } from '@dnd-kit/core';
import { motion, AnimatePresence } from 'framer-motion';
import { skills as allSkills, type Skill } from './data/skills';
import { models, type ModelDef } from './data/models';
import { createAgentSession, deleteAgentSession, getAvailableModels, type AgentSessionInfo } from './api/agent';
import { useBlockyBits, type UseBlockyBitsResult } from './hooks/useBlockyBits';
import { SoulPicker } from './components/SoulPicker';
import { SkillPalette } from './components/SkillPalette';
import { AgentBuilder } from './components/AgentBuilder';
import { BuildButton } from './components/BuildButton';
import { BuildAnimation } from './components/BuildAnimation';
import { ParticleBackground } from './components/ParticleBackground';
import { ChatSection } from './components/ChatSection';
import { SkillCard } from './components/SkillCard';
import { SettingsPanel } from './components/SettingsPanel';
import './App.css';

type Phase = 'soul' | 'builder' | 'building' | 'chat';
type InputMode = 'website' | 'visual';

function App() {
  const [phase, setPhase] = useState<Phase>('soul');
  const [inputMode, setInputMode] = useState<InputMode>('website');
  const [selectedModel, setSelectedModel] = useState<ModelDef | null>(null);
  const [addedSkills, setAddedSkills] = useState<Skill[]>([]);
  const [activeSkill, setActiveSkill] = useState<Skill | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sandboxMap, setSandboxMap] = useState<Record<string, boolean>>({});
  const [sandboxMode, setSandboxMode] = useState(false);
  // Actual sandbox state reported by the backend at build time (null until a
  // session is built). Drives the header badge so it never claims isolation
  // that failed to start.
  const [sandboxStatus, setSandboxStatus] = useState<{ requested: boolean; active: boolean } | null>(null);
  const [showSandboxInfo, setShowSandboxInfo] = useState(false);
  const [showSandboxWarning, setShowSandboxWarning] = useState(false);
  const [sessionReady, setSessionReady] = useState(false);
  const [isExtendedBuild, setIsExtendedBuild] = useState(false);
  const [availableModels, setAvailableModels] = useState<ModelDef[]>([]);
  const [modelError, setModelError] = useState<string | null>(null);
  const [buildError, setBuildError] = useState<string | null>(null);
  const [sessionInfo, setSessionInfo] = useState<AgentSessionInfo | null>(null);
  const buildGeneration = useRef(0);
  const modalRef = useRef<HTMLDivElement>(null);
  const ragInitializedRef = useRef(false);

  const loadModels = useCallback(async () => {
    try {
      const configured = await getAvailableModels();
      setAvailableModels(configured.flatMap(item => {
        const style = models.find(model => model.id === item.id);
        return style ? [{ ...style, name: item.name, backendModel: item.model }] : [];
      }));
      setModelError(null);
    } catch (error) {
      setModelError(error instanceof Error ? error.message : 'Could not load models. Try again.');
    }
  }, []);
  useEffect(() => {
    let active = true;
    getAvailableModels().then(configured => {
      if (!active) return;
      setAvailableModels(configured.flatMap(item => {
        const style = models.find(model => model.id === item.id);
        return style ? [{ ...style, name: item.name, backendModel: item.model }] : [];
      }));
    }).catch(error => { if (active) setModelError(error.message); });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    if (!showSandboxInfo && !showSandboxWarning) return;
    const previous = document.activeElement as HTMLElement | null;
    const focusable = () => Array.from(modalRef.current?.querySelectorAll<HTMLElement>('button, a[href]') ?? []);
    focusable()[0]?.focus();
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') { setShowSandboxInfo(false); setShowSandboxWarning(false); }
      if (event.key === 'Tab') {
        const items = focusable();
        const first = items[0], last = items[items.length - 1];
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
      }
    };
    document.addEventListener('keydown', onKey);
    return () => { document.removeEventListener('keydown', onKey); previous?.focus(); };
  }, [showSandboxInfo, showSandboxWarning]);

  const prevBlockySkillsRef = useRef<string>('');
  const prevBlockyModelRef = useRef<string | null>(null);
  const handleBlockyUpdate = useCallback((state: UseBlockyBitsResult) => {
    if (!state.connected) return;
    if (phase === 'soul' && state.modelId !== prevBlockyModelRef.current) {
      const model = availableModels.find(item => item.id === state.modelId);
      if (model) {
        prevBlockyModelRef.current = state.modelId;
        setSelectedModel(model);
        setPhase('builder');
      }
    }
    if (phase !== 'builder') return;
    const key = [...state.skillIds].sort().join(',');
    if (key === prevBlockySkillsRef.current) return;
    prevBlockySkillsRef.current = key;
    const detected = allSkills.filter(skill => state.skillIds.includes(skill.id));
    setAddedSkills(previous => [...previous, ...detected.filter(skill => !previous.some(item => item.id === skill.id))]);
    if (sandboxMode) setSandboxMap(previous => ({ ...previous,
      ...Object.fromEntries(detected.filter(skill => skill.sandboxable).map(skill => [skill.id, true])),
    }));
  }, [phase, availableModels, sandboxMode]);
  const blocky = useBlockyBits(inputMode === 'visual' && (phase === 'soul' || phase === 'builder'), handleBlockyUpdate);

  // Apply accent color CSS variables when model changes
  useEffect(() => {
    const root = document.documentElement;
    if (selectedModel) {
      root.style.setProperty('--accent-color', selectedModel.primaryColor);
      root.style.setProperty('--accent-light', selectedModel.accentColor);
      root.style.setProperty('--accent-glow', selectedModel.glowColor);
      root.style.setProperty('--accent-subtle', selectedModel.subtleColor);
    } else {
      root.style.setProperty('--accent-color', '#76B900');
      root.style.setProperty('--accent-light', '#8dc63f');
      root.style.setProperty('--accent-glow', 'rgba(118, 185, 0, 0.4)');
      root.style.setProperty('--accent-subtle', 'rgba(118, 185, 0, 0.1)');
    }
  }, [selectedModel]);

  const handleSoulSelect = useCallback((model: ModelDef) => {
    setSelectedModel(model);
    setPhase('builder');
  }, []);

  const handleDragStart = useCallback((event: DragStartEvent) => {
    const skill = allSkills.find(s => s.id === event.active.id);
    if (skill) setActiveSkill(skill);
  }, []);

  const handleDragEnd = useCallback((event: DragEndEvent) => {
    setActiveSkill(null);
    const { active, over } = event;
    if (over?.id === 'agent-dropzone') {
      const skill = allSkills.find(s => s.id === active.id);
      if (skill && !addedSkills.find(s => s.id === skill.id)) {
        setAddedSkills(prev => [...prev, skill]);
        // Auto-sandbox new sandboxable skills when sandbox mode is ON
        if (sandboxMode && skill.sandboxable) {
          setSandboxMap(prev => ({ ...prev, [skill.id]: true }));
        }
      }
    }
  }, [addedSkills, sandboxMode]);

  const handleRemoveSkill = useCallback((skillId: string) => {
    setAddedSkills(prev => prev.filter(s => s.id !== skillId));
    setSandboxMap(prev => { const next = { ...prev }; delete next[skillId]; return next; });
  }, []);

  const handleAddSkill = useCallback((id: string) => {
    const skill = allSkills.find(item => item.id === id);
    if (!skill || phase !== 'builder') return;
    setAddedSkills(previous => previous.some(item => item.id === id) ? previous : [...previous, skill]);
    if (sandboxMode && skill.sandboxable) setSandboxMap(previous => ({ ...previous, [id]: true }));
  }, [phase, sandboxMode]);

  const handleToggleSandboxMode = useCallback(() => {
    if (!sandboxMode) {
      setShowSandboxInfo(true);
    } else {
      setShowSandboxWarning(true);
    }
  }, [sandboxMode]);

  const handleConfirmDisableSandbox = useCallback(() => {
    setSandboxMode(false);
    setSandboxMap({});
    setShowSandboxWarning(false);
  }, []);

  const handleConfirmSandboxMode = useCallback(() => {
    setSandboxMode(true);
    setShowSandboxInfo(false);
    // Auto-sandbox all sandboxable tools that are already added
    const newMap: Record<string, boolean> = {};
    addedSkills.forEach(s => { if (s.sandboxable) newMap[s.id] = true; });
    setSandboxMap(newMap);
  }, [addedSkills]);

  const handleBuild = useCallback(async () => {
    if (addedSkills.length > 0 && selectedModel) {
      const hasRAG = addedSkills.some(s => s.id === 'rag');
      const isFirstRAG = hasRAG && !ragInitializedRef.current;

      setSessionReady(false);
      setBuildError(null);
      setSessionInfo(null);
      const generation = ++buildGeneration.current;
      setIsExtendedBuild(isFirstRAG);
      setPhase('building');

      try {
        const skillIds = addedSkills.map(s => s.id);
        console.log('[App] Creating agent session:', selectedModel.id, skillIds, 'sandboxMap:', sandboxMap);
        const info = await createAgentSession(selectedModel.id, skillIds, true, sandboxMap);
        if (generation !== buildGeneration.current) { void deleteAgentSession(info.sessionId); return; }
        console.log('[App] Session created:', info.sessionId, 'sandbox:', info);
        setSessionId(info.sessionId);
        setSessionInfo(info);
        setSandboxStatus({ requested: info.sandboxRequested, active: info.sandboxActive });
        if (hasRAG) ragInitializedRef.current = true;
        setSessionReady(true);
      } catch (err) {
        if (generation !== buildGeneration.current) return;
        console.error('[App] Failed to create agent session:', err);
        setSessionId(null);
        setSandboxStatus(null);
        setSessionReady(false);
        setBuildError(err instanceof Error ? err.message : 'Could not build your agent. Try again.');
        setPhase('builder');
      }
    }
  }, [addedSkills, selectedModel, sandboxMap]);

  const handleBuildComplete = useCallback(() => {
    if (sessionReady && sessionId) setPhase('chat');
  }, [sessionReady, sessionId]);

  const handleReset = useCallback(() => {
    buildGeneration.current += 1;
    setBuildError(null);
    setSessionReady(false);
    setSessionInfo(null);
    if (sessionId) {
      deleteAgentSession(sessionId);
    }
    setSessionId(null);
    setAddedSkills([]);
    setSandboxMap({});
    setSandboxMode(false);
    setSandboxStatus(null);
    setPhase('soul');
    setSelectedModel(null);
    prevBlockySkillsRef.current = '';
    prevBlockyModelRef.current = null;
  }, [sessionId]);

  // Reset when switching modes
  const handleModeSwitch = useCallback((mode: InputMode) => {
    if (mode === inputMode) return;
    buildGeneration.current += 1;
    setBuildError(null);
    setSessionReady(false);
    setSessionInfo(null);
    if (sessionId) deleteAgentSession(sessionId);
    setInputMode(mode);
    setSessionId(null);
    setAddedSkills([]);
    setSandboxMap({});
    setSandboxMode(false);
    setSandboxStatus(null);
    setPhase('soul');
    setSelectedModel(null);
    prevBlockySkillsRef.current = '';
    prevBlockyModelRef.current = null;
  }, [inputMode, sessionId]);

  const addedSkillIds = addedSkills.map(s => s.id);

  return (
    <DndContext onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
      <div className="app">
        <ParticleBackground />
        
        {/* Header */}
        <motion.header 
          className="app-header"
          initial={{ y: -50, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.5 }}
        >
          <div className="header-logo">
            <svg className="nvidia-logo" viewBox="0 0 100 20" fill="currentColor">
              <text x="0" y="16" fontSize="16" fontWeight="bold" fontFamily="system-ui">NVIDIA</text>
            </svg>
            <span className="header-divider">|</span>
            <span className="header-title">Deep Agent Builder</span>
          </div>
          <div className="header-right">
            {/* Mode toggle — only on soul picker screen */}
            {phase === 'soul' && (
              <div className="mode-toggle">
                <button
                  className={`mode-btn ${inputMode === 'website' ? 'active' : ''}`}
                  onClick={() => handleModeSwitch('website')}
                >
                  🖱️ Website
                </button>
                <button
                  className={`mode-btn ${inputMode === 'visual' ? 'active' : ''}`}
                  onClick={() => handleModeSwitch('visual')}
                >
                  🧊 Visual
                </button>
              </div>
            )}
            {inputMode === 'visual' && (
              <div className={`blocky-indicator ${blocky.connected ? 'connected' : 'disconnected'}`}>
                <span className="blocky-dot" />
                <span>{blocky.connected ? 'Blocks Connected' : 'Waiting for Blocks...'}</span>
              </div>
            )}
            {/* Sandbox indicator in header — show on chat only. Reflects the
                ACTUAL backend state (sandboxStatus), not the toggle intent, so a
                requested-but-unavailable sandbox reads "unavailable", never
                "Sandboxed". Falls back to intent only before a session exists. */}
            {phase === 'chat' && (() => {
              const active = sandboxStatus?.active ?? false;
              const requested = sandboxStatus?.requested ?? sandboxMode;
              const cls = active ? 'on' : (requested ? 'failed' : 'off');
              const label = active
                ? '🔒 File / shell sandbox'
                : (requested ? '⚠️ Sandbox unavailable' : '⚠️ No Sandbox');
              return <span className={`sandbox-mode-badge ${cls}`}>{label}</span>;
            })()}
            <div className="header-badge" style={selectedModel ? { borderColor: selectedModel.primaryColor, color: selectedModel.primaryColor, background: selectedModel.subtleColor } : undefined}>
              {selectedModel ? `${selectedModel.name} · Build an Agent Workshop` : 'Build an Agent Workshop'}
            </div>
          </div>
        </motion.header>

        {/* Main content */}
        <div className="app-content">
          <AnimatePresence mode="wait">
            {phase === 'soul' && (
              <motion.div
                key="soul"
                className="soul-view"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.3 }}
              >
                <SoulPicker onSelect={handleSoulSelect} models={availableModels} error={modelError} onRetry={loadModels} />
              </motion.div>
            )}

            {(phase === 'builder' || phase === 'building') && (
              <motion.div
                key="builder"
                className="builder-view"
                initial={{ opacity: 0, x: 50 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -50 }}
                transition={{ duration: 0.3 }}
              >
                <SkillPalette addedSkillIds={addedSkillIds} selectedModel={selectedModel} onAddSkill={handleAddSkill} />
                
                <div className="app-main">
                  <AgentBuilder 
                    skills={addedSkills}
                    isBuilding={phase === 'building'}
                    isReady={false}
                    onRemoveSkill={handleRemoveSkill}
                    sandboxMap={sandboxMap}
                  />
                  
                  {buildError && <div className="build-error" role="alert"><strong>Build did not finish.</strong> {buildError} Your selections are saved. Try Build Agent again.</div>}
                  <BuildButton
                    disabled={addedSkills.length === 0}
                    isBuilding={phase === 'building'}
                    isReady={false}
                    onClick={handleBuild}
                    skillCount={addedSkills.length}
                  />
                </div>

                <SettingsPanel
                  sandboxMode={sandboxMode}
                  onToggleSandbox={handleToggleSandboxMode}
                  skills={addedSkills}
                  sandboxMap={sandboxMap}
                />
              </motion.div>
            )}

            {phase === 'chat' && (
              <motion.div
                key="chat"
                className="chat-view"
                initial={{ opacity: 0, x: 50 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.4, delay: 0.2 }}
              >
                {sessionInfo?.capabilities && <details className="session-capabilities">
                  <summary>Active tools &amp; boundaries</summary>
                  <p>File tools: {sessionInfo.capabilities.file_root ?? 'disabled'}. Shell: {sessionInfo.capabilities.execution}.
                    {' '}Web search and RAG run in the app.</p>
                  <p>Enabled: {sessionInfo.enabledTools.join(', ') || 'none'}</p>
                </details>}
                <ChatSection
                  isVisible={phase === 'chat'}
                  skills={addedSkills}
                  onReset={handleReset}
                  sessionId={sessionId}
                  model={selectedModel!}
                />
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Build animation overlay */}
        {phase === 'building' && <BuildAnimation
          isActive={phase === 'building'}
          onComplete={handleBuildComplete}
          sessionReady={sessionReady}
          extendedBuild={isExtendedBuild}
        />}

        {/* Sandbox info modal */}
        <AnimatePresence>
          {showSandboxInfo && (
            <>
              <motion.div
                className="sandbox-backdrop"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={() => setShowSandboxInfo(false)}
              />
              <motion.div
                className="sandbox-info-modal"
                ref={modalRef}
                role="dialog"
                aria-modal="true"
                aria-labelledby="sandbox-info-title"
                style={{ x: '-50%', y: '-50%' }}
                initial={{ opacity: 0, scale: 0.85 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                transition={{ type: 'spring', stiffness: 300, damping: 25 }}
              >
                <div className="sandbox-info-icon">🔒</div>
                <h2 id="sandbox-info-title" className="sandbox-info-title">Enable Sandbox Mode?</h2>
                <p className="sandbox-info-desc">
                  Run file and shell tools in an <strong>isolated <a href="https://www.docker.com/" target="_blank" rel="noreferrer">Docker</a> container</strong>.
                </p>
                <div className="sandbox-info-benefits">
                  <div className="sandbox-benefit">
                    <span className="benefit-icon">🛡️</span>
                    <div>
                      <strong>Isolated Execution</strong>
                      <p>File and shell tools use a separate workspace with no network access.</p>
                    </div>
                  </div>
                  <div className="sandbox-benefit">
                    <span className="benefit-icon">🔐</span>
                    <div>
                      <strong>Credential Protection</strong>
                      <p>Host files and API keys are not mounted into the container. Web search and RAG run in the app.</p>
                    </div>
                  </div>
                  <div className="sandbox-benefit">
                    <span className="benefit-icon">🧹</span>
                    <div>
                      <strong>Clean Slate</strong>
                      <p>Each session gets a fresh container. No leftover files or state from previous runs.</p>
                    </div>
                  </div>
                </div>
                <p className="sandbox-info-note">
                  Requires Docker. If the sandbox cannot start, the build stops so you can fix it and retry.
                </p>
                <div className="sandbox-info-buttons">
                  <button className="sandbox-confirm" onClick={handleConfirmSandboxMode}>
                    🔒 Enable Sandbox Mode
                  </button>
                  <button className="sandbox-cancel" onClick={() => setShowSandboxInfo(false)}>
                    Cancel
                  </button>
                </div>
              </motion.div>
            </>
          )}
        </AnimatePresence>

        {/* Disable sandbox warning modal */}
        <AnimatePresence>
          {showSandboxWarning && (
            <>
              <motion.div
                className="sandbox-backdrop"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={() => setShowSandboxWarning(false)}
              />
              <motion.div
                className="sandbox-warning-modal"
                ref={modalRef}
                role="dialog"
                aria-modal="true"
                aria-labelledby="sandbox-warning-title"
                style={{ x: '-50%', y: '-50%' }}
                initial={{ opacity: 0, scale: 0.85 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                transition={{ type: 'spring', stiffness: 300, damping: 25 }}
              >
                <div className="sandbox-warning-icon">⚠️</div>
                <h2 id="sandbox-warning-title" className="sandbox-warning-title">Disable Sandbox Mode?</h2>
                <p className="sandbox-warning-desc">
                  Shell commands will run <strong>as your workshop user</strong> and can access that user's files.
                  File tools alone stay within their workspace.
                </p>
                <div className="sandbox-info-buttons">
                  <button className="sandbox-cancel" onClick={() => setShowSandboxWarning(false)}>
                    Keep Sandbox On
                  </button>
                  <button className="sandbox-disable-btn" onClick={handleConfirmDisableSandbox}>
                    ⚠️ Disable Sandbox
                  </button>
                </div>
              </motion.div>
            </>
          )}
        </AnimatePresence>

        {/* Drag overlay */}
        <DragOverlay>
          {activeSkill && (
            <div className="drag-overlay-card">
              <SkillCard skill={activeSkill} isInPalette={false} />
            </div>
          )}
        </DragOverlay>
      </div>
    </DndContext>
  );
}

export default App;
