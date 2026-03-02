import { motion } from 'framer-motion';
import { skills, comingSoonSkills } from '../../data/skills';
import type { ModelDef } from '../../data/models';
import { SkillCard } from '../SkillCard';
import './SkillPalette.css';

interface SkillPaletteProps {
  addedSkillIds: string[];
  selectedModel?: ModelDef | null;
}

export function SkillPalette({ addedSkillIds, selectedModel }: SkillPaletteProps) {
  const availableSkills = skills.filter(skill => !addedSkillIds.includes(skill.id));
  const recommendedIds = new Set(selectedModel?.recommendedSkills || []);

  // Sort so recommended come first
  const sortedSkills = [...availableSkills].sort((a, b) => {
    const aRec = recommendedIds.has(a.id) ? 0 : 1;
    const bRec = recommendedIds.has(b.id) ? 0 : 1;
    return aRec - bRec;
  });

  return (
    <motion.aside 
      className="skill-palette"
      initial={{ x: -100, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
    >
      <div className="skill-palette-header">
        <h2 className="skill-palette-title">Tools</h2>
        <p className="skill-palette-subtitle">Drag to add capabilities</p>
      </div>
      
      <div className="skill-palette-content">
        {/* Recommended section */}
        {sortedSkills.some(s => recommendedIds.has(s.id)) && (
          <motion.div 
            className="skill-category"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <div className="skill-category-header">
              <h3 className="skill-category-name">Recommended</h3>
              <span className="skill-category-badge">✦ For {selectedModel?.name || 'your model'}</span>
            </div>
            <div className="skill-category-list">
              {sortedSkills.filter(s => recommendedIds.has(s.id)).map((skill, index) => (
                <motion.div
                  key={skill.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 + 0.3 }}
                >
                  <SkillCard
                    skill={skill}
                    isInPalette
                    isRecommended
                    accentColor={selectedModel?.primaryColor}
                  />
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}

        {/* Other available tools */}
        {sortedSkills.some(s => !recommendedIds.has(s.id)) && (
          <motion.div 
            className="skill-category"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.35 }}
          >
            <div className="skill-category-header">
              <h3 className="skill-category-name">Available</h3>
              <span className="skill-category-count">
                {sortedSkills.filter(s => !recommendedIds.has(s.id)).length}
              </span>
            </div>
            <div className="skill-category-list">
              {sortedSkills.filter(s => !recommendedIds.has(s.id)).map((skill, index) => (
                <motion.div
                  key={skill.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.05 + 0.45 }}
                >
                  <SkillCard skill={skill} isInPalette />
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}

        {availableSkills.length === 0 && (
          <motion.div 
            className="skill-palette-empty"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <p>All tools added!</p>
          </motion.div>
        )}

        {/* Coming soon section */}
        <motion.div
          className="skill-category coming-soon"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          <div className="skill-category-header">
            <h3 className="skill-category-name">Coming Soon</h3>
          </div>
          <div className="coming-soon-list">
            {comingSoonSkills.map((skill) => (
              <div key={skill.name} className="coming-soon-item">
                <span className="coming-soon-icon">{skill.icon}</span>
                <div className="coming-soon-info">
                  <span className="coming-soon-name">{skill.name}</span>
                  <span className="coming-soon-desc">{skill.description}</span>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </motion.aside>
  );
}
