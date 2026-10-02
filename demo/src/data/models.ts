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

// Display settings only. The backend supplies supported IDs and model endpoints.
export const models: ModelDef[] = [
  {
    id: 'nemotron', name: 'Nemotron Super', provider: 'NVIDIA',
    tagline: 'Reasoning for complex agent tasks', icon: '🟢',
    primaryColor: '#76B900', accentColor: '#8dc63f',
    glowColor: 'rgba(118,185,0,0.4)', subtleColor: 'rgba(118,185,0,0.1)',
    backendModel: '', recommendedSkills: ['websearch', 'superpowers', 'rag'],
  },
  {
    id: 'nemotron_fast', name: 'Nemotron Lightning', provider: 'NVIDIA',
    tagline: 'Fast responses for everyday tasks', icon: '⚡',
    primaryColor: '#76B900', accentColor: '#8dc63f',
    glowColor: 'rgba(118,185,0,0.4)', subtleColor: 'rgba(118,185,0,0.1)',
    backendModel: '', recommendedSkills: ['websearch', 'fileio', 'execute'],
  },
];
