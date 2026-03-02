import { useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { nemotronVariants, type NemotronVariant } from '../../data/models';
import './NemotronVariantModal.css';

interface NemotronVariantModalProps {
  isOpen: boolean;
  onSelect: (variant: NemotronVariant) => void;
  onClose: () => void;
}

function VariantCard({ variant, index, onSelect }: { variant: NemotronVariant; index: number; onSelect: (v: NemotronVariant) => void }) {
  const cardRef = useRef<HTMLDivElement>(null);

  // 3D tilt on mouse move
  const handleMouseMove = (e: React.MouseEvent) => {
    if (!variant.available || !cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width - 0.5;
    const y = (e.clientY - rect.top) / rect.height - 0.5;
    cardRef.current.style.transform = `perspective(600px) rotateY(${x * 12}deg) rotateX(${-y * 12}deg) scale(1.03)`;
  };

  const handleMouseLeave = () => {
    if (!cardRef.current) return;
    cardRef.current.style.transform = 'perspective(600px) rotateY(0deg) rotateX(0deg) scale(1)';
  };

  return (
    <motion.div
      className={`variant-card ${variant.available ? 'available' : 'coming-soon'}`}
      style={{
        '--variant-color': variant.color,
        '--variant-glow': variant.glowColor,
      } as React.CSSProperties}
      initial={{ opacity: 0, y: 30, rotateX: -10 }}
      animate={{ opacity: 1, y: 0, rotateX: 0 }}
      transition={{ delay: 0.15 + index * 0.08, type: 'spring', stiffness: 200, damping: 18 }}
      onClick={() => variant.available && onSelect(variant)}
      whileTap={variant.available ? { scale: 0.95 } : {}}
    >
      <div
        ref={cardRef}
        className="variant-card-inner"
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
      >
        {/* (reserved) */}

        {/* Coming soon ribbon */}
        {!variant.available && (
          <div className="variant-ribbon">Coming Soon</div>
        )}

        {/* Icon with hover bounce */}
        <div className="variant-card-icon">
          <span className="variant-icon-inner">{variant.icon}</span>
        </div>

        <div className="variant-card-info">
          <div className="variant-card-name">{variant.name}</div>
          <div className="variant-card-type" style={{ color: variant.color }}>{variant.subtitle}</div>
          <div className="variant-card-desc">{variant.description}</div>
        </div>

        {/* Bottom glow */}
        <div className="variant-card-glow" />

        {/* Sparkle particles for available card */}
        {variant.available && (
          <div className="variant-sparkles">
            {[...Array(6)].map((_, i) => (
              <div
                key={i}
                className="sparkle"
                style={{
                  left: `${15 + i * 14}%`,
                  animationDelay: `${i * 0.4}s`,
                }}
              />
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
}

export function NemotronVariantModal({ isOpen, onSelect, onClose }: NemotronVariantModalProps) {
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            className="variant-backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.25 }}
            onClick={onClose}
          />

          {/* Modal */}
          <motion.div
            className="variant-modal"
            style={{ x: '-50%', y: '-50%' }}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            transition={{ type: 'spring', stiffness: 250, damping: 22 }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Glow trail on entrance */}
            <motion.div
              className="variant-modal-glow"
              initial={{ opacity: 0, scale: 0.5 }}
              animate={{ opacity: [0, 0.5, 0], scale: [0.5, 1.2, 1.5] }}
              transition={{ duration: 1.2, ease: 'easeOut' }}
            />

            <div className="variant-header">
              <motion.div
                className="variant-nvidia-badge"
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
              >
                NVIDIA
              </motion.div>
              <motion.h2
                className="variant-title"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.15 }}
              >
                Choose Your Nemotron
              </motion.h2>
              <motion.p
                className="variant-subtitle"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.25 }}
              >
                Select a specialized variant for your agent
              </motion.p>
            </div>

            <div className="variant-grid">
              {nemotronVariants.map((variant, i) => (
                <VariantCard
                  key={variant.id}
                  variant={variant}
                  index={i}
                  onSelect={onSelect}
                />
              ))}
            </div>

            <motion.button
              className="variant-close"
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
