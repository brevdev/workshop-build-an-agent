/**
 * SVG brand icons for each model, styled to match their brand colors.
 */

interface IconProps {
  size?: number;
  color?: string;
}

export function NemotronIcon({ size = 48, color = '#76B900' }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" fill="none">
      {/* NVIDIA eye / chip shape */}
      <rect x="8" y="8" width="32" height="32" rx="6" stroke={color} strokeWidth="2.5" fill="none" />
      <rect x="14" y="14" width="20" height="20" rx="3" fill={color} opacity="0.15" />
      <circle cx="24" cy="24" r="6" fill={color} />
      <circle cx="24" cy="24" r="3" fill="#fff" opacity="0.9" />
      {/* Corner pins */}
      <circle cx="8" cy="8" r="2" fill={color} />
      <circle cx="40" cy="8" r="2" fill={color} />
      <circle cx="8" cy="40" r="2" fill={color} />
      <circle cx="40" cy="40" r="2" fill={color} />
      {/* Top/bottom traces */}
      <line x1="18" y1="4" x2="18" y2="8" stroke={color} strokeWidth="2" strokeLinecap="round" />
      <line x1="24" y1="4" x2="24" y2="8" stroke={color} strokeWidth="2" strokeLinecap="round" />
      <line x1="30" y1="4" x2="30" y2="8" stroke={color} strokeWidth="2" strokeLinecap="round" />
      <line x1="18" y1="40" x2="18" y2="44" stroke={color} strokeWidth="2" strokeLinecap="round" />
      <line x1="24" y1="40" x2="24" y2="44" stroke={color} strokeWidth="2" strokeLinecap="round" />
      <line x1="30" y1="40" x2="30" y2="44" stroke={color} strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

export function LlamaIcon({ size = 48, color = '#0668E1' }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" fill="none">
      {/* Llama silhouette */}
      <path
        d="M16 40V28L12 20V12L16 8L20 6L24 8V12L22 16L24 20L28 18L32 20V14L36 10L40 12V20L38 28V40"
        stroke={color}
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill={color}
        fillOpacity="0.12"
      />
      {/* Eye */}
      <circle cx="18" cy="12" r="1.5" fill={color} />
      {/* Ground line */}
      <line x1="10" y1="40" x2="42" y2="40" stroke={color} strokeWidth="2" strokeLinecap="round" opacity="0.4" />
    </svg>
  );
}

export function DeepSeekIcon({ size = 48, color = '#4D6BFE' }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" fill="none">
      {/* Magnifying glass / deep search motif */}
      <circle cx="22" cy="22" r="12" stroke={color} strokeWidth="2.5" fill={color} fillOpacity="0.1" />
      <line x1="31" y1="31" x2="40" y2="40" stroke={color} strokeWidth="3" strokeLinecap="round" />
      {/* Brain / neural pattern inside lens */}
      <path
        d="M18 18C18 18 20 22 22 22C24 22 22 18 24 18C26 18 24 22 26 22"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="18" cy="22" r="1" fill={color} />
      <circle cx="26" cy="18" r="1" fill={color} />
      {/* Sparkle / depth indicator */}
      <circle cx="16" cy="16" r="1.5" fill={color} opacity="0.5" />
    </svg>
  );
}

export function ClaudeIcon({ size = 48, color = '#D97757' }: IconProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" fill="none">
      {/* Anthropic starburst / sparkle shape */}
      <path
        d="M24 6L27 18L38 14L30 24L38 34L27 30L24 42L21 30L10 34L18 24L10 14L21 18Z"
        fill={color}
        fillOpacity="0.15"
        stroke={color}
        strokeWidth="2"
        strokeLinejoin="round"
      />
      {/* Inner circle */}
      <circle cx="24" cy="24" r="5" fill={color} opacity="0.6" />
      <circle cx="24" cy="24" r="2.5" fill="#fff" opacity="0.8" />
    </svg>
  );
}

export function ModelIcon({ modelId, size = 48 }: { modelId: string; size?: number }) {
  switch (modelId) {
    case 'nemotron': return <NemotronIcon size={size} />;
    case 'llama': return <LlamaIcon size={size} />;
    case 'deepseek': return <DeepSeekIcon size={size} />;
    case 'claude': return <ClaudeIcon size={size} />;
    default: return <NemotronIcon size={size} />;
  }
}
