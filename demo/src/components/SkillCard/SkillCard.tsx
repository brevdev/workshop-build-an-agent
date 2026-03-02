import { useRef } from 'react';
import { useDraggable } from '@dnd-kit/core';
import { CSS } from '@dnd-kit/utilities';
import { motion } from 'framer-motion';
import type { Skill } from '../../data/skills';
import './SkillCard.css';

interface SkillCardProps {
  skill: Skill;
  isInPalette?: boolean;
  isRecommended?: boolean;
  accentColor?: string;
}

export function SkillCard({ skill, isInPalette = true, isRecommended = false, accentColor }: SkillCardProps) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: skill.id,
    data: skill,
  });
  const tooltipRef = useRef<HTMLDivElement>(null);

  const style = transform
    ? {
        transform: CSS.Translate.toString(transform),
      }
    : undefined;

  const handleMouseMove = (e: React.MouseEvent) => {
    if (tooltipRef.current) {
      tooltipRef.current.style.left = `${e.clientX + 12}px`;
      tooltipRef.current.style.top = `${e.clientY - 10}px`;
    }
  };

  const recommendedStyle = isRecommended && accentColor ? {
    '--rec-color': accentColor,
    '--rec-glow': `${accentColor}66`,
  } as React.CSSProperties : undefined;

  return (
    <motion.div
      ref={setNodeRef}
      style={{ ...style, ...recommendedStyle }}
      {...listeners}
      {...attributes}
      className={`skill-card ${isDragging ? 'dragging' : ''} ${isInPalette ? 'in-palette' : 'in-agent'} ${isRecommended ? 'recommended' : ''}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      layout
      onMouseMove={handleMouseMove}
    >
      {isRecommended && <div className="skill-card-rec-glow" />}
      <div className="skill-card-icon">{skill.icon}</div>
      <div className="skill-card-content">
        <h4 className="skill-card-name">{skill.name}</h4>
        {isInPalette && (
          <p className="skill-card-description">{skill.description}</p>
        )}
      </div>
      <div className="skill-card-category" data-category={skill.category}>
        {isRecommended ? '★ REC' : skill.category.toUpperCase()}
      </div>
      <div className="skill-card-glow" />
      <div className="skill-card-tooltip" ref={tooltipRef}>{skill.description}</div>
    </motion.div>
  );
}
