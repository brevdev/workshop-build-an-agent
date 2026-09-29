/**
 * Hook that polls Ryan's blocky-bits physical block API.
 * Returns current skill blocks and model block detected on the workspace.
 * Gracefully handles blocky-bits not running (returns empty arrays).
 */

import { useState, useEffect, useRef, useCallback } from 'react';

// Map blocky-bits block names → our skill IDs
const SKILL_BLOCK_MAP: Record<string, string> = {
  'Google': 'websearch',
  'weather': 'websearch',
  'GitHub': 'github',       // future
  'Linear': 'linear',       // future
};

// Map blocky-bits block names → our model IDs
const MODEL_BLOCK_MAP: Record<string, string> = {
  'NVIDIA': 'nemotron',
  'Lightning': 'nemotron_fast',
};

interface BlockyBitsResponse {
  refreshing: boolean;
  skill_blocks: Array<{ name: string; [key: string]: unknown }>;
  model_blocks: Array<{ name: string; [key: string]: unknown }>;
}

export interface UseBlockyBitsResult {
  connected: boolean;
  skillIds: string[];
  modelId: string | null;
  rawSkillBlocks: string[];
  rawModelBlock: string | null;
}

const POLL_INTERVAL = 1000; // 1 second

export function useBlockyBits(enabled: boolean = true, onUpdate?: (state: UseBlockyBitsResult) => void): UseBlockyBitsResult {
  const [connected, setConnected] = useState(false);
  const [skillIds, setSkillIds] = useState<string[]>([]);
  const [modelId, setModelId] = useState<string | null>(null);
  const [rawSkillBlocks, setRawSkillBlocks] = useState<string[]>([]);
  const [rawModelBlock, setRawModelBlock] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const failCountRef = useRef(0);

  const poll = useCallback(async () => {
    if (!enabled) return;

    try {
      const response = await fetch('blocks/workspace', {
        signal: AbortSignal.timeout(2000),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data: BlockyBitsResponse = await response.json();

      // If refreshing, skip this poll
      if (data.refreshing) return;

      failCountRef.current = 0;
      setConnected(true);

      // Map skill blocks
      const blockNames = (data.skill_blocks || []).map(b => b.name);
      setRawSkillBlocks(blockNames);

      const mappedSkills = blockNames
        .map(name => SKILL_BLOCK_MAP[name])
        .filter((id): id is string => id !== undefined);
      // Deduplicate
      setSkillIds([...new Set(mappedSkills)]);

      // Map model block (take first non-empty)
      const modelBlocks = (data.model_blocks || []).map(b => b.name);
      setRawModelBlock(modelBlocks[0] || null);

      const mapped = MODEL_BLOCK_MAP[modelBlocks[0]] || null;
      setModelId(mapped);
      onUpdate?.({ connected: true, skillIds: [...new Set(mappedSkills)], modelId: mapped,
        rawSkillBlocks: blockNames, rawModelBlock: modelBlocks[0] || null });
    } catch {
      failCountRef.current++;
      // After 3 consecutive failures, mark as disconnected
      if (failCountRef.current >= 3) {
        setConnected(false);
      }
    }
  }, [enabled, onUpdate]);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    // Initial poll
    poll();

    // Set up interval
    intervalRef.current = setInterval(poll, POLL_INTERVAL);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [enabled, poll]);

  return { connected: enabled && connected, skillIds, modelId, rawSkillBlocks, rawModelBlock };
}
