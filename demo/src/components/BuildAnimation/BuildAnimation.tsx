import { motion, AnimatePresence } from 'framer-motion';
import { useEffect, useState } from 'react';
import './BuildAnimation.css';

interface BuildAnimationProps {
  isActive: boolean;
  onComplete: () => void;
  sessionReady?: boolean;
  extendedBuild?: boolean;
}

export function BuildAnimation({ isActive, onComplete, sessionReady = false, extendedBuild = false }: BuildAnimationProps) {
  const [minChargingDone, setMinChargingDone] = useState(false);
  const [burstDone, setBurstDone] = useState(false);
  const phase = !isActive ? 'idle' : minChargingDone && sessionReady ? burstDone ? 'complete' : 'burst' : 'charging';
  const statusMessage = extendedBuild ? 'Preparing your agent and knowledge base…' : 'Preparing your agent…';

  useEffect(() => {
    if (!isActive) return;
    const timer = setTimeout(() => setMinChargingDone(true), 1500);
    return () => clearTimeout(timer);
  }, [isActive]);

  // Every build waits for a real session, including builds without RAG.
  useEffect(() => {
    if (!isActive || !minChargingDone || !sessionReady) return;
    const timer = setTimeout(() => { setBurstDone(true); onComplete(); }, 1000);
    return () => clearTimeout(timer);
  }, [isActive, minChargingDone, sessionReady, onComplete]);

  return (
    <AnimatePresence>
      {isActive && (
        <motion.div
          className="build-animation-overlay"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          {/* Radial energy lines */}
          <div className="energy-lines">
            {[...Array(12)].map((_, i) => (
              <motion.div
                key={i}
                className="energy-line"
                style={{
                  transform: `rotate(${i * 30}deg)`,
                }}
                initial={{ scaleY: 0, opacity: 0 }}
                animate={phase === 'charging' || phase === 'burst' ? {
                  scaleY: [0, 1, 0],
                  opacity: [0, 1, 0],
                } : {}}
                transition={{
                  duration: 1.5,
                  delay: i * 0.05,
                  ease: 'easeOut',
                  ...(extendedBuild ? { repeat: Infinity, repeatType: 'loop' as const } : {}),
                }}
              />
            ))}
          </div>

          {/* Central burst */}
          <AnimatePresence>
            {phase === 'burst' && (
              <motion.div
                className="central-burst"
                initial={{ scale: 0, opacity: 1 }}
                animate={{ scale: 3, opacity: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.8, ease: 'easeOut' }}
              />
            )}
          </AnimatePresence>

          {/* Particle explosion */}
          <AnimatePresence>
            {phase === 'burst' && (
              <div className="particle-explosion">
                {[...Array(24)].map((_, i) => {
                  const angle = (i / 24) * Math.PI * 2;
                  const distance = 200 + (i * 37) % 100;
                  return (
                    <motion.div
                      key={i}
                      className="explosion-particle"
                      initial={{
                        x: 0,
                        y: 0,
                        scale: 1,
                        opacity: 1,
                      }}
                      animate={{
                        x: Math.cos(angle) * distance,
                        y: Math.sin(angle) * distance,
                        scale: 0,
                        opacity: 0,
                      }}
                      transition={{
                        duration: 0.8,
                        ease: 'easeOut',
                      }}
                    />
                  );
                })}
              </div>
            )}
          </AnimatePresence>

          {/* Screen flash */}
          <AnimatePresence>
            {phase === 'burst' && (
              <motion.div
                className="screen-flash"
                initial={{ opacity: 0 }}
                animate={{ opacity: [0, 0.8, 0] }}
                transition={{ duration: 0.3 }}
              />
            )}
          </AnimatePresence>

          {/* Progress ring */}
          <svg className="progress-ring" viewBox="0 0 100 100">
            <circle
              className="progress-ring-bg"
              cx="50"
              cy="50"
              r="45"
              fill="none"
              strokeWidth="2"
            />
            <motion.circle
              className="progress-ring-fill"
              cx="50"
              cy="50"
              r="45"
              fill="none"
              strokeWidth="3"
              strokeLinecap="round"
              initial={{ pathLength: 0 }}
              animate={
                phase === 'idle'
                  ? { pathLength: 0 }
                  : extendedBuild && phase === 'charging'
                    ? { pathLength: 0.8 }
                    : { pathLength: 1 }
              }
              transition={{
                duration: extendedBuild && phase === 'charging' ? 8 : 2,
                ease: 'easeInOut',
              }}
              style={{
                transformOrigin: 'center',
                transform: 'rotate(-90deg)',
              }}
            />
          </svg>

          {/* Status text */}
          <motion.div
            className="build-status"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            {phase === 'charging' && statusMessage}
            {phase === 'burst' && 'Activating skills...'}
            {phase === 'complete' && 'Agent Ready!'}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
