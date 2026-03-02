import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { Skill } from '../../data/skills';
import './RobotVisual.css';

interface RobotVisualProps {
  skills: Skill[];
  isBuilding: boolean;
  isReady: boolean;
  accentColor?: string;
}

export function RobotVisual({ skills, isBuilding, isReady, accentColor = '#76B900' }: RobotVisualProps) {
  const hasSkills = skills.length > 0;
  const c = accentColor;
  const [eyeOffset, setEyeOffset] = useState({ x: 0, y: 0 });
  const containerRef = useCallback((node: HTMLDivElement | null) => {
    if (node) containerNodeRef.current = node;
  }, []);
  const containerNodeRef = { current: null as HTMLDivElement | null };

  const handleMouseMove = useCallback((e: MouseEvent) => {
    const el = document.querySelector('.robot-container');
    if (!el) return;
    const rect = el.getBoundingClientRect();
    // Use the robot's center as reference
    const cx = rect.left + rect.width / 2;
    const cy = rect.top + rect.height / 2;
    // Distance from robot center, normalized
    const dx = (e.clientX - cx) / (window.innerWidth / 2);
    const dy = (e.clientY - cy) / (window.innerHeight / 2);
    // Clamp to max movement
    setEyeOffset({
      x: Math.max(-4, Math.min(4, dx * 4)),
      y: Math.max(-3, Math.min(3, dy * 3)),
    });
  }, []);

  useEffect(() => {
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, [handleMouseMove]);

  return (
    <div ref={containerRef} className={`robot-container ${isBuilding ? 'building' : ''} ${isReady ? 'ready' : ''}`}>
      {/* Ambient glow behind robot */}
      <div className={`robot-ambient-glow ${hasSkills ? 'active' : ''}`} />
      
      {/* Main robot SVG — idle float animation */}
      <motion.svg
        className="robot-svg"
        viewBox="0 0 200 280"
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ 
          opacity: 1, 
          scale: 1,
          y: isBuilding ? 0 : [0, -6, 0],
          rotate: isBuilding ? 0 : [0, 1, 0, -1, 0],
          filter: isBuilding ? `drop-shadow(0 0 30px ${c})` : 'none',
        }}
        transition={{ 
          duration: 0.6, 
          ease: 'easeOut',
          y: { duration: 3, repeat: Infinity, ease: 'easeInOut' },
          rotate: { duration: 5, repeat: Infinity, ease: 'easeInOut' },
        }}
      >
        {/* Definitions for gradients and filters */}
        <defs>
          <linearGradient id="bodyGradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#3a3a3a" />
            <stop offset="50%" stopColor="#2a2a2a" />
            <stop offset="100%" stopColor="#1a1a1a" />
          </linearGradient>
          
          <linearGradient id="glowGradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor={c} stopOpacity="0.8" />
            <stop offset="100%" stopColor={c} stopOpacity="0.2" />
          </linearGradient>
          
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>

          <filter id="innerGlow">
            <feGaussianBlur stdDeviation="2" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>

        {/* Robot Head — bobs up and down */}
        <motion.g
          className="robot-head"
          animate={!isBuilding ? {
            y: [0, -3, 0, -2, 0],
          } : { y: 0 }}
          transition={{
            duration: 4,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        >
          {/* Head base */}
          <rect
            x="50"
            y="20"
            width="100"
            height="70"
            rx="15"
            fill="url(#bodyGradient)"
            stroke="#444"
            strokeWidth="2"
          />
          
          {/* Antenna */}
          <motion.g
            animate={hasSkills ? { y: [0, -3, 0] } : {}}
            transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
          >
            <line x1="100" y1="20" x2="100" y2="5" stroke="#555" strokeWidth="3" />
            <circle
              cx="100"
              cy="5"
              r="5"
              fill={hasSkills ? c : '#444'}
              filter={hasSkills ? 'url(#glow)' : 'none'}
            />
          </motion.g>

          {/* Eyes — blink idle animation */}
          <g>
            <motion.ellipse
              cx="75"
              cy="50"
              rx="12"
              fill={hasSkills ? c : '#333'}
              filter={hasSkills ? 'url(#glow)' : 'none'}
              animate={isBuilding
                ? { ry: [15, 8, 15], opacity: [1, 0.5, 1] }
                : { ry: [15, 15, 15, 1, 15, 15, 15, 15, 15, 1, 1, 15] }
              }
              transition={isBuilding
                ? { duration: 0.3, repeat: Infinity }
                : { duration: 5, repeat: Infinity, ease: 'easeInOut', times: [0, 0.3, 0.38, 0.4, 0.42, 0.6, 0.78, 0.8, 0.81, 0.82, 0.84, 0.86] }
              }
            />
            <motion.ellipse
              cx="125"
              cy="50"
              rx="12"
              fill={hasSkills ? c : '#333'}
              filter={hasSkills ? 'url(#glow)' : 'none'}
              animate={isBuilding
                ? { ry: [15, 8, 15], opacity: [1, 0.5, 1] }
                : { ry: [15, 15, 15, 1, 15, 15, 15, 15, 15, 1, 1, 15] }
              }
              transition={isBuilding
                ? { duration: 0.3, repeat: Infinity }
                : { duration: 5, repeat: Infinity, ease: 'easeInOut', times: [0, 0.3, 0.38, 0.4, 0.42, 0.6, 0.78, 0.8, 0.81, 0.82, 0.84, 0.86] }
              }
            />
            {/* Eye highlights — follow cursor + hide during blink */}
            <motion.ellipse
              cx={78 + eyeOffset.x} cy={46 + eyeOffset.y} rx="4"
              fill="rgba(255,255,255,0.4)"
              animate={isBuilding ? {} : { ry: [5, 5, 5, 0, 5, 5, 5, 5, 5, 0, 0, 5] }}
              transition={{ duration: 5, repeat: Infinity, ease: 'easeInOut', times: [0, 0.3, 0.38, 0.4, 0.42, 0.6, 0.78, 0.8, 0.81, 0.82, 0.84, 0.86] }}
            />
            <motion.ellipse
              cx={128 + eyeOffset.x} cy={46 + eyeOffset.y} rx="4"
              fill="rgba(255,255,255,0.4)"
              animate={isBuilding ? {} : { ry: [5, 5, 5, 0, 5, 5, 5, 5, 5, 0, 0, 5] }}
              transition={{ duration: 5, repeat: Infinity, ease: 'easeInOut', times: [0, 0.3, 0.38, 0.4, 0.42, 0.6, 0.78, 0.8, 0.81, 0.82, 0.84, 0.86] }}
            />
          </g>

          {/* Mouth/Speaker */}
          <rect
            x="70"
            y="70"
            width="60"
            height="10"
            rx="5"
            fill="#333"
            stroke={hasSkills ? c : '#444'}
            strokeWidth="1"
          />
        </motion.g>

        {/* Neck */}
        <rect x="85" y="90" width="30" height="15" fill="#2a2a2a" />

        {/* Robot Body */}
        <g className="robot-body">
          {/* Main torso */}
          <rect
            x="40"
            y="105"
            width="120"
            height="100"
            rx="10"
            fill="url(#bodyGradient)"
            stroke="#444"
            strokeWidth="2"
          />

          {/* Chest panel */}
          <rect
            x="55"
            y="115"
            width="90"
            height="80"
            rx="5"
            fill="#1a1a1a"
            stroke={hasSkills ? c : '#333'}
            strokeWidth="1"
          />

          {/* Core energy indicator */}
          <motion.circle
            cx="100"
            cy="155"
            r={hasSkills ? 20 : 15}
            fill={hasSkills ? 'url(#glowGradient)' : '#222'}
            stroke={hasSkills ? c : '#333'}
            strokeWidth="2"
            filter={hasSkills ? 'url(#glow)' : 'none'}
            animate={hasSkills ? {
              scale: [1, 1.1, 1],
              opacity: [0.8, 1, 0.8],
            } : {}}
            transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
          />

          {/* Skill count display */}
          <text
            x="100"
            y="160"
            textAnchor="middle"
            fill={hasSkills ? '#fff' : '#555'}
            fontSize="14"
            fontWeight="bold"
            fontFamily="var(--font-family-mono)"
          >
            {skills.length}
          </text>

          {/* Side panels for skills */}
          <g className="skill-slots">
            {/* Left slots */}
            {[0, 1, 2].map((i) => (
              <motion.rect
                key={`left-${i}`}
                x="45"
                y={120 + i * 25}
                width="8"
                height="20"
                rx="2"
                fill={skills[i] ? c : '#333'}
                filter={skills[i] ? 'url(#glow)' : 'none'}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: i * 0.1 }}
              />
            ))}
            {/* Right slots */}
            {[0, 1, 2].map((i) => (
              <motion.rect
                key={`right-${i}`}
                x="147"
                y={120 + i * 25}
                width="8"
                height="20"
                rx="2"
                fill={skills[i + 3] ? c : '#333'}
                filter={skills[i + 3] ? 'url(#glow)' : 'none'}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: i * 0.1 }}
              />
            ))}
          </g>
        </g>

        {/* Arms — sway back and forth */}
        <g className="robot-arms">
          {/* Left arm */}
          <motion.g
            animate={!isBuilding ? {
              rotate: [0, 3, 0, -3, 0],
            } : { rotate: 0 }}
            transition={{
              duration: 3.5,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
            style={{ transformOrigin: '29px 110px' }}
          >
            <rect x="20" y="110" width="18" height="60" rx="8" fill="url(#bodyGradient)" stroke="#444" strokeWidth="2" />
            <circle cx="29" cy="175" r="10" fill="#2a2a2a" stroke="#444" strokeWidth="2" />
          </motion.g>
          
          {/* Right arm — sways opposite to left */}
          <motion.g
            animate={!isBuilding ? {
              rotate: [0, -3, 0, 3, 0],
            } : { rotate: 0 }}
            transition={{
              duration: 3.5,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
            style={{ transformOrigin: '171px 110px' }}
          >
            <rect x="162" y="110" width="18" height="60" rx="8" fill="url(#bodyGradient)" stroke="#444" strokeWidth="2" />
            <circle cx="171" cy="175" r="10" fill="#2a2a2a" stroke="#444" strokeWidth="2" />
          </motion.g>
        </g>

        {/* Legs */}
        <g className="robot-legs">
          <rect x="55" y="205" width="25" height="50" rx="5" fill="url(#bodyGradient)" stroke="#444" strokeWidth="2" />
          <rect x="120" y="205" width="25" height="50" rx="5" fill="url(#bodyGradient)" stroke="#444" strokeWidth="2" />
          
          {/* Feet */}
          <rect x="50" y="255" width="35" height="15" rx="5" fill="#2a2a2a" stroke="#444" strokeWidth="2" />
          <rect x="115" y="255" width="35" height="15" rx="5" fill="#2a2a2a" stroke="#444" strokeWidth="2" />
        </g>

        {/* Building animation overlay */}
        <AnimatePresence>
          {isBuilding && (
            <motion.g
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
            >
              {/* Energy lines */}
              {[...Array(8)].map((_, i) => (
                <motion.line
                  key={i}
                  x1="100"
                  y1="155"
                  x2={100 + Math.cos((i * Math.PI) / 4) * 80}
                  y2={155 + Math.sin((i * Math.PI) / 4) * 80}
                  stroke={c}
                  strokeWidth="2"
                  strokeLinecap="round"
                  initial={{ pathLength: 0, opacity: 0 }}
                  animate={{ 
                    pathLength: [0, 1, 0],
                    opacity: [0, 1, 0],
                  }}
                  transition={{
                    duration: 1.5,
                    repeat: Infinity,
                    delay: i * 0.1,
                    ease: 'easeInOut',
                  }}
                />
              ))}
            </motion.g>
          )}
        </AnimatePresence>

        {/* Ready state crown/halo */}
        <AnimatePresence>
          {isReady && (
            <motion.g
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
            >
              <motion.ellipse
                cx="100"
                cy="0"
                rx="40"
                ry="8"
                fill="none"
                stroke={c}
                strokeWidth="3"
                filter="url(#glow)"
                animate={{ 
                  ry: [8, 10, 8],
                  opacity: [0.8, 1, 0.8],
                }}
                transition={{ duration: 2, repeat: Infinity }}
              />
            </motion.g>
          )}
        </AnimatePresence>
      </motion.svg>

      {/* Skill badges around robot */}
      <div className="robot-skill-badges">
        <AnimatePresence>
          {skills.slice(0, 8).map((skill, index) => {
            const angle = (index / Math.min(skills.length, 8)) * Math.PI * 2 - Math.PI / 2;
            const radius = 220;
            const xPos = Math.cos(angle) * radius;
            const yPos = Math.sin(angle) * radius;
            
            return (
              <motion.div
                key={skill.id}
                className="robot-skill-anchor"
                style={{ x: xPos, y: yPos }}
                initial={{ scale: 0, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0, opacity: 0 }}
                transition={{ 
                  type: 'spring',
                  stiffness: 300,
                  damping: 20,
                  delay: index * 0.05,
                }}
              >
                <div className="robot-skill-badge">
                  <span className="badge-icon">{skill.icon}</span>
                  <span className="badge-name">{skill.name}</span>
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </div>
  );
}
