import { motion, AnimatePresence } from 'framer-motion';
import './BuildButton.css';

interface BuildButtonProps {
  disabled: boolean;
  isBuilding: boolean;
  isReady: boolean;
  onClick: () => void;
  skillCount: number;
}

export function BuildButton({ disabled, isBuilding, isReady, onClick, skillCount }: BuildButtonProps) {
  return (
    <motion.div 
      className="build-button-container"
      initial={{ y: 50, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ delay: 0.5, duration: 0.5 }}
    >
      <AnimatePresence mode="wait">
        {isReady ? (
          <motion.div
            key="ready"
            className="build-success"
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0, opacity: 0 }}
          >
            <div className="success-icon">✓</div>
            <div className="success-text">
              <h3>Agent Ready!</h3>
              <p>{skillCount} skills configured</p>
            </div>
            <button 
              className="reset-button"
              onClick={onClick}
            >
              Build Another
            </button>
          </motion.div>
        ) : (
          <motion.button
            key="build"
            className={`build-button ${disabled ? 'disabled' : 'active'} ${isBuilding ? 'building' : ''}`}
            onClick={onClick}
            disabled={disabled || isBuilding}
            whileHover={!disabled && !isBuilding ? { scale: 1.02 } : {}}
            whileTap={!disabled && !isBuilding ? { scale: 0.98 } : {}}
          >
            {/* Background glow effect */}
            <div className="button-glow" />
            
            {/* Button content */}
            <div className="button-content">
              {isBuilding ? (
                <>
                  <motion.div 
                    className="building-spinner"
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                  />
                  <span>Building Agent...</span>
                </>
              ) : (
                <>
                  <span className="button-icon">⚡</span>
                  <span>Build Agent</span>
                  {!disabled && (
                    <span className="skill-badge">{skillCount} skills</span>
                  )}
                </>
              )}
            </div>

            {/* Animated border */}
            <svg className="button-border" viewBox="0 0 100 100" preserveAspectRatio="none">
              <motion.rect
                x="0"
                y="0"
                width="100"
                height="100"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                initial={{ pathLength: 0 }}
                animate={!disabled ? { pathLength: 1 } : { pathLength: 0 }}
                transition={{ duration: 0.5 }}
              />
            </svg>

            {/* Particle effects when active */}
            {!disabled && !isBuilding && (
              <div className="button-particles">
                {[...Array(6)].map((_, i) => (
                  <motion.div
                    key={i}
                    className="particle"
                    animate={{
                      y: [-20, -40],
                      opacity: [0, 1, 0],
                      scale: [0.5, 1, 0.5],
                    }}
                    transition={{
                      duration: 2,
                      repeat: Infinity,
                      delay: i * 0.3,
                      ease: 'easeOut',
                    }}
                    style={{
                      left: `${15 + i * 14}%`,
                    }}
                  />
                ))}
              </div>
            )}
          </motion.button>
        )}
      </AnimatePresence>

      {/* Hint text */}
      <AnimatePresence>
        {disabled && !isReady && (
          <motion.p
            className="build-hint"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            Add at least one skill to build your agent
          </motion.p>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
