/**
 * PAPR Memory Service
 *
 * Communicates with Python CoreML microservice for fast on-device memory retrieval.
 * This service maintains the <100ms latency target by:
 * - Using localhost HTTP (1-5ms overhead)
 * - Keeping CoreML embeddings in Python process (50-75ms)
 * - Local ChromaDB search (20-30ms)
 * Total: ~80-110ms end-to-end
 */

import type {
  MemorySearchParams,
  SearchResponse,
  SearchHistoryResponse,
  ApiKeysResponse,
  ToolSchema,
  MessageRequest,
  MessageResponse,
} from '../types/papr-memory.js';

export interface PaprMemoryServiceConfig {
  /** Python microservice base URL for on-device search (default: http://localhost:3001) */
  pythonServiceUrl?: string;
  /** PAPR Cloud API base URL for messages (default: https://memory.papr.ai) */
  paprCloudUrl?: string;
  /** PAPR API key for cloud services */
  paprApiKey?: string;
  /** Request timeout in milliseconds (default: 5000) */
  timeout?: number;
  /** Enable debug logging (default: false) */
  debug?: boolean;
}

export class PaprMemoryService {
  private pythonServiceUrl: string;
  private paprCloudUrl: string;
  private paprApiKey: string | undefined;
  private timeout: number;
  private debug: boolean;

  constructor(config: PaprMemoryServiceConfig = {}) {
    this.pythonServiceUrl = config.pythonServiceUrl || 'http://localhost:3001';
    this.paprCloudUrl = config.paprCloudUrl || 'https://memory.papr.ai';
    this.paprApiKey = config.paprApiKey;
    this.timeout = config.timeout || 5000;
    this.debug = config.debug || false;
  }

  /**
   * Search memories using CoreML on-device embedding
   *
   * @param params - Search parameters (validated against Pydantic schema)
   * @returns Search results with latency breakdown
   *
   * @example
   * ```ts
   * const results = await service.search({
   *   query: "What are my current project priorities?",
   *   enable_agentic_graph: false,
   *   max_memories: 30
   * });
   * console.log(`Found ${results.data.memories.length} memories in ${results.latency_ms}ms`);
   * ```
   */
  async search(params: MemorySearchParams): Promise<SearchResponse> {
    const startTime = performance.now();

    if (this.debug) {
      console.log('🔍 [PaprMemoryService] Searching with params:', params);
    }

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout);

