export interface ModelDef {
  id: string;
  name: string;
  provider: string;
  tagline: string;
  icon: string;
  primaryColor: string;
  accentColor: string;
  glowColor: string;
  subtleColor: string;
  backendModel: string;
  recommendedSkills?: string[];
}

export interface NemotronVariant {
  id: string;
  name: string;
  subtitle: string;
  description: string;
  icon: string;
  color: string;
  glowColor: string;
  available: boolean;
  backendModel: string;
}

export const nemotronVariants: NemotronVariant[] = [
  {
    id: 'nemotron',
    name: 'Nemotron',
    subtitle: 'General Purpose',
    description: 'NVIDIA\'s flagship reasoning model for any task',
    icon: '🧠',
    color: '#76B900',
    glowColor: 'rgba(118, 185, 0, 0.4)',
    available: true,
    backendModel: 'nvidia/llama-3.3-nemotron-super-49b-v1.5',
  },
  {
    id: 'nemotron-finance',
    name: 'Nemotron',
    subtitle: 'Finance',
    description: 'Fine-tuned for financial analysis, markets & risk',
    icon: '📊',
    color: '#0088FF',
    glowColor: 'rgba(0, 136, 255, 0.4)',
    available: true,
    backendModel: 'nvidia/llama-3.3-nemotron-super-49b-v1.5',
  },
  {
    id: 'nemotron-code',
    name: 'Nemotron',
    subtitle: 'Code',
    description: 'Fine-tuned for software engineering & CUDA',
    icon: '💻',
    color: '#A855F7',
    glowColor: 'rgba(168, 85, 247, 0.4)',
    available: true,
    backendModel: 'nvidia/llama-3.3-nemotron-super-49b-v1.5',
  },
  {
    id: 'nemotron-legal',
    name: 'Nemotron',
    subtitle: 'Legal',
    description: 'Fine-tuned for legal research & compliance',
    icon: '⚖️',
    color: '#F59E0B',
    glowColor: 'rgba(245, 158, 11, 0.4)',
    available: true,
    backendModel: 'nvidia/llama-3.3-nemotron-super-49b-v1.5',
  },
];

export const models: ModelDef[] = [
  {
    id: 'nemotron',
    name: 'Nemotron',
    provider: 'NVIDIA',
    tagline: 'NVIDIA\'s flagship reasoning model',
    icon: '🟢',
    primaryColor: '#76B900',
    accentColor: '#8dc63f',
    glowColor: 'rgba(118, 185, 0, 0.4)',
    subtleColor: 'rgba(118, 185, 0, 0.1)',
    backendModel: 'nvidia/llama-3.3-nemotron-super-49b-v1.5',
    recommendedSkills: ['websearch', 'superpowers', 'rag'],
  },
  {
    id: 'llama',
    name: 'Llama',
    provider: 'Meta',
    tagline: 'Meta\'s open-weight powerhouse',
    icon: '🦙',
    primaryColor: '#0668E1',
    accentColor: '#1877F2',
    glowColor: 'rgba(6, 104, 225, 0.4)',
    subtleColor: 'rgba(6, 104, 225, 0.1)',
    backendModel: 'meta/llama-3.3-70b-instruct',
    recommendedSkills: ['websearch', 'superpowers', 'rag'],
  },
  {
    id: 'deepseek',
    name: 'DeepSeek',
    provider: 'DeepSeek',
    tagline: 'Deep reasoning & code specialist',
    icon: '🔮',
    primaryColor: '#4D6BFE',
    accentColor: '#7B8FFE',
    glowColor: 'rgba(77, 107, 254, 0.4)',
    subtleColor: 'rgba(77, 107, 254, 0.1)',
    backendModel: 'deepseek-ai/deepseek-r1-0528',
    recommendedSkills: ['websearch', 'superpowers'],
  },
  {
    id: 'claude',
    name: 'Claude',
    provider: 'Anthropic',
    tagline: 'Thoughtful & articulate assistant',
    icon: '🧡',
    primaryColor: '#D97757',
    accentColor: '#E8956A',
    glowColor: 'rgba(217, 119, 87, 0.4)',
    subtleColor: 'rgba(217, 119, 87, 0.1)',
    backendModel: 'meta/llama-3.3-70b-instruct', // Fallback until Anthropic key added
    recommendedSkills: ['fileio', 'execute'],
  },
];
