import { useDroppable } from '@dnd-kit/core';
import { motion, AnimatePresence } from 'framer-motion';
import type { Skill } from '../../data/skills';
import { RobotVisual } from '../RobotVisual';
import './AgentBuilder.css';

interface AgentBuilderProps {
  skills: Skill[];
  isBuilding: boolean;
  isReady: boolean;
  onRemoveSkill: (skillId: string) => void;
  sandboxMap: Record<string, boolean>;
}

export function AgentBuilder({ skills, isBuilding, isReady, onRemoveSkill, sandboxMap }: AgentBuilderProps) {
  const { isOver, setNodeRef } = useDroppable({
    id: 'agent-dropzone',
  });

  return (
    <motion.main 
      className="agent-builder"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5, delay: 0.2 }}
    >
      <div className="agent-builder-header">
        <motion.h1 
          className="agent-builder-title"
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          Build Your <span className="text-brand">Deep Agent</span>
        </motion.h1>
        <motion.p 
          className="agent-builder-subtitle"
          initial={{ y: -10, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.4 }}
        >
          Drag skills onto the agent to add capabilities
        </motion.p>
      </div>

      <div 
        ref={setNodeRef}
        className={`agent-dropzone ${isOver ? 'drag-over' : ''} ${skills.length > 0 ? 'has-skills' : ''}`}
      >
        <RobotVisual 
          skills={skills} 
          isBuilding={isBuilding}
          isReady={isReady}
        />

        {/* Drop indicator */}
        <AnimatePresence>
          {isOver && (
            <motion.div
              className="drop-indicator"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
            >
              <div className="drop-indicator-ring" />
              <span>Drop to add skill</span>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Empty state hint */}
        <AnimatePresence>
          {skills.length === 0 && !isOver && (
            <motion.div
              className="empty-hint"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ delay: 0.5 }}
            >
              <div className="empty-hint-icon">↖</div>
              <p>Drag skills from the palette</p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Skills list */}
      <AnimatePresence>
        {skills.length > 0 && (
          <motion.div
            className="added-skills"
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 20, opacity: 0 }}
          >
            <h3 className="added-skills-title">Added Skills ({skills.length})</h3>
            <div className="added-skills-list">
              {skills.map((skill) => {
                const isSandboxed = sandboxMap[skill.id] || false;
                return (
                  <motion.div
                    key={skill.id}
                    className={`added-skill-chip ${isSandboxed ? 'sandboxed' : ''}`}
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    exit={{ scale: 0 }}
                    whileHover={{ scale: 1.05 }}
                    layout
                  >
                    <span className="chip-icon">{skill.icon}</span>
                    <span className="chip-name">{skill.name}</span>
                    {skill.sandboxable && (
                      <span
                        className={`chip-sandbox-indicator ${isSandboxed ? 'locked' : 'unlocked'}`}
                        title={isSandboxed ? 'Sandboxed (isolated)' : 'No sandbox'}
                      >
                        {isSandboxed ? '🔒' : '🔓'}
                      </span>
                    )}
                    <button
                      className="chip-remove"
                      onClick={() => onRemoveSkill(skill.id)}
                      aria-label={`Remove ${skill.name}`}
                    >
                      ×
                    </button>
                    <span className="chip-tooltip">
                      {skill.description}
                      {skill.sandboxable && (isSandboxed ? ' (sandboxed)' : ' (local)')}
                    </span>
                  </motion.div>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.main>
  );
}
