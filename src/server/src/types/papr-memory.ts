/**
 * PAPR Memory TypeScript Types
 *
 * These types are derived from the official PAPR SDK Pydantic schemas
 * located at papr-pythonSDK/src/papr_memory/types/
 *
 * They ensure type safety when communicating with the Python CoreML microservice
 * and maintain consistency with the PAPR SDK API.
 */

/**
 * Memory search parameters
 * Derived from: papr_memory.types.memory_search_params.MemorySearchParams
 */
export interface MemorySearchParams {
  /**
   * Detailed search query describing what you're looking for.
   * For best results, write 2-3 sentences with specific details, context, and timeframe.
   */
  query: string;

  /**
   * Maximum number of memories to return.
   * Recommended: 15-20 for comprehensive results. Default: 20.
   */
  max_memories?: number;

  /**
   * Maximum number of graph nodes to return.
   * Recommended: 10-15 for comprehensive graph results. Default: 15.
   */
  max_nodes?: number;

  /**
   * Enable agentic graph search for intelligent, context-aware results.
   * When enabled, the system understands ambiguous references by identifying
   * entities first, then performing targeted searches.
   * Default: false (faster keyword-based search)
   */
  enable_agentic_graph?: boolean;

  /**
   * External user ID for filtering results.
   */
  external_user_id?: string;

  /**
   * Namespace ID for multi-tenant search scoping.
   */
  namespace_id?: string;

  /**
   * Organization ID for multi-tenant search scoping.
   */
  organization_id?: string;

  /**
   * Enable additional ranking of search results.
   * Default: true for CoreML on-device (optimizes results)
   */
  rank_results?: boolean;

  /**
   * User-defined schema ID for this search.
   */
  schema_id?: string;

  /**
   * Use simple schema mode (system schema + ONE most relevant user schema).
   * Recommended for production consistency. Default: false.
   */
  simple_schema_mode?: boolean;

  /**
   * Internal user ID for filtering results.
   */
  user_id?: string;
}

/**
 * Memory object returned from search
 * Derived from PAPR SDK Memory response structure
 */
export interface Memory {
  /** Unique memory ID */
  id: string;

  /** Memory content text */
  content: string | null;

  /**
   * ChromaDB query similarity score (cosine similarity to search query)
   * Range: 0.0 to 1.0, higher is more relevant
   */
  query_similarity: number;

  /**
   * Server-side relevance score (composite: goals/transitions/hotness)
   * Range: 0.0 to 1.0, higher is more relevant
   */
  relevance_score: number;

  /**
   * Backward compatibility score field
   * @deprecated Use query_similarity or relevance_score instead
   */
  score: number;

  /**
   * Backward compatibility similarity score field
   * @deprecated Use query_similarity instead
   */
  similarity_score: number;

  /** Associated tags */
  tags: string[];

  /** Associated topics */
  topics: string[];

  /** Custom metadata object */
  custom_metadata?: Record<string, any> | null;

  /** System metadata */
  metadata?: Record<string, any>;
}

/**
 * Search response from Python microservice
 */
export interface SearchResponse {
  data: {
    memories: Memory[];
  };
  /** Total latency in milliseconds */
  latency_ms: number;
  /** Detailed latency breakdown */
  latency_breakdown: LatencyBreakdown;
  /** Unique search ID for constellation tracking */
  search_id: string;
}

/**
 * Latency breakdown for performance tracking
 */
export interface LatencyBreakdown {
  /** Total end-to-end latency (ms) */
  total_ms: number;
  /** SDK processing time (ms) */
  sdk_processing_ms: number;
  /** Estimated embedding generation time (ms) */
  embedding_generation_ms: number;
  /** Estimated ChromaDB search time (ms) */
  chromadb_search_ms: number;
  /** Python/Flask processing overhead (ms) */
  processing_overhead_ms: number;
  /** Explanation note */
  note: string;
}

/**
 * Search history entry for constellation visualization
 */
export interface SearchHistoryEntry {
  /** Unique search ID */
  id: string;
  /** ISO timestamp */
  timestamp: string;
  /** Search query text */
  query: string;
  /** Number of results returned */
  result_count: number;
  /** Whether agentic graph was used */
  enable_agentic_graph: boolean;
  /** Latency breakdown */
  latency: LatencyBreakdown;
  /** Highest similarity score in results */
  top_score: number;
  /** Preview of top 3 memories */
  top_memories_preview: Array<{
    content: string;
    score: number;
  }>;
}

/**
 * Search history response
 */
export interface SearchHistoryResponse {
  searches: SearchHistoryEntry[];
  count: number;
}

/**
 * Memory metadata parameters
 * Derived from: papr_memory.types.memory_metadata_param.MemoryMetadataParam
 */
export interface MemoryMetadataParam {
  /** Custom metadata fields */
  [key: string]: any;
}

/**
 * Memory add parameters
 * Derived from: papr_memory.types.memory_add_params.MemoryAddParams
 */
export interface MemoryAddParams {
  /** Memory content (required) */
  content: string;
  /** Optional metadata */
  metadata?: MemoryMetadataParam;
  /** Optional tags */
  tags?: string[];
  /** Optional topics */
  topics?: string[];
  /** External user ID */
  external_user_id?: string;
  /** Namespace ID */
  namespace_id?: string;
  /** Organization ID */
  organization_id?: string;
  /** User ID */
  user_id?: string;
}

/**
 * API keys response
 */
export interface ApiKeysResponse {
  openai_key: string;
  papr_key: string;
}

/**
 * Tool schema for OpenAI Realtime API
 */
export interface ToolSchema {
  type: 'function';
  name: string;
  description: string;
  parameters: {
    type: 'object';
    properties: Record<string, any>;
    required: string[];
  };
}

/**
 * Message roles for conversation storage
 * Derived from: models.shared_types.MessageRole
 */
export type MessageRole = 'user' | 'assistant';

/**
 * Message content can be string or structured objects
 */
export type MessageContent = string | Array<{
  type: string;
  text?: string;
  [key: string]: any;
}>;

/**
 * Message request for storing chat messages
 * Derived from: models.message_models.MessageRequest
 *
 * Automatically stores conversation with background AI analysis
 * and memory creation (when process_messages=true)
 */
export interface MessageRequest {
  /** The content of the chat message */
  content: MessageContent;

  /** Role of the message sender */
  role: MessageRole;

  /** Session ID to group related messages in a conversation */
  sessionId: string;

  /** Optional metadata for the message */
  metadata?: MemoryMetadataParam;

  /**
   * Whether to process messages into memories (true) or just store them (false).
   * Default: true
   *
   * When true:
   * - Message is analyzed for memory-worthiness
   * - Memories are created with role-based categorization
   * - User messages: preference, task, goal, facts, context
   * - Assistant messages: skills, learning
   */
  process_messages?: boolean;

  /** Optional organization ID for multi-tenant scoping */
  organization_id?: string;

  /** Optional namespace ID for multi-tenant scoping */
  namespace_id?: string;
}

/**
 * Message response after storage
 */
export interface MessageResponse {
  /** Success status */
  success: boolean;
  /** Stored message ID */
  message_id: string;
  /** Message content */
  message: string;
  /** Processing status */
  queued_for_processing: boolean;
}
