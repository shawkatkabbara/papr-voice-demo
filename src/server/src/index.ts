/**
 * PAPR Voice Demo - Fastify Backend Server
 *
 * This server provides:
 * 1. Static file serving for voice.html
 * 2. API endpoints that proxy to Python CoreML microservice
 * 3. CORS support for local development
 * 4. WebSocket support (future: for Pipecat integration)
 */

import Fastify from 'fastify';
import fastifyCors from '@fastify/cors';
import fastifyStatic from '@fastify/static';
import fastifyWebsocket from '@fastify/websocket';
import { config } from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';
import { PaprMemoryService } from './services/PaprMemoryService.js';

// Load environment variables
config();

// ES module dirname equivalent
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Initialize Fastify with logging
const server = Fastify({
  logger: {
    level: process.env.LOG_LEVEL || 'info',
    transport: {
      target: 'pino-pretty',
      options: {
        translateTime: 'HH:MM:ss Z',
        ignore: 'pid,hostname',
      },
    },
  },
});

// Initialize PAPR Memory Service
const paprService = new PaprMemoryService({
  pythonServiceUrl: process.env.PYTHON_SERVICE_URL || 'http://localhost:3001',
  paprCloudUrl: process.env.PAPR_CLOUD_URL || 'https://memory.papr.ai',
  paprApiKey: process.env.PAPR_MEMORY_API_KEY,
  timeout: parseInt(process.env.SERVICE_TIMEOUT || '5000'),
  debug: process.env.DEBUG === 'true',
});

// Register CORS plugin
await server.register(fastifyCors, {
  origin: true, // Allow all origins in development
  credentials: true,
});

// Register WebSocket plugin (for future Pipecat integration)
await server.register(fastifyWebsocket);

// Register static file serving
await server.register(fastifyStatic, {
  root: path.join(__dirname, '../../../'), // Serve from project root
  prefix: '/',
});

/**
 * Health check endpoint
 */
server.get('/health', async (request, reply) => {
  const pythonHealthy = await paprService.healthCheck();

  return {
    status: pythonHealthy ? 'healthy' : 'degraded',
    timestamp: new Date().toISOString(),
    services: {
      python_microservice: pythonHealthy ? 'up' : 'down',
      typescript_server: 'up',
    },
  };
});

/**
 * Get API keys from Python microservice
 */
server.get('/api/keys', async (request, reply) => {
  try {
    const keys = await paprService.getApiKeys();
    return keys;
  } catch (error) {
    server.log.error(error, 'Failed to fetch API keys');
    reply.code(500).send({
      error: 'Failed to fetch API keys',
      message: error instanceof Error ? error.message : 'Unknown error',
    });
  }
});

/**
 * Get OpenAI-compatible tool schema from Python microservice
 */
server.get('/api/tool-schema', async (request, reply) => {
  try {
    const schema = await paprService.getToolSchema();
    return schema;
  } catch (error) {
    server.log.error(error, 'Failed to fetch tool schema');
    reply.code(500).send({
      error: 'Failed to fetch tool schema',
      message: error instanceof Error ? error.message : 'Unknown error',
    });
  }
});

/**
 * Search memories using Python CoreML microservice
 * POST /api/search
 */
server.post<{
  Body: {
    query: string;
    max_memories?: number;
    enable_agentic_graph?: boolean;
    rank_results?: boolean;
  };
}>('/api/search', async (request, reply) => {
  try {
    const { query, max_memories, enable_agentic_graph, rank_results } = request.body;

    if (!query || typeof query !== 'string') {
      reply.code(400).send({
        error: 'Invalid request',
        message: 'query parameter is required and must be a string',
      });
      return;
    }

    const result = await paprService.search({
      query,
      max_memories,
      enable_agentic_graph,
      rank_results,
    });

    return result;
  } catch (error) {
    server.log.error(error, 'Search failed');
    reply.code(500).send({
      error: 'Search failed',
      message: error instanceof Error ? error.message : 'Unknown error',
    });
  }
});

/**
 * Get search history for constellation visualization
 */
server.get('/api/search-history', async (request, reply) => {
  try {
    const history = await paprService.getSearchHistory();
    return history;
  } catch (error) {
    server.log.error(error, 'Failed to fetch search history');
    reply.code(500).send({
      error: 'Failed to fetch search history',
      message: error instanceof Error ? error.message : 'Unknown error',
    });
  }
});

/**
 * Store conversation message with PAPR Cloud
 * POST /api/messages
 */
server.post<{
  Body: {
    content: string | Array<{ type: string; text?: string; [key: string]: any }>;
    role: 'user' | 'assistant';
    sessionId: string;
    process_messages?: boolean;
    metadata?: Record<string, any>;
  };
}>('/api/messages', async (request, reply) => {
  try {
    const { content, role, sessionId, process_messages, metadata } = request.body;

    if (!content || !role || !sessionId) {
      reply.code(400).send({
        error: 'Invalid request',
        message: 'content, role, and sessionId are required',
      });
      return;
    }

    const result = await paprService.storeMessage({
      content,
      role,
      sessionId,
      process_messages,
      metadata,
    });

    return result;
  } catch (error) {
    server.log.error(error, 'Failed to store message');
    reply.code(500).send({
      error: 'Failed to store message',
      message: error instanceof Error ? error.message : 'Unknown error',
    });
  }
});

/**
 * Serve voice.html at root
 */
server.get('/', async (request, reply) => {
  return reply.sendFile('voice.html');
});

/**
 * Serve logo.svg
 */
server.get('/logo.svg', async (request, reply) => {
  return reply.sendFile('voice.html.logo.svg');
});

/**
 * Start the server
 */
const start = async () => {
  try {
    const port = parseInt(process.env.PORT || '3000');
    const host = process.env.HOST || '0.0.0.0';

    await server.listen({ port, host });

    server.log.info(`
╔═══════════════════════════════════════════════════════╗
║  🎤 PAPR Voice Demo - TypeScript Backend Server      ║
║                                                       ║
║  Server:     http://localhost:${port}                  ║
║  Health:     http://localhost:${port}/health          ║
║  API:        http://localhost:${port}/api/*           ║
║                                                       ║
║  Python:     ${process.env.PYTHON_SERVICE_URL || 'http://localhost:3001'}              ║
║  PAPR Cloud: ${process.env.PAPR_CLOUD_URL || 'https://memory.papr.ai'}   ║
╚═══════════════════════════════════════════════════════╝
    `);

    // Check Python microservice health
    const pythonHealthy = await paprService.healthCheck();
    if (!pythonHealthy) {
      server.log.warn('⚠️  Python CoreML microservice is not responding!');
      server.log.warn('   Make sure to start it with: poetry run python src/python/voice_server.py');
    } else {
      server.log.info('✅ Python CoreML microservice is healthy');
    }
  } catch (err) {
    server.log.error(err);
    process.exit(1);
  }
};

// Handle graceful shutdown
const shutdown = async () => {
  server.log.info('Shutting down gracefully...');
  await server.close();
  process.exit(0);
};

process.on('SIGTERM', shutdown);
process.on('SIGINT', shutdown);

// Start the server
start();
