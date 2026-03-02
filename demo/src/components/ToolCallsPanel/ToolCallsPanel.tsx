import { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { Skill } from '../../data/skills';
import { ToolWebView } from './ToolWebView';
import './ToolCallsPanel.css';

export interface ToolCall {
  id: string;
  skillId: string;
  skillName: string;
  skillIcon: string;
  action: string;
  status: 'pending' | 'running' | 'success' | 'error';
  startTime: Date;
  endTime?: Date;
  duration?: number;
  input?: string;
  output?: string;
}

interface ToolCallsPanelProps {
  toolCalls: ToolCall[];
  skills: Skill[];
  activeToolId: string | null;
}

type ViewMode = 'web' | 'log';

function getStatusColor(status: ToolCall['status']) {
  switch (status) {
    case 'pending': return 'var(--text-tertiary)';
    case 'running': return 'var(--nvidia-green)';
    case 'success': return 'var(--nvidia-green)';
    case 'error': return 'var(--r400)';
  }
}

function getStatusIcon(status: ToolCall['status']) {
  switch (status) {
    case 'pending': return '○';
    case 'running': return '◉';
    case 'success': return '✓';
    case 'error': return '✕';
  }
}

export function ToolCallsPanel({ toolCalls, skills, activeToolId }: ToolCallsPanelProps) {
  const [viewMode, setViewMode] = useState<ViewMode>('web');
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (viewMode === 'log') {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [toolCalls, viewMode]);

  return (
    <div className="tool-calls-panel">
      {/* Panel Header with Toggle */}
      <div className="tool-panel-header">
        <div className="tool-panel-title">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
            <path d="M2 3h12v1H2V3zm0 4h12v1H2V7zm0 4h8v1H2v-1z"/>
          </svg>
          <span>Tool Calls</span>
          <div className="tool-panel-count">
            {toolCalls.filter(t => t.status === 'success').length}/{toolCalls.length}
          </div>
        </div>

        {/* Toggle */}
        <div className="view-toggle">
          <button
            className={`toggle-btn ${viewMode === 'web' ? 'active' : ''}`}
            onClick={() => setViewMode('web')}
            title="Web View"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="3" />
              <circle cx="4" cy="6" r="2" />
              <circle cx="20" cy="6" r="2" />
              <circle cx="4" cy="18" r="2" />
              <circle cx="20" cy="18" r="2" />
              <line x1="9.5" y1="10.5" x2="5.5" y2="7.5" />
              <line x1="14.5" y1="10.5" x2="18.5" y2="7.5" />
              <line x1="9.5" y1="13.5" x2="5.5" y2="16.5" />
              <line x1="14.5" y1="13.5" x2="18.5" y2="16.5" />
            </svg>
          </button>
          <button
            className={`toggle-btn ${viewMode === 'log' ? 'active' : ''}`}
            onClick={() => setViewMode('log')}
            title="Log View"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="4" y1="6" x2="20" y2="6" />
              <line x1="4" y1="12" x2="20" y2="12" />
              <line x1="4" y1="18" x2="14" y2="18" />
            </svg>
          </button>
        </div>
      </div>

      {/* View Content */}
      <div className="tool-panel-content">
        <AnimatePresence mode="wait">
          {viewMode === 'web' ? (
            <motion.div
              key="web"
              className="view-container"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.2 }}
            >
              <ToolWebView
                skills={skills}
                toolCalls={toolCalls}
                activeToolId={activeToolId}
              />
            </motion.div>
          ) : (
            <motion.div
              key="log"
              className="view-container"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ duration: 0.2 }}
            >
              {/* Skills inventory */}
              <div className="tool-skills-inventory">
                <div className="inventory-label">Available Tools</div>
                <div className="inventory-grid">
                  {skills.map(skill => {
                    const isActive = activeToolId === skill.id;
                    const callCount = toolCalls.filter(t => t.skillId === skill.id && t.status === 'success').length;
                    return (
                      <motion.div
                        key={skill.id}
                        className={`inventory-item ${isActive ? 'active' : ''} ${callCount > 0 ? 'used' : ''}`}
                        animate={isActive ? {
                          boxShadow: [
                            '0 0 0px rgba(118, 185, 0, 0)',
                            '0 0 20px rgba(118, 185, 0, 0.6)',
                            '0 0 0px rgba(118, 185, 0, 0)',
                          ],
                        } : {}}
                        transition={{ duration: 0.8, repeat: isActive ? Infinity : 0 }}
                      >
                        <span className="inventory-icon">{skill.icon}</span>
                        <span className="inventory-name">{skill.name}</span>
                        {callCount > 0 && (
                          <span className="inventory-count">{callCount}</span>
                        )}
                        {isActive && (
                          <motion.div
                            className="active-indicator"
                            layoutId="activeIndicator"
                            initial={false}
                            transition={{ type: 'spring', stiffness: 300, damping: 25 }}
                          />
                        )}
                      </motion.div>
                    );
                  })}
                </div>
              </div>

              {/* Tool call log */}
              <div className="tool-call-log">
                <div className="log-label">Execution Log</div>
                <div className="log-entries">
                  <AnimatePresence>
                    {toolCalls.length === 0 && (
                      <motion.div
                        className="log-empty"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                      >
                        <span className="log-empty-icon">⚙️</span>
                        <span>Tool calls will appear here</span>
                      </motion.div>
                    )}
                    {toolCalls.map((call, index) => (
                      <motion.div
                        key={call.id}
                        className={`log-entry ${call.status}`}
                        initial={{ opacity: 0, x: 20, height: 0 }}
                        animate={{ opacity: 1, x: 0, height: 'auto' }}
                        transition={{ delay: index * 0.05, duration: 0.3 }}
                      >
                        <div className="log-entry-header">
                          <div className="log-entry-status" style={{ color: getStatusColor(call.status) }}>
                            {call.status === 'running' ? (
                              <motion.span
                                animate={{ opacity: [1, 0.3, 1] }}
                                transition={{ duration: 1, repeat: Infinity }}
                              >
                                {getStatusIcon(call.status)}
                              </motion.span>
                            ) : (
                              getStatusIcon(call.status)
                            )}
                          </div>
                          <div className="log-entry-info">
                            <div className="log-entry-name">
                              <span className="log-entry-icon">{call.skillIcon}</span>
                              <span>{call.skillName}</span>
                            </div>
                            <div className="log-entry-action">{call.action}</div>
                          </div>
                          {call.duration !== undefined && (
                            <div className="log-entry-duration">{call.duration}ms</div>
                          )}
                        </div>

                        {(call.input || call.output) && (
                          <div className="log-entry-details">
                            {call.input && (
                              <div className="log-detail">
                                <span className="log-detail-label">Input</span>
                                <code className="log-detail-value">{call.input}</code>
                              </div>
                            )}
                            {call.output && call.status === 'success' && (
                              <div className="log-detail">
                                <span className="log-detail-label">Output</span>
                                <code className="log-detail-value">{call.output}</code>
                              </div>
                            )}
                          </div>
                        )}

                        {call.status === 'running' && (
                          <div className="log-entry-progress">
                            <motion.div
                              className="progress-bar"
                              initial={{ width: '0%' }}
                              animate={{ width: '100%' }}
                              transition={{ duration: 1.5, ease: 'linear' }}
                            />
                          </div>
                        )}
                      </motion.div>
                    ))}
                  </AnimatePresence>
                  <div ref={bottomRef} />
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
