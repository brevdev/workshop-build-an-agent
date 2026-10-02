/**
 * API client for the Deep Agent backend.
 * Session-based: create an agent, chat, approve/reject interrupted tools.
 */

export interface TokenEvent { type: 'token'; content: string; }
export interface ToolStartEvent { type: 'tool_start'; id: string; name: string; skillId: string; icon: string; action: string; input: string; }
export interface ToolEndEvent { type: 'tool_end'; id: string; name: string; output: string; duration: number; status: 'success' | 'error'; }
export interface ErrorEvent { type: 'error'; message: string; }
export interface DoneEvent { type: 'done'; }
export interface InterruptEvent {
  type: 'interrupt';
  actionRequests: Array<{ name: string; args: Record<string, unknown>; description: string }>;
  allowedDecisions: string[];
}
export interface UsageEvent { type: 'usage'; inputTokens: number; outputTokens: number; totalTokens: number; reasoningTokens: number; }

export type AgentEvent = TokenEvent | ToolStartEvent | ToolEndEvent | ErrorEvent | DoneEvent | InterruptEvent | UsageEvent;


/**
 * Actual capabilities of a successfully created session.
 */
export interface AgentSessionInfo {
  sessionId: string;
  sandboxRequested: boolean;
  sandboxActive: boolean;
  enabledTools: string[];
  capabilities: {
    file_root: string | null;
    execution: 'container' | 'host user' | 'disabled';
    container_network: string | null;
    web_and_rag: string;
  };
}

export async function getAvailableModels(): Promise<Array<{ id: string; name: string; model: string }>> {
  const response = await fetch('api/models');
  if (!response.ok) throw new Error('Could not load models. Check that the Deep Agents backend is running.');
  const data = await response.json();
  if (!Array.isArray(data.models) || !data.models.length) throw new Error('No models are configured.');
  return data.models;
}

/**
 * Create a new agent session.
 */
export async function createAgentSession(
  modelId: string,
  skillIds: string[],
  hitlEnabled: boolean = false,
  sandboxMap: Record<string, boolean> = {},
): Promise<AgentSessionInfo> {
  const response = await fetch('api/agent', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ model_id: modelId, skill_ids: skillIds, hitl_enabled: hitlEnabled, sandbox_map: sandboxMap }),
  });
  if (!response.ok) {
    const failure = await response.json().catch(() => ({}));
    throw new Error(typeof failure.detail === 'string' ? failure.detail
      : 'Could not build your agent. Check the backend terminal and try again.');
  }
  const data = await response.json();
  if (typeof data.session_id !== 'string' || !data.session_id) throw new Error('The backend did not create a session. Try again.');
  return {
    sessionId: data.session_id,
    sandboxRequested: Boolean(data.sandbox_requested),
    sandboxActive: Boolean(data.sandbox_active),
    enabledTools: data.enabled_tools ?? [],
    capabilities: data.capabilities,
  };
}

/**
 * Delete an agent session.
 */
export async function deleteAgentSession(sessionId: string): Promise<void> {
  try { await fetch(`api/agent/${sessionId}`, { method: 'DELETE' }); } catch { /* ignore */ }
}

/**
 * Send a message and stream the response via SSE.
 */
export async function sendMessage(
  sessionId: string,
  message: string,
  onEvent: (event: AgentEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch(`api/agent/${sessionId}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
    signal,
  });

  if (!response.ok) {
    onEvent({ type: 'error', message: `Server error ${response.status}` });
    return;
  }

  await _parseSSE(response, onEvent);
}

/**
 * Approve or reject an interrupted tool call, then continue streaming.
 */
export async function sendApproval(
  sessionId: string,
  decision: 'approve' | 'reject' | 'edit',
  onEvent: (event: AgentEvent) => void,
  editedArgs?: Record<string, unknown>,
  signal?: AbortSignal,
): Promise<void> {
  const body: Record<string, unknown> = { decision };
  if (decision === 'edit' && editedArgs) {
    body.edited_args = editedArgs;
  }

  const response = await fetch(`api/agent/${sessionId}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal,
  });

  if (!response.ok) {
    onEvent({ type: 'error', message: `Approval failed: ${response.status}` });
    return;
  }

  await _parseSSE(response, onEvent);
}


// ── SSE parser ──────────────────────────────────────────────────────────────

async function _parseSSE(response: Response, onEvent: (event: AgentEvent) => void): Promise<void> {
  const reader = response.body?.getReader();
  if (!reader) { onEvent({ type: 'error', message: 'No response body' }); return; }

  const decoder = new TextDecoder();
  let buffer = '';
  let finished = false;

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer = (buffer + decoder.decode(value, { stream: true })).replace(/\r\n/g, '\n');

      let blockEnd: number;
      while ((blockEnd = buffer.indexOf('\n\n')) !== -1) {
        const block = buffer.substring(0, blockEnd);
        buffer = buffer.substring(blockEnd + 2);

        let eventType = '';
        const dataLines: string[] = [];
        for (const line of block.split('\n')) {
          if (line.startsWith('event:')) eventType = line.substring(6).trim();
          else if (line.startsWith('data:')) dataLines.push(line.substring(5).trim());
        }
        const eventData = dataLines.join('\n');

        if (!eventType || !eventData) continue;

        try {
          const parsed = JSON.parse(eventData);
          if (['done', 'error', 'interrupt'].includes(eventType)) finished = true;
          switch (eventType) {
            case 'token': onEvent({ type: 'token', content: parsed.content || '' }); break;
            case 'tool_start': onEvent({ type: 'tool_start', id: parsed.id, name: parsed.name, skillId: parsed.skillId || 'api', icon: parsed.icon || '🔧', action: parsed.action || parsed.name, input: parsed.input || '' }); break;
            case 'tool_end': onEvent({ type: 'tool_end', id: parsed.id, name: parsed.name, output: parsed.output || '', duration: parsed.duration || 0, status: parsed.status === 'error' ? 'error' : 'success' }); break;
            case 'error': onEvent({ type: 'error', message: parsed.message || 'Unknown error' }); break;
            case 'done': onEvent({ type: 'done' }); break;
            case 'interrupt':
              onEvent({
                type: 'interrupt',
                actionRequests: parsed.action_requests || [],
                allowedDecisions: parsed.review_configs?.[0]?.allowed_decisions || ['approve', 'reject'],
              });
              break;
            case 'usage':
              onEvent({
                type: 'usage',
                inputTokens: parsed.input_tokens || 0,
                outputTokens: parsed.output_tokens || 0,
                totalTokens: parsed.total_tokens || 0,
                reasoningTokens: parsed.reasoning_tokens || 0,
              });
              break;
          }
        } catch { /* skip malformed */ }
      }
    }
    if (!finished) onEvent({ type: 'error', message: 'The connection ended before the agent finished. Check the backend terminal.' });
  } finally {
    reader.releaseLock();
  }
}
