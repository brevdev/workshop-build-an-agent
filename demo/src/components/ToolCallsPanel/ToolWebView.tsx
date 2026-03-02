import { useEffect, useRef, useMemo, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { Skill } from '../../data/skills';
import type { ToolCall } from './ToolCallsPanel';

interface ToolWebViewProps {
  skills: Skill[];
  toolCalls: ToolCall[];
  activeToolId: string | null;
}

interface NodePosition {
  x: number;
  y: number;
}

export function ToolWebView({ skills, toolCalls, activeToolId }: ToolWebViewProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const animFrameRef = useRef<number>();
  const pulsePhaseRef = useRef(0);
  const shakeRef = useRef({ x: 0, y: 0, intensity: 0 });
  const [size, setSize] = useState({ w: 340, h: 400 });

  // Dynamically measure the container
  const updateSize = useCallback(() => {
    const el = containerRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    setSize({ w: rect.width, h: rect.height });
  }, []);

  useEffect(() => {
    updateSize();
    const obs = new ResizeObserver(updateSize);
    if (containerRef.current) obs.observe(containerRef.current);
    return () => obs.disconnect();
  }, [updateSize]);

  // Center point derived from measured size
  const cx = size.w / 2;
  const cy = size.h / 2;
  const radius = Math.min(size.w, size.h) * 0.36;

  // Calculate node positions in a circular layout around the center
  const nodePositions = useMemo((): Map<string, NodePosition> => {
    const map = new Map<string, NodePosition>();
    skills.forEach((skill, i) => {
      const angle = (i / skills.length) * Math.PI * 2 - Math.PI / 2;
      map.set(skill.id, {
        x: cx + Math.cos(angle) * radius,
        y: cy + Math.sin(angle) * radius,
      });
    });
    return map;
  }, [skills, cx, cy, radius]);

  // Track which tools have been called
  const calledToolIds = useMemo(() => {
    const set = new Set<string>();
    toolCalls.forEach(tc => {
      if (tc.status === 'success' || tc.status === 'running') {
        set.add(tc.skillId);
      }
    });
    return set;
  }, [toolCalls]);

  // Canvas animation for connection lines and particles
  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const resize = () => {
      const rect = container.getBoundingClientRect();
      canvas.width = rect.width;
      canvas.height = rect.height;
    };
    resize();

    // Particles for active connections
    const particles: Array<{
      x: number; y: number;
      tx: number; ty: number;
      progress: number;
      speed: number;
      skillId: string;
    }> = [];

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      pulsePhaseRef.current += 0.02;

      // Shake decay
      if (shakeRef.current.intensity > 0) {
        shakeRef.current.intensity *= 0.92;
        shakeRef.current.x = (Math.random() - 0.5) * shakeRef.current.intensity;
        shakeRef.current.y = (Math.random() - 0.5) * shakeRef.current.intensity;
      }

      // Draw connections from robot to each skill
      skills.forEach(skill => {
        const pos = nodePositions.get(skill.id);
        if (!pos) return;

        const isActive = activeToolId === skill.id;
        const isCalled = calledToolIds.has(skill.id);

        ctx.beginPath();
        ctx.moveTo(cx + shakeRef.current.x, cy + shakeRef.current.y);
        ctx.lineTo(pos.x, pos.y);

        if (isActive) {
          ctx.strokeStyle = 'rgba(118, 185, 0, 0.8)';
          ctx.lineWidth = 2.5;
          ctx.shadowColor = 'rgba(118, 185, 0, 0.6)';
          ctx.shadowBlur = 10;
        } else if (isCalled) {
          ctx.strokeStyle = 'rgba(118, 185, 0, 0.25)';
          ctx.lineWidth = 1.5;
          ctx.shadowColor = 'transparent';
          ctx.shadowBlur = 0;
        } else {
          ctx.strokeStyle = 'rgba(100, 100, 100, 0.15)';
          ctx.lineWidth = 1;
          ctx.shadowColor = 'transparent';
          ctx.shadowBlur = 0;
        }
        ctx.stroke();
        ctx.shadowBlur = 0;

        // Spawn particles for active tool
        if (isActive && Math.random() < 0.15) {
          particles.push({
            x: cx, y: cy,
            tx: pos.x, ty: pos.y,
            progress: 0,
            speed: 0.015 + Math.random() * 0.01,
            skillId: skill.id,
          });
        }
      });

      // Draw & update particles
      for (let i = particles.length - 1; i >= 0; i--) {
        const p = particles[i];
        p.progress += p.speed;

        if (p.progress >= 1) {
          particles.splice(i, 1);
          continue;
        }

        const px = p.x + (p.tx - p.x) * p.progress;
        const py = p.y + (p.ty - p.y) * p.progress;
        const alpha = p.progress < 0.5
          ? p.progress * 2
          : 2 - p.progress * 2;

        ctx.beginPath();
        ctx.arc(px, py, 3, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(118, 185, 0, ${alpha * 0.8})`;
        ctx.shadowColor = 'rgba(118, 185, 0, 0.8)';
        ctx.shadowBlur = 8;
        ctx.fill();
        ctx.shadowBlur = 0;
      }

      // Draw robot glow ring
      const glowAlpha = 0.1 + Math.sin(pulsePhaseRef.current) * 0.05;
      ctx.beginPath();
      ctx.arc(cx + shakeRef.current.x, cy + shakeRef.current.y, 30, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(118, 185, 0, ${activeToolId ? glowAlpha + 0.1 : glowAlpha})`;
      ctx.fill();

      animFrameRef.current = requestAnimationFrame(draw);
    };

    draw();

    const resizeObs = new ResizeObserver(() => {
      resize();
      updateSize();
    });
    resizeObs.observe(container);

    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
      resizeObs.disconnect();
    };
  }, [skills, nodePositions, activeToolId, calledToolIds, cx, cy, updateSize]);

  // Trigger shake when activeToolId changes
  useEffect(() => {
    if (activeToolId) {
      shakeRef.current.intensity = 8;
    }
  }, [activeToolId]);

  return (
    <div className="tool-web-view" ref={containerRef}>
      {/* Canvas for lines and particles */}
      <canvas ref={canvasRef} className="web-canvas" />

      {/* Robot node (center) — 52px is the node size, offset by half */}
      <motion.div
        className={`web-robot-node ${activeToolId ? 'active' : ''}`}
        style={{ left: cx - 26, top: cy - 26 }}
        animate={activeToolId ? {
          x: [0, -3, 3, -2, 2, 0],
          y: [0, 2, -2, 1, -1, 0],
        } : { x: 0, y: 0 }}
        transition={activeToolId ? {
          duration: 0.4,
          repeat: Infinity,
          repeatType: 'loop',
        } : { duration: 0.3 }}
      >
        <div className="robot-node-inner">
          <span className="robot-emoji">🤖</span>
        </div>
        {activeToolId && (
          <motion.div
            className="robot-pulse-ring"
            initial={{ scale: 1, opacity: 0.6 }}
            animate={{ scale: 2, opacity: 0 }}
            transition={{ duration: 1, repeat: Infinity }}
          />
        )}
      </motion.div>

      {/* Skill nodes */}
      <AnimatePresence>
        {skills.map((skill) => {
          const pos = nodePositions.get(skill.id);
          if (!pos) return null;

          const isActive = activeToolId === skill.id;
          const isCalled = calledToolIds.has(skill.id);
          const callCount = toolCalls.filter(t => t.skillId === skill.id && t.status === 'success').length;

          {/* 38px is the skill node size, offset by half; +10 for label below */}
          return (
            <motion.div
              key={skill.id}
              className={`web-skill-node ${isActive ? 'active' : ''} ${isCalled ? 'called' : ''}`}
              style={{ left: pos.x - 19, top: pos.y - 19 }}
              initial={{ scale: 0, opacity: 0 }}
              animate={{
                scale: isActive ? 1.2 : 1,
                opacity: 1,
              }}
              transition={{
                scale: { type: 'spring', stiffness: 400, damping: 15 },
              }}
            >
              <div className="skill-node-inner">
                <span className="skill-node-icon">{skill.icon}</span>
                {/* Glow rings for active — inside inner so inset:0 works */}
                {isActive && (
                  <>
                    <motion.div
                      className="node-glow-ring"
                      initial={{ scale: 1, opacity: 0.5 }}
                      animate={{ scale: 2.5, opacity: 0 }}
                      transition={{ duration: 0.8, repeat: Infinity }}
                    />
                    <motion.div
                      className="node-glow-ring delay"
                      initial={{ scale: 1, opacity: 0.3 }}
                      animate={{ scale: 2, opacity: 0 }}
                      transition={{ duration: 0.8, repeat: Infinity, delay: 0.3 }}
                    />
                  </>
                )}
              </div>
              <span className="skill-node-label">{skill.name}</span>
              {callCount > 0 && (
                <span className="skill-node-badge">{callCount}</span>
              )}
            </motion.div>
          );
        })}
      </AnimatePresence>

      {/* Active tool call indicator */}
      <AnimatePresence>
        {activeToolId && (
          <motion.div
            className="web-active-label"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
          >
            <span className="active-label-dot" />
            Calling {skills.find(s => s.id === activeToolId)?.name}...
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
