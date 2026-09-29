import { motion, AnimatePresence } from 'framer-motion';
import type { Skill } from '../../data/skills';
import './SettingsPanel.css';

interface SettingsPanelProps {
  sandboxMode: boolean;
  onToggleSandbox: () => void;
  skills: Skill[];
  sandboxMap: Record<string, boolean>;
}

export function SettingsPanel({ sandboxMode, onToggleSandbox, skills, sandboxMap }: SettingsPanelProps) {
  const sandboxableSkills = skills.filter(s => s.sandboxable);

  return (
    <motion.aside
      className="settings-panel"
      initial={{ x: 100, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
    >
      <div className="settings-header">
        <h2 className="settings-title">Settings</h2>
        <p className="settings-subtitle">Agent configuration</p>
      </div>

      <div className="settings-content">
        {/* Sandbox Section */}
        <div className="settings-section">
          <div className="settings-section-header">
            <h3 className="settings-section-name">Sandbox Mode</h3>
          </div>

          <button type="button" role="switch" aria-checked={sandboxMode} aria-label="Sandbox Mode" className="sandbox-toggle-card" onClick={onToggleSandbox}>
            <div className="sandbox-toggle-left">
              <span className="sandbox-toggle-icon">{sandboxMode ? '🔒' : '⚠️'}</span>
              <div className="sandbox-toggle-info">
                <span className="sandbox-toggle-label">
                  {sandboxMode ? 'Sandbox Enabled' : 'Sandbox Disabled'}
                </span>
                <span className="sandbox-toggle-desc">
                  {sandboxMode ? 'File and shell tools use Docker' : 'Shell tools run as your user'}
                </span>
              </div>
            </div>
            <div className={`sandbox-switch ${sandboxMode ? 'on' : 'off'}`}>
              <div className="sandbox-switch-thumb" />
            </div>
          </button>

          {/* Sandbox status per tool */}
          <AnimatePresence>
            {sandboxableSkills.length > 0 && (
              <motion.div
                className="sandbox-tool-list"
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
              >
                <div className="sandbox-tool-label">Requested tool isolation</div>
                {sandboxableSkills.map(skill => {
                  const isSandboxed = sandboxMap[skill.id] || false;
                  return (
                    <div key={skill.id} className={`sandbox-tool-row ${isSandboxed ? 'active' : ''}`}>
                      <span className="sandbox-tool-icon">{skill.icon}</span>
                      <span className="sandbox-tool-name">{skill.name}</span>
                      <span className={`sandbox-tool-badge ${isSandboxed ? 'locked' : 'unlocked'}`}>
                        {isSandboxed ? '🔒 Docker requested' : '🔓 Local'}
                      </span>
                    </div>
                  );
                })}
              </motion.div>
            )}
          </AnimatePresence>

          {/* Info box */}
          <div className="sandbox-info-box">
            <div className="sandbox-info-row">
              <span>🛡️</span>
              <span>File and shell tools in <a href="https://www.docker.com/" target="_blank" rel="noreferrer">Docker</a> containers</span>
            </div>
            <div className="sandbox-info-row">
              <span>🔐</span>
              <span>Web search and RAG run in the app</span>
            </div>
            <div className="sandbox-info-row">
              <span>🧹</span>
              <span>Fresh container per agent session</span>
            </div>
          </div>
        </div>

        {/* Future: more settings sections can go here */}
        <div className="settings-section coming-soon-settings">
          <div className="settings-section-header">
            <h3 className="settings-section-name">More Settings</h3>
          </div>
          <div className="settings-placeholder">
            <span>🔧</span>
            <span>Memory, checkpoints, and more coming soon</span>
          </div>
        </div>
      </div>
    </motion.aside>
  );
}
