/**
 * app/api/chat/route.ts — NutriBot RAG pipeline (Vercel serverless)
 *
 *  1. Embed query  → @huggingface/inference (all-MiniLM-L6-v2, FREE)
 *  2. Retrieve     → Supabase pgvector (match_chunks RPC)
 *  3. Generate     → Groq via OpenAI-compatible SDK (llama-3.1-8b-instant, FREE)
 */

import { NextRequest, NextResponse } from "next/server";
import OpenAI from "openai";
import { createClient } from "@supabase/supabase-js";
import { HfInference } from "@huggingface/inference";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

// ── Clients (one per cold start) ──────────────────────────────────────────────
const hf = new HfInference(process.env.HF_TOKEN ?? "");

const groq = new OpenAI({
  apiKey: process.env.GROQ_API_KEY ?? "",
  baseURL: "https://api.groq.com/openai/v1",
});

const supabase = createClient(
  process.env.SUPABASE_URL ?? "",
  process.env.SUPABASE_SERVICE_ROLE_KEY ?? "",
  { auth: { persistSession: false, autoRefreshToken: false } }
);

const GROQ_MODEL = process.env.GROQ_MODEL ?? "llama-3.1-8b-instant";
const TOP_K      = parseInt(process.env.TOP_K ?? "5", 10);
const EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2";

// ── Step 1: Embed via official HF package (no raw URL needed) ─────────────────
async function embedQuery(query: string): Promise<number[]> {
  const result = await hf.featureExtraction({
    model: EMBED_MODEL,
    inputs: query,
  });

  // result is Float64Array | Float64Array[] | number[] | number[][]
  // For a single string input, sentence-transformers returns number[]
  if (Array.isArray(result)) {
    // Flat array of numbers → direct embedding
    if (typeof result[0] === "number") return result as number[];
    // Nested array (batch of 1) → unwrap
    if (Array.isArray(result[0])) {
      const inner = result[0];
      if (typeof inner[0] === "number") return inner as number[];
    }
  }

  // Handle TypedArray (Float64Array)
  if (result instanceof Float64Array || result instanceof Float32Array) {
    return Array.from(result);
  }

  throw new Error(`Unexpected embedding shape: ${typeof result}`);
}

// ── Step 2: Retrieve from Supabase pgvector ───────────────────────────────────
interface SupabaseChunk {
  content: string;
  metadata: { page?: number; source?: string } | null;
  similarity: number;
}

async function retrieveChunks(embedding: number[]): Promise<SupabaseChunk[]> {
  const { data, error } = await supabase.rpc("match_chunks", {
    query_embedding: embedding,
    match_count: TOP_K,
  });
  if (error) throw new Error(`Supabase RPC error: ${error.message}`);
  return (data ?? []) as SupabaseChunk[];
}

// ── System prompt ─────────────────────────────────────────────────────────────
const SYSTEM_PROMPT = `You are NutriBot, an expert AI nutritionist powered by the Human Nutrition textbook.

Your expertise covers:
- Macronutrients (proteins, carbohydrates, fats) and their metabolic roles
- Micronutrients (vitamins, minerals) and deficiency symptoms
- Meal planning, dietary patterns (Mediterranean, keto, vegan, plant-based)
- Weight management, metabolism, and body composition
- Sports nutrition and physical performance
- Digestive health and gut microbiome

Guidelines:
1. Base your answers PRIMARILY on the provided CONTEXT from the knowledge base
2. Cite source numbers like [1], [2] and mention page numbers when available
3. If context doesn't fully answer the question, say so and give general guidance
4. Recommend consulting a registered dietitian for personalized medical advice
5. Be friendly, clear, and structured — use bullet points for complex topics
6. Keep responses focused and practical (150–300 words)`;

// ── Step 3: Generate via Groq ─────────────────────────────────────────────────
async function generateAnswer(
  query: string,
  chunks: SupabaseChunk[],
  history: { role: string; content: string }[]
): Promise<{ answer: string; tokensUsed: number }> {
  const context = chunks.length
    ? chunks
        .map((c, i) => `[${i + 1}] (Page ${c.metadata?.page ?? "?"}) ${c.content}`)
        .join("\n\n")
    : "No specific context retrieved from the knowledge base.";

  const messages: OpenAI.Chat.ChatCompletionMessageParam[] = [
    { role: "system", content: SYSTEM_PROMPT },
    ...history.slice(-6).map((m) => ({
      role: m.role as "user" | "assistant",
      content: m.content,
    })),
    {
      role: "user",
      content: `CONTEXT FROM KNOWLEDGE BASE:\n${context}\n\nUSER QUESTION: ${query}`,
    },
  ];

  const completion = await groq.chat.completions.create({
    model: GROQ_MODEL,
    messages,
    temperature: 0.4,
    max_tokens: 600,
    top_p: 0.9,
  });

  return {
    answer: completion.choices[0]?.message?.content?.trim() ?? "",
    tokensUsed: completion.usage?.total_tokens ?? 0,
  };
}

// ── POST /api/chat ────────────────────────────────────────────────────────────
export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const message: string = (body?.message ?? "").toString().trim();
    const history: { role: string; content: string }[] = body?.history ?? [];

    if (!message) {
      return NextResponse.json({ error: "Empty query" }, { status: 400 });
    }

    // 1. Embed
    const embedding = await embedQuery(message);

    // 2. Retrieve
    const chunks = await retrieveChunks(embedding);

    if (!chunks.length) {
      return NextResponse.json({
        answer:
          "I couldn't find relevant information for that question. " +
          "Try asking about macronutrients, vitamins, diet plans, or specific foods.",
        sources: [],
        model: GROQ_MODEL,
      });
    }

    // 3. Generate
    const { answer, tokensUsed } = await generateAnswer(message, chunks, history);

    return NextResponse.json({
      answer,
      sources: chunks.map((c) => ({
        content: c.content,
        page: c.metadata?.page,
        source: c.metadata?.source ?? "human-nutrition-text.pdf",
        similarity: c.similarity,
      })),
      model: GROQ_MODEL,
      tokens_used: tokensUsed,
    });
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : "Unknown error";
    console.error("[NutriBot] /api/chat error:", msg);
    return NextResponse.json({ error: msg }, { status: 500 });
  }
}