      const response = await fetch(`${this.pythonServiceUrl}/api/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...params,
          enable_agentic_graph: params.enable_agentic_graph ?? false,
          max_memories: params.max_memories ?? 30,
          max_nodes: params.max_nodes ?? 10,
          rank_results: params.rank_results ?? true, // PAPR optimization for CoreML
        }),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const error = await response.json() as { error?: string };
        throw new Error(
          `Python microservice error (${response.status}): ${error.error || 'Unknown error'}`
        );
      }

      const data = await response.json() as SearchResponse;
      const totalTime = performance.now() - startTime;

      if (this.debug) {
        console.log(
          `✅ [PaprMemoryService] Search completed in ${totalTime.toFixed(1)}ms (Python: ${data.latency_ms}ms)`
        );
        console.log(
          `   └─ Latency breakdown: embedding=${data.latency_breakdown.embedding_generation_ms}ms, ` +
            `search=${data.latency_breakdown.chromadb_search_ms}ms, ` +
            `overhead=${data.latency_breakdown.processing_overhead_ms}ms`
        );
      }

      return data;
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        throw new Error(
          `Search timeout after ${this.timeout}ms. Python CoreML microservice may be slow or unavailable.`
        );
      }
      throw error;
    }
  }

  /**
   * Store a conversation message with automatic AI processing
   *
   * This calls PAPR Cloud (not local Python) to:
   * 1. Store the message in the conversation history
   * 2. Queue for background AI analysis (when process_messages=true)
   * 3. Automatically create memories with role-based categorization
   *
   * @param message - Message to store
   * @returns Storage confirmation with message ID
   *
   * @example
   * ```ts
   * // Store user message with auto-processing
   * await service.storeMessage({
   *   content: "I need to finish the Q4 roadmap by next week",
   *   role: "user",
   *   sessionId: "voice_session_123",
   *   process_messages: true // AI will create memories automatically
   * });
   *
   * // Store assistant message
   * await service.storeMessage({
   *   content: "I found 5 memories about your roadmap planning",
   *   role: "assistant",
   *   sessionId: "voice_session_123"
   * });
   * ```
   */
  async storeMessage(message: MessageRequest): Promise<MessageResponse> {
    if (!this.paprApiKey) {
      throw new Error('PAPR API key is required for message storage');
    }

    if (this.debug) {
      console.log('💬 [PaprMemoryService] Storing message:', {
        role: message.role,
        sessionId: message.sessionId,
        process: message.process_messages ?? true,
      });
    }

    try {
      const response = await fetch(`${this.paprCloudUrl}/v1/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': this.paprApiKey,
        },
        body: JSON.stringify({
          ...message,
          process_messages: message.process_messages ?? true,
        }),
      });

      if (!response.ok) {
        const error = await response.json() as { detail?: string };
        throw new Error(
          `Failed to store message (${response.status}): ${error.detail || 'Unknown error'}`
        );
      }

      const data = await response.json() as MessageResponse;

      if (this.debug) {
        console.log(
          `✅ [PaprMemoryService] Message stored: ${data.message_id} (queued: ${data.queued_for_processing})`
        );
      }

      return data;
    } catch (error) {
      if (this.debug) {
        console.error('❌ [PaprMemoryService] Failed to store message:', error);
      }
      throw error;
    }
  }

  /**
   * Get search history for constellation visualization
   *
   * @returns Last 30 searches with latency details
   */
  async getSearchHistory(): Promise<SearchHistoryResponse> {
    try {
      const response = await fetch(`${this.pythonServiceUrl}/api/search-history`);

      if (!response.ok) {
        throw new Error(`Failed to fetch search history: ${response.status}`);
      }

      return await response.json() as SearchHistoryResponse;
    } catch (error) {
      if (this.debug) {
        console.error('❌ [PaprMemoryService] Failed to fetch search history:', error);
      }
      throw error;
    }
  }

  /**
   * Get API keys for frontend
   *
   * @returns OpenAI and PAPR API keys
   */
  async getApiKeys(): Promise<ApiKeysResponse> {
    try {
      const response = await fetch(`${this.pythonServiceUrl}/api/keys`);

      if (!response.ok) {
        throw new Error(`Failed to fetch API keys: ${response.status}`);
      }

      return await response.json() as ApiKeysResponse;
    } catch (error) {
      if (this.debug) {
        console.error('❌ [PaprMemoryService] Failed to fetch API keys:', error);
      }
      throw error;
    }
  }

  /**
   * Get OpenAI-compatible tool schema
   *
   * @returns Tool schema for OpenAI Realtime API
   */
  async getToolSchema(): Promise<ToolSchema> {
    try {
      const response = await fetch(`${this.pythonServiceUrl}/api/tool-schema`);

      if (!response.ok) {
        throw new Error(`Failed to fetch tool schema: ${response.status}`);
      }

      return await response.json() as ToolSchema;
    } catch (error) {
      if (this.debug) {
        console.error('❌ [PaprMemoryService] Failed to fetch tool schema:', error);
      }
      throw error;
    }
  }

  /**
   * Health check - verify Python microservice is running
   *
   * @returns true if service is healthy, false otherwise
   */
  async healthCheck(): Promise<boolean> {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 2000); // Quick timeout

      const response = await fetch(`${this.pythonServiceUrl}/api/keys`, {
        signal: controller.signal,
      });

      clearTimeout(timeoutId);
      return response.ok;
    } catch {
      return false;
    }
  }

  /**
   * Get service configuration
   */
  getConfig() {
    return {
      pythonServiceUrl: this.pythonServiceUrl,
      paprCloudUrl: this.paprCloudUrl,
      timeout: this.timeout,
      debug: this.debug,
    };
  }
}
