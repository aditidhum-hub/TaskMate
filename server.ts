import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';
import { createServer as createViteServer } from 'vite';
import { GoogleGenAI, Type, FunctionDeclaration } from '@google/genai';
import { evaluateSafeMath, resolveDateTime, sanitizeCustomerError } from './src/utils/safeEvaluator.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function startServer() {
  const app = express();
  const PORT = 3000;

  app.use(express.json());

  // In-memory telemetry log for server-side tool invocations
  const serverToolTraces: Array<{
    id: string;
    toolName: string;
    arguments: Record<string, unknown>;
    result: unknown;
    status: 'success' | 'error';
    latencyMs: number;
    timestamp: string;
  }> = [];

  // Health check endpoint
  app.get('/api/health', (req, res) => {
    res.json({
      status: 'ok',
      service: 'Agentic Platform Microservice',
      uptime: process.uptime(),
      timestamp: new Date().toISOString(),
    });
  });

  // Safe AST Math Tool API endpoint (FR-07)
  app.post('/api/tools/calculate', (req, res) => {
    const { expression } = req.body;
    if (!expression || typeof expression !== 'string') {
      return res.status(400).json({ error: 'Expression string is required' });
    }
    const t0 = performance.now();
    try {
      const result = evaluateSafeMath(expression);
      const latencyMs = Math.round(performance.now() - t0);
      serverToolTraces.unshift({
        id: `srv-trace-${Date.now()}`,
        toolName: 'calculate',
        arguments: { expression },
        result,
        status: 'success',
        latencyMs: Math.max(1, latencyMs),
        timestamp: new Date().toISOString(),
      });
      res.json({ success: true, ...result, latencyMs });
    } catch (err) {
      const sanitized = sanitizeCustomerError(err);
      res.status(400).json({
        success: false,
        error: sanitized.customerMessage,
      });
    }
  });

  // Relative / Absolute Date Resolver Tool API endpoint (FR-08)
  app.post('/api/tools/date-time', (req, res) => {
    const { query } = req.body;
    const t0 = performance.now();
    try {
      const result = resolveDateTime(query);
      const latencyMs = Math.round(performance.now() - t0);
      serverToolTraces.unshift({
        id: `srv-trace-${Date.now()}`,
        toolName: 'get_date_time',
        arguments: { query },
        result,
        status: 'success',
        latencyMs: Math.max(1, latencyMs),
        timestamp: new Date().toISOString(),
      });
      res.json({ success: true, ...result, latencyMs });
    } catch (err) {
      const sanitized = sanitizeCustomerError(err);
      res.status(400).json({ success: false, error: sanitized.customerMessage });
    }
  });

  // Autonomous Agent Chat & Tool Calling Orchestrator
  app.post('/api/agent/chat', async (req, res) => {
    const { prompt, tenantId, userRole, tenantTasks } = req.body;

    if (!prompt) {
      return res.status(400).json({ error: 'Prompt is required' });
    }

    const traces: Array<any> = [];
    const thoughtSteps: Array<{ step: number; type: string; content: string }> = [];

    thoughtSteps.push({
      step: 1,
      type: 'reasoning',
      content: `Received prompt: "${prompt.slice(0, 60)}" for tenant ${tenantId || 'default'}. Analyzing intent & tool declarations.`,
    });

    // Check if GEMINI_API_KEY is available for LLM reasoning
    const apiKey = process.env.GEMINI_API_KEY;

    if (apiKey) {
      try {
        const ai = new GoogleGenAI({
          apiKey,
          httpOptions: {
            headers: {
              'User-Agent': 'aistudio-build',
            },
          },
        });

        // Function declarations for Gemini tool calling
        const calculateTool: FunctionDeclaration = {
          name: 'calculate',
          description: 'Evaluates safe mathematical arithmetic expressions without eval (FR-07). Supports +, -, *, /, %, ^, sqrt, round.',
          parameters: {
            type: Type.OBJECT,
            properties: {
              expression: {
                type: Type.STRING,
                description: 'The math expression to evaluate, e.g. "450 * 3 + 1200 * 2"',
              },
            },
            required: ['expression'],
          },
        };

        const dateTimeTool: FunctionDeclaration = {
          name: 'get_date_time',
          description: 'Resolves relative and absolute dates into ISO strings (e.g. "tomorrow", "next Tuesday", "in 5 days").',
          parameters: {
            type: Type.OBJECT,
            properties: {
              query: {
                type: Type.STRING,
                description: 'The relative or absolute date expression, e.g. "next Tuesday"',
              },
            },
            required: ['query'],
          },
        };

        thoughtSteps.push({
          step: 2,
          type: 'reasoning',
          content: 'Invoking Gemini 3.8 Flash model with tools [calculate, get_date_time].',
        });

        const response = await ai.models.generateContent({
          model: 'gemini-3.8-flash',
          contents: prompt,
          config: {
            systemInstruction: `You are an Autonomous Task & Planning Agent for a multi-tenant platform.
You assist customers by managing tasks, evaluating mathematical budgets with the 'calculate' tool, and resolving relative dates with 'get_date_time'.
Always use the tools for any arithmetic or date calculations.
Current tenant: ${tenantId || 'tenant-enterprise-01'}.
Current active tasks: ${JSON.stringify(tenantTasks || [])}.`,
            tools: [{ functionDeclarations: [calculateTool, dateTimeTool] }],
          },
        });

        const functionCalls = response.functionCalls;
        let toolOutputSummary = '';

        if (functionCalls && functionCalls.length > 0) {
          for (const call of functionCalls) {
            const t0 = performance.now();
            thoughtSteps.push({
              step: thoughtSteps.length + 1,
              type: 'tool_call',
              content: `Calling tool '${call.name}' with args: ${JSON.stringify(call.args)}`,
            });

            if (call.name === 'calculate') {
              const expr = String(call.args?.expression || '');
              try {
                const evalRes = evaluateSafeMath(expr);
                const lat = Math.round(performance.now() - t0);
                traces.push({
                  id: `trace-${Date.now()}`,
                  toolName: 'calculate',
                  arguments: call.args,
                  result: evalRes,
                  status: 'success',
                  latencyMs: Math.max(1, lat),
                  timestamp: new Date().toISOString(),
                });
                toolOutputSummary += `\n- Calculation evaluated: ${evalRes.expression} = ${evalRes.result}`;
              } catch (err) {
                const sanitized = sanitizeCustomerError(err);
                traces.push({
                  id: `trace-${Date.now()}`,
                  toolName: 'calculate',
                  arguments: call.args,
                  result: { error: sanitized.customerMessage },
                  status: 'error',
                  latencyMs: 5,
                  timestamp: new Date().toISOString(),
                  sanitizedForCustomer: true,
                });
                toolOutputSummary += `\n- Calculation error: ${sanitized.customerMessage}`;
              }
            } else if (call.name === 'get_date_time') {
              const q = String(call.args?.query || '');
              const dateRes = resolveDateTime(q);
              const lat = Math.round(performance.now() - t0);
              traces.push({
                id: `trace-${Date.now()}`,
                toolName: 'get_date_time',
                arguments: call.args,
                result: dateRes,
                status: 'success',
                latencyMs: Math.max(1, lat),
                timestamp: new Date().toISOString(),
              });
              toolOutputSummary += `\n- Date resolved: ${dateRes.relativeDescription} -> ${dateRes.formatted}`;
            }
          }
        }

        const generatedText = response.text || '';
        const finalContent = generatedText
          ? `${generatedText}${toolOutputSummary ? `\n\n**Tool Output Summary:**${toolOutputSummary}` : ''}`
          : `I processed your request using the Autonomous Agent with registered tools.${toolOutputSummary}`;

        thoughtSteps.push({
          step: thoughtSteps.length + 1,
          type: 'synthesis',
          content: 'Synthesized final response from Gemini reasoning and tool traces.',
        });

        return res.json({
          content: finalContent,
          thoughtSteps,
          toolCalls: traces,
          modelUsed: 'gemini-3.8-flash',
        });
      } catch (geminiError) {
        console.warn('Gemini API call failed or rate-limited; falling back to local orchestrator:', geminiError);
      }
    }

    // Deterministic fallback (runs if GEMINI_API_KEY not set or request failed)
    const lower = prompt.toLowerCase();
    let textOut = '';

    // Math check
    if (lower.includes('calculate') || /[0-9]+\s*[\+\-\*\/]\s*[0-9]+/.test(lower)) {
      const match = lower.match(/([0-9+\-*/%^().,\s]+)/);
      if (match && /[+\-*/%^]/.test(match[1])) {
        const expr = match[1].trim();
        thoughtSteps.push({
          step: 2,
          type: 'tool_call',
          content: `Invoking AST Calculator for expression: "${expr}"`,
        });
        try {
          const evalRes = evaluateSafeMath(expr);
          traces.push({
            id: `trace-${Date.now()}`,
            toolName: 'calculate',
            arguments: { expression: expr },
            result: evalRes,
            status: 'success',
            latencyMs: 3,
            timestamp: new Date().toISOString(),
          });
          textOut += `Mathematical calculation result:\n$$\`${evalRes.expression}\` = **${evalRes.result}**$$\n\n`;
        } catch (err) {
          const sanitized = sanitizeCustomerError(err);
          textOut += `⚠️ ${sanitized.customerMessage}\n\n`;
        }
      }
    }

    // Date check
    if (lower.includes('date') || lower.includes('tomorrow') || lower.includes('next ') || lower.includes('today')) {
      const dt = resolveDateTime(prompt);
      thoughtSteps.push({
        step: 3,
        type: 'tool_call',
        content: `Resolved date: "${prompt}" -> ${dt.formatted}`,
      });
      traces.push({
        id: `trace-${Date.now()}-dt`,
        toolName: 'get_date_time',
        arguments: { query: prompt },
        result: dt,
        status: 'success',
        latencyMs: 2,
        timestamp: new Date().toISOString(),
      });
      textOut += `Date verification:\n- **${dt.relativeDescription}**: **${dt.formatted}** (\`${dt.iso}\`)\n\n`;
    }

    if (!textOut) {
      textOut = `I have received your request in tenant \`${tenantId || 'tenant-enterprise-01'}\`. You can ask me to evaluate math calculations, resolve relative dates, or organize tasks!`;
    }

    thoughtSteps.push({
      step: thoughtSteps.length + 1,
      type: 'synthesis',
      content: 'Final synthesized response emitted to client.',
    });

    res.json({
      content: textOut.trim(),
      thoughtSteps,
      toolCalls: traces,
      modelUsed: 'autonomous-agent-local',
    });
  });

  // Vite middleware for development
  if (process.env.NODE_ENV !== 'production') {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), 'dist');
    app.use(express.static(distPath));
    app.get('*', (req, res) => {
      res.sendFile(path.join(distPath, 'index.html'));
    });
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`Autonomous Agent Platform running on http://0.0.0.0:${PORT}`);
  });
}

startServer();
