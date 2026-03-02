import { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { QRCodeSVG } from 'qrcode.react';
import type { ModelDef } from '../../data/models';
import type { Skill } from '../../data/skills';
import type { ToolCall } from '../ToolCallsPanel';
import './ExportModal.css';

interface ExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  model: ModelDef;
  skills: Skill[];
  sessionTokens: { input: number; output: number; total: number; reasoning: number };
  toolCalls: ToolCall[];
}

function formatTokens(count: number): string {
  return count >= 1000 ? `${(count / 1000).toFixed(1)}k` : String(count);
}

const WORKSHOP_URL = 'https://github.com/brevdev/workshop-build-an-agent';
const LAUNCHABLE_URL = 'https://brev.nvidia.com/launchable/deploy?launchableID=env-32kC34ErT9wsqTcJyaKMxBEuhr2';
const TAKE_HOME_URL = 'https://example.com/';

export function ExportModal({ isOpen, onClose, model, skills, sessionTokens, toolCalls }: ExportModalProps) {
  // Escape key listener
  useEffect(() => {
    if (!isOpen) return;
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [isOpen, onClose]);

  // Compute tool breakdown from toolCalls
  const toolBreakdown = toolCalls.reduce<Record<string, { name: string; icon: string; count: number }>>((acc, tc) => {
    const key = tc.skillId;
    if (!acc[key]) {
      acc[key] = { name: tc.skillName, icon: tc.skillIcon, count: 0 };
    }
    acc[key].count++;
    return acc;
  }, {});

  const tools = skills.filter(s => s.category === 'tools');
  const agentSkills = skills.filter(s => s.category === 'skills');
  const totalInvocations = toolCalls.length;

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            className="export-backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.25 }}
            onClick={onClose}
          />

          {/* Modal */}
          <motion.div
            className="export-modal"
            style={{ x: '-50%', y: '-50%' }}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            transition={{ type: 'spring', stiffness: 250, damping: 22 }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="export-header">
              <motion.h2
                className="export-title"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
              >
                Session Export
              </motion.h2>
              <motion.p
                className="export-subtitle"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.2 }}
              >
                Your agent session summary
              </motion.p>
            </div>

            {/* Two-column grid */}
            <div className="export-grid">
              {/* Left: Session Metrics */}
              <motion.div
                className="export-card"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.15 }}
              >
                <div className="export-card-label">Session Metrics</div>
                <div className="metrics-columns">
                  <div className="export-metrics">
                    <div className="export-metric">
                      <span className="metric-value">{formatTokens(sessionTokens.reasoning)}</span>
                      <span className="metric-label">reasoning tokens</span>
                    </div>
                    <div className="export-metric">
                      <span className="metric-value">{formatTokens(sessionTokens.output - sessionTokens.reasoning)}</span>
                      <span className="metric-label">output tokens</span>
                    </div>
                    <div className="export-metric">
                      <span className="metric-value">{totalInvocations}</span>
                      <span className="metric-label">tool invocations</span>
                    </div>
                  </div>

                  {Object.keys(toolBreakdown).length > 0 && (
                    <div className="export-tool-breakdown">
                      <div className="breakdown-label">Tool Breakdown</div>
                      {Object.values(toolBreakdown).map((tool) => (
                        <div key={tool.name} className="breakdown-row">
                          <span className="breakdown-icon">{tool.icon}</span>
                          <span className="breakdown-name">{tool.name}</span>
                          <span className="breakdown-count">{tool.count}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </motion.div>

              {/* Right: Agent Configuration */}
              <motion.div
                className="export-card"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 }}
              >
                <div className="export-card-label">Agent Configuration</div>
                <div className="export-config">
                  <div className="config-row">
                    <span className="config-key">Model</span>
                    <span className="config-value">{model.name}</span>
                  </div>
                  <div className="config-row">
                    <span className="config-key">Provider</span>
                    <span className="config-value">{model.provider}</span>
                  </div>

                  {tools.length > 0 && (
                    <div className="config-section">
                      <span className="config-key">Tools</span>
                      <div className="config-tags">
                        {tools.map(t => (
                          <span key={t.id} className="config-tag">{t.icon} {t.name}</span>
                        ))}
                      </div>
                    </div>
                  )}

                  {agentSkills.length > 0 && (
                    <div className="config-section">
                      <span className="config-key">Skills</span>
                      <div className="config-tags">
                        {agentSkills.map(s => (
                          <span key={s.id} className="config-tag">{s.icon} {s.name}</span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </motion.div>
            </div>

            {/* Take Your Agent Home */}
            <motion.div
              className="export-take-home"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.25 }}
            >
              <div className="take-home-label">Take Your Agent Home</div>
              <div className="take-home-grid">
                <div className="take-home-step">
                  <div className="step-header">
                    <div className="step-badge">1</div>
                    <div className="step-heading">Claim Your Free Credits</div>
                  </div>
                  <p className="step-text">
                    Scan the QR code at the booth to claim your complimentary Brev credits.
                  </p>
                  <p className="step-hint">$30 in free Brev credits — limited to first 200 users</p>
                  <div className="step-scan-indicator">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M7 17L17 7" />
                      <path d="M7 7h10v10" />
                    </svg>
                    Scan at booth
                  </div>
                </div>
                <div className="take-home-step">
                  <div className="step-header">
                    <div className="step-badge">2</div>
                    <div className="step-heading">Take Your Agent Home</div>
                  </div>
                  <p className="step-text">
                    Scan to deploy your agent in your own Brev account.
                  </p>
                  <div className="step-qr">
                    <QRCodeSVG
                      value={TAKE_HOME_URL}
                      size={120}
                      bgColor="transparent"
                      fgColor="#ffffff"
                      level="M"
                    />
                  </div>
                </div>
              </div>
            </motion.div>

            {/* CTA Footer */}
            <motion.div
              className="export-cta"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.35 }}
            >
              <div className="cta-content">
                <div className="cta-label">Continue Learning</div>
                <p className="cta-text">
                  You just experienced building an AI agent — now dive deeper with the full workshop.
                </p>
                <div className="cta-buttons">
                  <a
                    className="cta-link"
                    href={LAUNCHABLE_URL}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Launch Workshop
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M7 17L17 7" />
                      <path d="M7 7h10v10" />
                    </svg>
                  </a>
                  <a
                    className="cta-link-secondary"
                    href={WORKSHOP_URL}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    View on GitHub
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M7 17L17 7" />
                      <path d="M7 7h10v10" />
                    </svg>
                  </a>
                </div>
              </div>
              <div className="cta-qr">
                <QRCodeSVG
                  value={LAUNCHABLE_URL}
                  size={120}
                  bgColor="transparent"
                  fgColor="#ffffff"
                  level="M"
                />
              </div>
            </motion.div>

            {/* Close button */}
            <motion.button
              className="export-close"
              onClick={onClose}
              whileHover={{ scale: 1.15, rotate: 90 }}
              whileTap={{ scale: 0.85 }}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3 }}
            >
              ✕
            </motion.button>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
