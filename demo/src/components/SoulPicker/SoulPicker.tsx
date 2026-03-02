import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { models, type ModelDef, type NemotronVariant } from '../../data/models';
import { ModelIcon } from './ModelIcons';
import { NemotronVariantModal } from './NemotronVariantModal';
import './SoulPicker.css';

interface SoulPickerProps {
  onSelect: (model: ModelDef) => void;
}

export function SoulPicker({ onSelect }: SoulPickerProps) {
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [showNemotronModal, setShowNemotronModal] = useState(false);

  const activeColor = hoveredId
    ? models.find(m => m.id === hoveredId)?.primaryColor
    : selectedId
    ? models.find(m => m.id === selectedId)?.primaryColor
    : '#76B900';

  const handleSelect = (model: ModelDef) => {
    // If Nemotron, show variant picker instead
    if (model.id === 'nemotron') {
      setShowNemotronModal(true);
      return;
    }
    setSelectedId(model.id);
    setTimeout(() => onSelect(model), 900);
  };

  const handleNemotronVariant = (variant: NemotronVariant) => {
    setShowNemotronModal(false);
    // Find the base Nemotron model and override with variant's backendModel
    const nemotronBase = models.find(m => m.id === 'nemotron')!;
    const selected: ModelDef = {
      ...nemotronBase,
      id: variant.id,
      name: `${variant.name} ${variant.subtitle}`,
      tagline: variant.description,
      backendModel: variant.backendModel,
    };
    setSelectedId('nemotron');
    setTimeout(() => onSelect(selected), 600);
  };

  // Position cards around the center robot
  const positions = [
    { x: 0, y: -1 },   // top
    { x: 1, y: 0 },    // right
    { x: 0, y: 1 },    // bottom
    { x: -1, y: 0 },   // left
  ];

  return (
    <motion.div
      className="soul-picker"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ duration: 0.4 }}
    >
      {/* Title */}
      <motion.div
        className="soul-title"
        initial={{ y: -30, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.2 }}
      >
        <h1>Choose the <span className="soul-accent" style={{ color: activeColor }}>LLM</span> of Your Agent</h1>
        <p>Select the foundation model that powers your Deep Agent</p>
      </motion.div>

      {/* Center area with robot and cards */}
      <div className="soul-arena">
        {/* Ambient glow that changes color */}
        <motion.div
          className="soul-ambient"
          animate={{
            background: `radial-gradient(circle, ${hoveredId || selectedId ? (models.find(m => m.id === (hoveredId || selectedId))?.glowColor || 'rgba(118,185,0,0.15)') : 'rgba(118,185,0,0.08)'} 0%, transparent 70%)`,
          }}
          transition={{ duration: 0.5 }}
        />

        {/* Robot in the center — full idle animation */}
        <motion.div
          className={`soul-robot ${selectedId ? 'selected' : ''}`}
          initial={{ scale: 0, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.3, type: 'spring', stiffness: 200, damping: 20 }}
        >
          <motion.svg
            viewBox="0 0 200 280"
            className="soul-robot-svg"
            animate={{
              y: [0, -6, 0],
              rotate: [0, 1, 0, -1, 0],
            }}
            transition={{
              y: { duration: 3, repeat: Infinity, ease: 'easeInOut' },
              rotate: { duration: 5, repeat: Infinity, ease: 'easeInOut' },
            }}
          >
            <defs>
              <linearGradient id="soulBodyGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor="#3a3a3a" />
                <stop offset="50%" stopColor="#2a2a2a" />
                <stop offset="100%" stopColor="#1a1a1a" />
              </linearGradient>
              <filter id="soulGlow">
                <feGaussianBlur stdDeviation="3" result="blur" />
                <feMerge>
                  <feMergeNode in="blur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>

            {/* Head — bobs independently */}
            <motion.g
              animate={{ y: [0, -3, 0, -2, 0] }}
              transition={{ duration: 4, repeat: Infinity, ease: 'easeInOut' }}
            >
              <rect x="50" y="20" width="100" height="70" rx="15" fill="url(#soulBodyGrad)" stroke="#444" strokeWidth="2" />
              {/* Antenna */}
              <motion.g
                animate={{ y: [0, -3, 0] }}
                transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
              >
                <line x1="100" y1="20" x2="100" y2="5" stroke="#555" strokeWidth="3" />
                <motion.circle
                  cx="100" cy="5" r="5"
                  animate={{ fill: activeColor }}
                  transition={{ duration: 0.4 }}
                  filter="url(#soulGlow)"
                />
              </motion.g>
              {/* Eyes — blink */}
              <motion.ellipse cx="75" cy="50" rx="12"
                animate={{
                  fill: activeColor,
                  ry: [15, 15, 15, 1, 15, 15, 15, 15, 15, 1, 1, 15],
                }}
                transition={{
                  fill: { duration: 0.4 },
                  ry: { duration: 5, repeat: Infinity, ease: 'easeInOut', times: [0, 0.3, 0.38, 0.4, 0.42, 0.6, 0.78, 0.8, 0.81, 0.82, 0.84, 0.86] },
                }}
                filter="url(#soulGlow)"
              />
              <motion.ellipse cx="125" cy="50" rx="12"
                animate={{
                  fill: activeColor,
                  ry: [15, 15, 15, 1, 15, 15, 15, 15, 15, 1, 1, 15],
                }}
                transition={{
                  fill: { duration: 0.4 },
                  ry: { duration: 5, repeat: Infinity, ease: 'easeInOut', times: [0, 0.3, 0.38, 0.4, 0.42, 0.6, 0.78, 0.8, 0.81, 0.82, 0.84, 0.86] },
                }}
                filter="url(#soulGlow)"
              />
              {/* Eye highlights — hide during blink */}
              <motion.ellipse cx="78" cy="46" rx="4" fill="rgba(255,255,255,0.3)"
                animate={{ ry: [5, 5, 5, 0, 5, 5, 5, 5, 5, 0, 0, 5] }}
                transition={{ duration: 5, repeat: Infinity, ease: 'easeInOut', times: [0, 0.3, 0.38, 0.4, 0.42, 0.6, 0.78, 0.8, 0.81, 0.82, 0.84, 0.86] }}
              />
              <motion.ellipse cx="128" cy="46" rx="4" fill="rgba(255,255,255,0.3)"
                animate={{ ry: [5, 5, 5, 0, 5, 5, 5, 5, 5, 0, 0, 5] }}
                transition={{ duration: 5, repeat: Infinity, ease: 'easeInOut', times: [0, 0.3, 0.38, 0.4, 0.42, 0.6, 0.78, 0.8, 0.81, 0.82, 0.84, 0.86] }}
              />
              {/* Mouth */}
              <motion.rect x="70" y="70" width="60" height="10" rx="5" fill="#333"
                animate={{ stroke: activeColor }}
                transition={{ duration: 0.4 }}
                strokeWidth="1"
              />
            </motion.g>

            {/* Neck */}
            <rect x="85" y="90" width="30" height="15" fill="#2a2a2a" />

            {/* Body */}
            <rect x="40" y="105" width="120" height="100" rx="10" fill="url(#soulBodyGrad)" stroke="#444" strokeWidth="2" />
            <motion.rect x="55" y="115" width="90" height="80" rx="5" fill="#1a1a1a"
              animate={{ stroke: activeColor }}
              transition={{ duration: 0.4 }}
              strokeWidth="1"
            />
            {/* Core */}
            <motion.circle cx="100" cy="155" r="20"
              animate={{
                fill: activeColor,
                opacity: [0.4, 0.7, 0.4],
              }}
              transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
              filter="url(#soulGlow)"
            />
            <text x="100" y="160" textAnchor="middle" fill="#fff" fontSize="14" fontWeight="bold">?</text>

            {/* Slots */}
            {[0,1,2].map(i => (
              <motion.rect key={`l${i}`} x="45" y={120+i*25} width="8" height="20" rx="2"
                animate={{ fill: activeColor, opacity: 0.5 }}
                transition={{ duration: 0.4 }}
              />
            ))}
            {[0,1,2].map(i => (
              <motion.rect key={`r${i}`} x="147" y={120+i*25} width="8" height="20" rx="2"
                animate={{ fill: activeColor, opacity: 0.5 }}
                transition={{ duration: 0.4 }}
              />
            ))}

            {/* Arms — sway opposite */}
            <motion.g
              animate={{ rotate: [0, 3, 0, -3, 0] }}
              transition={{ duration: 3.5, repeat: Infinity, ease: 'easeInOut' }}
              style={{ transformOrigin: '29px 110px' }}
            >
              <rect x="20" y="110" width="18" height="60" rx="8" fill="url(#soulBodyGrad)" stroke="#444" strokeWidth="2" />
              <circle cx="29" cy="175" r="10" fill="#2a2a2a" stroke="#444" strokeWidth="2" />
            </motion.g>
            <motion.g
              animate={{ rotate: [0, -3, 0, 3, 0] }}
              transition={{ duration: 3.5, repeat: Infinity, ease: 'easeInOut' }}
              style={{ transformOrigin: '171px 110px' }}
            >
              <rect x="162" y="110" width="18" height="60" rx="8" fill="url(#soulBodyGrad)" stroke="#444" strokeWidth="2" />
              <circle cx="171" cy="175" r="10" fill="#2a2a2a" stroke="#444" strokeWidth="2" />
            </motion.g>

            {/* Legs */}
            <rect x="55" y="205" width="25" height="50" rx="5" fill="url(#soulBodyGrad)" stroke="#444" strokeWidth="2" />
            <rect x="120" y="205" width="25" height="50" rx="5" fill="url(#soulBodyGrad)" stroke="#444" strokeWidth="2" />
            <rect x="50" y="255" width="35" height="15" rx="5" fill="#2a2a2a" stroke="#444" strokeWidth="2" />
            <rect x="115" y="255" width="35" height="15" rx="5" fill="#2a2a2a" stroke="#444" strokeWidth="2" />
          </motion.svg>

          {/* Selection pulse */}
          <AnimatePresence>
            {selectedId && (
              <motion.div
                className="soul-select-pulse"
                style={{ borderColor: models.find(m => m.id === selectedId)?.primaryColor }}
                initial={{ scale: 0.5, opacity: 1 }}
                animate={{ scale: 2.5, opacity: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.8 }}
              />
            )}
          </AnimatePresence>
        </motion.div>

        {/* Connection lines (drawn behind cards) */}
        <svg className="soul-connections" viewBox="0 0 1040 780">
          {models.map((model, i) => {
            const pos = positions[i];
            const cx = 520, cy = 390;
            const dist = 286;
            const ex = cx + pos.x * dist;
            const ey = cy + pos.y * dist;
            const isHovered = hoveredId === model.id;
            const isSelected = selectedId === model.id;
            return (
              <motion.line
                key={model.id}
                x1={cx} y1={cy}
                x2={ex} y2={ey}
                strokeWidth={isHovered || isSelected ? 2.5 : 1}
                animate={{
                  stroke: isHovered || isSelected ? model.primaryColor : 'rgba(100,100,100,0.2)',
                }}
                transition={{ duration: 0.3 }}
                strokeLinecap="round"
              />
            );
          })}
        </svg>

        {/* Model cards — use anchor wrapper so Framer scale doesn't break CSS centering */}
        {models.map((model, i) => {
          const isHovered = hoveredId === model.id;
          const isSelected = selectedId === model.id;

          return (
            <div
              key={model.id}
              className="soul-card-anchor"
              data-position={i === 0 ? 'top' : i === 1 ? 'right' : i === 2 ? 'bottom' : 'left'}
            >
              <motion.div
                className={`soul-card ${isHovered ? 'hovered' : ''} ${isSelected ? 'selected' : ''}`}
                style={{
                  '--card-color': model.primaryColor,
                  '--card-glow': model.glowColor,
                } as React.CSSProperties}
                initial={{ opacity: 0, scale: 0 }}
                animate={{
                  opacity: selectedId && selectedId !== model.id ? 0.3 : 1,
                  scale: isSelected ? 1.1 : 1,
                }}
                transition={{ delay: 0.4 + i * 0.1, type: 'spring', stiffness: 250, damping: 20 }}
                onHoverStart={() => !selectedId && setHoveredId(model.id)}
                onHoverEnd={() => !selectedId && setHoveredId(null)}
                onClick={() => !selectedId && handleSelect(model)}
              >
                <div className="soul-card-icon">
                    <ModelIcon modelId={model.id} size={52} />
                  </div>
                <div className="soul-card-info">
                  <h3 className="soul-card-name">{model.name}</h3>
                  <span className="soul-card-provider">{model.provider}</span>
                  <p className="soul-card-tagline">{model.tagline}</p>
                </div>
                {isSelected && (
                  <motion.div
                    className="soul-card-check"
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ type: 'spring', stiffness: 400, damping: 15 }}
                  >
                    ✓
                  </motion.div>
                )}
              </motion.div>
            </div>
          );
        })}
      </div>

      {/* Nemotron variant picker modal */}
      <NemotronVariantModal
        isOpen={showNemotronModal}
        onSelect={handleNemotronVariant}
        onClose={() => setShowNemotronModal(false)}
      />
    </motion.div>
  );
}
