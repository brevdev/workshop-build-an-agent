import { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Skill } from '../../data/skills';
import type { ModelDef } from '../../data/models';
import type { ToolCall } from '../ToolCallsPanel';
import { ToolCallsPanel } from '../ToolCallsPanel';
import { ExportModal } from '../ExportModal';
import { sendMessage, sendApproval } from '../../api/agent';
import type { InterruptEvent } from '../../api/agent';
import './ChatSection.css';

interface TraceItem {
  id: string;
  name: string;
  icon: string;
  status: 'running' | 'done';
  duration?: number;
}

interface Message {
  id: string;
  role: 'user' | 'agent';
  content: string;
  timestamp: Date;
  traces?: TraceItem[];
}

interface ChatSectionProps {
  isVisible: boolean;
  skills: Skill[];
  onReset: () => void;
  sessionId: string | null;
  model: ModelDef;
}

function formatTokens(count: number): string {
  return count >= 1000 ? `${(count / 1000).toFixed(1)}k` : String(count);
}

export function ChatSection({ isVisible, skills, onReset, sessionId, model }: ChatSectionProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [toolCalls, setToolCalls] = useState<ToolCall[]>([]);
  const [activeToolId, setActiveToolId] = useState<string | null>(null);
  const [streamingContent, setStreamingContent] = useState('');
  const [activeTraces, setActiveTraces] = useState<TraceItem[]>([]);
  const tracesRef = useRef<TraceItem[]>([]);
  const [pendingInterrupt, setPendingInterrupt] = useState<InterruptEvent | null>(null);
  const [sessionTokens, setSessionTokens] = useState<{ input: number; output: number; total: number; reasoning: number }>({ input: 0, output: 0, total: 0, reasoning: 0 });
  const [showExportModal, setShowExportModal] = useState(false);
  const [usedQuestions, setUsedQuestions] = useState<Set<string>>(new Set());
  const interruptRef = useRef<boolean>(false); // ref copy for capturing into messages
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Greeting on first show
  useEffect(() => {
    if (isVisible && messages.length === 0) {
      const skillNames = skills.slice(0, 3).map(s => s.name).join(', ');
      setMessages([{
        id: 'greeting',
        role: 'agent',
        content: `🤖 **Deep Agent Online**\n\nI've been configured with ${skills.length} capabilities including ${skillNames}${skills.length > 3 ? ' and more' : ''}.\n\nHow can I assist you today?`,
        timestamp: new Date(),
      }]);
    }
  }, [isVisible, skills, messages.length]);

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent]);

  // Auto-focus
  useEffect(() => {
    if (isVisible) {
      inputRef.current?.focus();
    }
  }, [isVisible]);

  // Pick one random question per enabled skill, shuffle, take up to 3
  const suggestedQuestions = useMemo(() => {
    const questions: string[] = [];
    for (const skill of skills) {
      if (skill.sampleQuestions && skill.sampleQuestions.length > 0) {
        const idx = Math.floor(Math.random() * skill.sampleQuestions.length);
        questions.push(skill.sampleQuestions[idx]);
      }
    }
    // Fisher-Yates shuffle
    for (let i = questions.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [questions[i], questions[j]] = [questions[j], questions[i]];
    }
    return questions.slice(0, 3);
  }, [skills]);

  const remainingQuestions = suggestedQuestions.filter(q => !usedQuestions.has(q));

  const handleSend = useCallback(async (overrideText?: string) => {
    const text = overrideText ?? input;
    if (!text.trim() || isTyping) return;

    if (!sessionId) {
      setMessages(prev => [...prev, {
        id: `error-${Date.now()}`,
        role: 'agent',
        content: '⚠️ No agent session found. Please click "Build New Agent" and try again.',
        timestamp: new Date(),
      }]);
      return;
    }

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    const currentInput = text;
    setInput('');
    setIsTyping(true);
    setStreamingContent('');

    let fullContent = '';
    let rawContent = '';

    // Reset traces and interrupt state for this response
    tracesRef.current = [];
    setActiveTraces([]);
    interruptRef.current = false;
    setPendingInterrupt(null);

    // Timeout: abort after 60s
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 60000);

    try {
      await sendMessage(sessionId, currentInput, (event) => {
        switch (event.type) {
          case 'token':
            rawContent += event.content;
            fullContent = rawContent
              .replace(/<think>[\s\S]*?<\/think>/g, '')
              .replace(/<think>[\s\S]*$/, '')
              .trim();
            setStreamingContent(fullContent);
            break;

          case 'tool_start': {
            const skill = skills.find(s => s.id === event.skillId);
            setActiveToolId(event.skillId);

            // Add to tool calls panel
            setToolCalls(prev => [...prev, {
              id: event.id,
              skillId: event.skillId,
              skillName: skill?.name || event.name,
              skillIcon: skill?.icon || event.icon,
              action: event.action,
              status: 'running',
              startTime: new Date(),
              input: event.input,
            }]);

            // Add inline trace (state + ref)
            const newTrace: TraceItem = {
              id: event.id,
              name: event.action || event.name,
              icon: skill?.icon || event.icon,
              status: 'running',
            };
            tracesRef.current = [...tracesRef.current, newTrace];
            setActiveTraces(tracesRef.current);
            break;
          }

          case 'tool_end':
            setToolCalls(prev => prev.map(tc =>
              tc.id === event.id
                ? {
                    ...tc,
                    status: 'success' as const,
                    endTime: new Date(),
                    duration: event.duration,
                    output: event.output,
                  }
                : tc
            ));
            setActiveToolId(null);

            // Update inline trace (state + ref)
            tracesRef.current = tracesRef.current.map(t =>
              t.id === event.id
                ? { ...t, status: 'done' as const, duration: event.duration }
                : t
            );
            setActiveTraces(tracesRef.current);
            break;

          case 'error':
            fullContent += `\n\n⚠️ Error: ${event.message}`;
            setStreamingContent(fullContent);
            break;

          case 'usage':
            setSessionTokens(prev => ({
              input: prev.input + event.inputTokens,
              output: prev.output + event.outputTokens,
              total: prev.total + event.totalTokens,
              reasoning: prev.reasoning + event.reasoningTokens,
            }));
            break;

          case 'interrupt':
            interruptRef.current = true;
            setPendingInterrupt(event as InterruptEvent);
            break;

          case 'done':
            break;
        }
      }, controller.signal);
    } catch (err) {
      console.error('[Chat] Stream error:', err);
      const errorMsg = err instanceof Error ? err.message : 'Connection failed';
      if (controller.signal.aborted && !fullContent) {
        fullContent = '⚠️ Request timed out after 60 seconds. The backend may be overloaded — try again.';
      } else {
        fullContent = fullContent || `⚠️ Could not reach the agent backend.\n\n${errorMsg}`;
      }
    } finally {
      clearTimeout(timeout);
    }

    // If interrupted, keep typing state — we'll resume after approval
    if (interruptRef.current) {
      return;
    }

    // Finalize the streamed message — embed traces into the message
    if (!fullContent) {
      fullContent = '⚠️ No response received from the agent. The backend may need to be restarted.';
    }

    // Capture traces from ref (always up-to-date, unlike state)
    const finalTraces = tracesRef.current.map(t => ({ ...t, status: 'done' as const }));
    setMessages(prev => [...prev, {
      id: `agent-${Date.now()}`,
      role: 'agent',
      content: fullContent || '',
      timestamp: new Date(),
      traces: finalTraces.length > 0 ? finalTraces : undefined,
    }]);
    tracesRef.current = [];
    setActiveTraces([]);
    setStreamingContent('');
    setIsTyping(false);
  }, [input, isTyping, sessionId, skills]);

  const handleApproval = useCallback(async (decision: 'approve' | 'reject') => {
    if (!sessionId) return;

    setPendingInterrupt(null);
    interruptRef.current = false;

    let fullContent = '';
    let rawContent = '';

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 60000);

    try {
      await sendApproval(sessionId, decision, (event) => {
        switch (event.type) {
          case 'token':
            rawContent += event.content;
            fullContent = rawContent
              .replace(/<think>[\s\S]*?<\/think>/g, '')
              .replace(/<think>[\s\S]*$/, '')
              .trim();
            setStreamingContent(fullContent);
            break;
          case 'tool_start': {
            const skill = skills.find(s => s.id === event.skillId);
            setActiveToolId(event.skillId);
            setToolCalls(prev => [...prev, { id: event.id, skillId: event.skillId, skillName: skill?.name || event.name, skillIcon: skill?.icon || event.icon, action: event.action, status: 'running', startTime: new Date(), input: event.input }]);
            const newTrace: TraceItem = { id: event.id, name: event.action || event.name, icon: skill?.icon || event.icon, status: 'running' };
            tracesRef.current = [...tracesRef.current, newTrace];
            setActiveTraces(tracesRef.current);
            break;
          }
          case 'tool_end':
            setToolCalls(prev => prev.map(tc => tc.id === event.id ? { ...tc, status: 'success' as const, endTime: new Date(), duration: event.duration, output: event.output } : tc));
            setActiveToolId(null);
            tracesRef.current = tracesRef.current.map(t => t.id === event.id ? { ...t, status: 'done' as const, duration: event.duration } : t);
            setActiveTraces(tracesRef.current);
            break;
          case 'usage':
            setSessionTokens(prev => ({
              input: prev.input + event.inputTokens,
              output: prev.output + event.outputTokens,
              total: prev.total + event.totalTokens,
              reasoning: prev.reasoning + event.reasoningTokens,
            }));
            break;
          case 'interrupt':
            interruptRef.current = true;
            setPendingInterrupt(event as InterruptEvent);
            break;
          case 'error':
            fullContent += `\n\n⚠️ Error: ${event.message}`;
            setStreamingContent(fullContent);
            break;
          case 'done':
            break;
        }
      }, controller.signal);
    } catch (err) {
      console.error('[Chat] Approval stream error:', err);
    } finally {
      clearTimeout(timeout);
    }

    // If another interrupt fired, don't finalize
    if (interruptRef.current) return;

    // Finalize
    const finalTraces = tracesRef.current.map(t => ({ ...t, status: 'done' as const }));
    if (decision === 'reject') {
      fullContent = fullContent || '🚫 Tool execution was rejected by the user.';
    }
    setMessages(prev => [...prev, {
      id: `agent-${Date.now()}`,
      role: 'agent',
      content: fullContent || '✅ Done.',
      timestamp: new Date(),
      traces: finalTraces.length > 0 ? finalTraces : undefined,
    }]);
    tracesRef.current = [];
    setActiveTraces([]);
    setStreamingContent('');
    setIsTyping(false);
  }, [sessionId, skills]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          className="chat-section"
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 50 }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
        >
          <div className="chat-main-area">
            {/* Chat Panel */}
            <div className="chat-panel">
              {/* Chat Header */}
              <div className="chat-header">
                <div className="chat-header-info">
                  <div className="chat-status">
                    <span className="status-dot" />
                    <span>Deep Agent Active</span>
                    {sessionId && <span className="session-id">#{sessionId}</span>}
                  </div>
                  <div className="chat-skills">
                    {skills.slice(0, 4).map(skill => (
                      <span key={skill.id} className="skill-tag">
                        {skill.icon} {skill.name}
                        <span className="skill-tooltip">{skill.description}</span>
                      </span>
                    ))}
                    {skills.length > 4 && (
                      <span className="skill-tag more">+{skills.length - 4}</span>
                    )}
                  </div>
                </div>
                <div className="chat-header-actions">
                  <button className="reset-btn" onClick={onReset}>
                    Build New Agent
                  </button>
                  <button
                    className="export-btn"
                    onClick={() => setShowExportModal(true)}
                    disabled={sessionTokens.total === 0}
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                      <polyline points="7 10 12 15 17 10" />
                      <line x1="12" y1="15" x2="12" y2="3" />
                    </svg>
                    Export
                  </button>
                </div>
              </div>

              {/* Messages */}
              <div className="chat-messages">
                {messages.map((message, index) => (
                  <motion.div
                    key={message.id}
                    className={`message ${message.role}`}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index === 0 ? 0 : 0.1 }}
                  >
                    <div className="message-avatar">
                      {message.role === 'agent' ? '🤖' : '👤'}
                    </div>
                    <div className="message-content">
                      {/* Saved traces — show above the response text */}
                      {message.traces && message.traces.length > 0 && (
                        <div className="tool-traces saved">
                          {message.traces.map((trace) => (
                            <div key={trace.id} className="tool-trace done">
                              <span className="trace-icon">{trace.icon}</span>
                              <span className="trace-name">{trace.name}</span>
                              <span className="trace-check">✓</span>
                              {trace.duration !== undefined && (
                                <span className="trace-duration">{trace.duration}ms</span>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                      <div className="message-text markdown-body">
                        <Markdown remarkPlugins={[remarkGfm]}>{message.content}</Markdown>
                      </div>
                      <div className="message-time">
                        {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </div>
                    </div>
                  </motion.div>
                ))}

                {/* Human-in-the-loop approval prompt */}
                <AnimatePresence>
                  {pendingInterrupt && (
                    <motion.div
                      className="approval-prompt"
                      initial={{ opacity: 0, y: 10, scale: 0.95 }}
                      animate={{ opacity: 1, y: 0, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.95 }}
                    >
                      <div className="approval-header">
                        <span className="approval-icon">⚠️</span>
                        <span className="approval-title">Approval Required</span>
                      </div>
                      <div className="approval-details">
                        {pendingInterrupt.actionRequests.map((req, i) => (
                          <div key={i} className="approval-action">
                            <span className="approval-tool-name">{req.name}</span>
                            <pre className="approval-args">{JSON.stringify(req.args, null, 2)}</pre>
                          </div>
                        ))}
                      </div>
                      <div className="approval-buttons">
                        <button className="approval-btn approve" onClick={() => handleApproval('approve')}>
                          ✓ Approve
                        </button>
                        <button className="approval-btn reject" onClick={() => handleApproval('reject')}>
                          ✕ Reject
                        </button>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Live tool traces — only during active response */}
                <AnimatePresence>
                  {isTyping && activeTraces.length > 0 && (
                    <motion.div
                      className="tool-traces live"
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0 }}
                    >
                      {activeTraces.map((trace) => (
                        <motion.div
                          key={trace.id}
                          className={`tool-trace ${trace.status}`}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          layout
                        >
                          <span className="trace-icon">{trace.icon}</span>
                          <span className="trace-name">{trace.name}</span>
                          {trace.status === 'running' ? (
                            <span className="trace-spinner" />
                          ) : (
                            <span className="trace-check">✓</span>
                          )}
                          {trace.duration !== undefined && (
                            <span className="trace-duration">{trace.duration}ms</span>
                          )}
                        </motion.div>
                      ))}
                    </motion.div>
                  )}
                </AnimatePresence>

                {/* Streaming content */}
                {streamingContent && (
                  <motion.div
                    className="message agent"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                  >
                    <div className="message-avatar">🤖</div>
                    <div className="message-content">
                      <div className="message-text markdown-body streaming">
                        <Markdown remarkPlugins={[remarkGfm]}>{streamingContent}</Markdown>
                        <span className="cursor-blink">▊</span>
                      </div>
                    </div>
                  </motion.div>
                )}
                
                {/* Typing indicator */}
                <AnimatePresence>
                  {isTyping && !streamingContent && (
                    <motion.div
                      className="message agent typing"
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0 }}
                    >
                      <div className="message-avatar">🤖</div>
                      <div className="message-content">
                        <div className="typing-indicator">
                          <span />
                          <span />
                          <span />
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
                
                <AnimatePresence>
                  {!isTyping && remainingQuestions.length > 0 && (
                    <motion.div
                      className="suggested-questions"
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                    >
                      {remainingQuestions.map((question, index) => (
                        <motion.button
                          key={question}
                          className="suggested-question-pill"
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: index * 0.1 }}
                          whileHover={{ scale: 1.03 }}
                          whileTap={{ scale: 0.97 }}
                          onClick={() => {
                            setUsedQuestions(prev => new Set(prev).add(question));
                            handleSend(question);
                          }}
                        >
                          {question}
                        </motion.button>
                      ))}
                    </motion.div>
                  )}
                </AnimatePresence>

                <div ref={messagesEndRef} />
              </div>

              {/* Input */}
              <div className="chat-input-container">
                <div className="chat-input-wrapper">
                  <input
                    ref={inputRef}
                    type="text"
                    className="chat-input"
                    placeholder="Message your Deep Agent..."
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    disabled={isTyping}
                  />
                  <button 
                    className="send-btn"
                    onClick={() => handleSend()}
                    disabled={!input.trim() || isTyping}
                  >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M22 2L11 13" />
                      <path d="M22 2L15 22L11 13L2 9L22 2Z" />
                    </svg>
                  </button>
                </div>
                {sessionTokens.total > 0 && (
                  <div className="token-counter">
                    {sessionTokens.reasoning > 0 ? (
                      <span className="token-counter-group">
                        <span>~{formatTokens(sessionTokens.reasoning)} <span className="token-label">reasoning</span></span>
                        <span className="token-separator">&middot;</span>
                        <span>~{formatTokens(sessionTokens.output - sessionTokens.reasoning)} <span className="token-label">output</span></span>
                      </span>
                    ) : (
                      <>~{formatTokens(sessionTokens.total)} tokens generated</>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Tool Calls Panel */}
            <ToolCallsPanel
              toolCalls={toolCalls}
              skills={skills}
              activeToolId={activeToolId}
            />
          </div>

          <ExportModal
            isOpen={showExportModal}
            onClose={() => setShowExportModal(false)}
            model={model}
            skills={skills}
            sessionTokens={sessionTokens}
            toolCalls={toolCalls}
          />
        </motion.div>
      )}
    </AnimatePresence>
  );
}
