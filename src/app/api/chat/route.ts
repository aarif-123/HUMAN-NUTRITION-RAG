// /* =====================================================
//    DEV ONLY: Windows TLS bypass
//    ❗ REMOVE IN PRODUCTION
// ===================================================== */
// process.env.NODE_TLS_REJECT_UNAUTHORIZED = "0";

// import { NextRequest, NextResponse } from "next/server";
// import { createClient } from "@supabase/supabase-js";

// /* =====================================================
//    Supabase client (SERVER ONLY)
// ===================================================== */
// const supabase = createClient(
//   process.env.SUPABASE_URL!,
//   process.env.SUPABASE_SERVICE_ROLE_KEY!
// );

// /* =====================================================
//    Embed query (FastAPI + E5)
// ===================================================== */
// async function embedQuery(query: string): Promise<number[]> {
//   const res = await fetch("http://127.0.0.1:8000/embed", {
//     method: "POST",
//     headers: { "Content-Type": "application/json" },
//     body: JSON.stringify({ text: `query: ${query}` })
//   });

//   if (!res.ok) {
//     const err = await res.text();
//     throw new Error("Embedding error: " + err);
//   }

//   const json = await res.json();
//   return json.embedding;
// }

// /* =====================================================
//    POST /api/chat
// ===================================================== */
// export async function POST(req: NextRequest) {
//   try {
//     /* ---------- 1. Read input ---------- */
//     const { message } = await req.json();

//     if (!message || typeof message !== "string") {
//       return NextResponse.json(
//         { error: "Message is required" },
//         { status: 400 }
//       );
//     }

//     /* ---------- 2. Embed query ---------- */
//     const queryEmbedding = await embedQuery(message);

//     /* ---------- 3. Retrieve chunks ---------- */
//     const { data: chunks, error } = await supabase.rpc(
//       "match_documents",
//       {
//         query_embedding: queryEmbedding,
//         match_count: 8,
//         filter: {}
//       }
//     );

//     if (error) throw error;

//     console.log("Retrieved chunks:", chunks?.length);

//     if (!chunks || chunks.length === 0) {
//       return NextResponse.json({
//         answer:
//           "I couldn’t find this in the provided document. Try rephrasing your question.",
//         sources: []
//       });
//     }

//     /* ---------- 4. Build context ---------- */
//     const context = chunks
//       .map((c: any, i: number) => `[${i + 1}] ${c.content}`)
//       .join("\n\n");

//     /* ---------- 5. Prompt ---------- */
//     const prompt = `
// You are an expert assistant.
// Answer ONLY using the context below.
// If the answer is not present, say:
// "I couldn’t find this in the provided document."

// CONTEXT:
// ${context}

// QUESTION:
// ${message}
// `;
// const llmRes = await fetch("http://127.0.0.1:11434/api/generate", {
//   method: "POST",
//   headers: { "Content-Type": "application/json" },
//   body: JSON.stringify({
//     model: "gemma:2b",
//     prompt,
//     temperature: 0.2,
//     stream: false
//   })
// });

// const llmJson = await llmRes.json();
// const answer = llmJson.response;


//     // /* ---------- 6. Hugging Face Gemma ---------- */
//     // const llmRes = await fetch(
//     //   "https://router.huggingface.co/hf-inference/models/google/gemma-2b-it",
//     //   {
//     //     method: "POST",
//     //     headers: {
//     //       Authorization: `Bearer ${process.env.HF_API_TOKEN}`,
//     //       "Content-Type": "application/json"
//     //     },
//     //     body: JSON.stringify({
//     //       inputs: prompt,
//     //       parameters: {
//     //         temperature: 0.2,
//     //         max_new_tokens: 512,
//     //         return_full_text: false
//     //       }
//     //     })
//     //   }
//     // );

//     const rawText = await llmRes.text();

//     if (!llmRes.ok) {
//       console.error("HF raw response:", rawText);
//       throw new Error("Gemma HF API call failed");
//     }

//     let llmJson: any;
//     try {
//       llmJson = JSON.parse(rawText);
//     } catch {
//       throw new Error("HF returned non-JSON: " + rawText);
//     }

//     const answer =
//       llmJson?.[0]?.generated_text ??
//       llmJson?.generated_text ??
//       "No response from Gemma";

//     /* ---------- 7. Return ---------- */
//     return NextResponse.json({
//       answer,
//       sources: chunks.map((c: any) => ({
//         doc_id: c.doc_id,
//         chunk_index: c.chunk_index,
//         similarity: c.similarity
//       }))
//     });

//   } catch (err: any) {
//     console.error("API error:", err.message);
//     return NextResponse.json(
//       { error: err.message },
//       { status: 500 }
//     );
//   }
// }













import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

/* =====================================================
   Supabase client (SERVER ONLY)
===================================================== */
const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
);

/* =====================================================
   Embed query via FastAPI (E5-base-v2)
===================================================== */
async function embedQuery(query: string): Promise<number[]> {
  const res = await fetch("http://127.0.0.1:8000/embed", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      text: `query: ${query}` // REQUIRED for E5
    })
  });

  if (!res.ok) {
    const errText = await res.text();
    throw new Error("Embedding server error: " + errText);
  }

  const json = await res.json();
  return json.embedding;
}

/* =====================================================
   POST /api/chat
===================================================== */
export async function POST(req: NextRequest) {
  try {
    /* ---------- 1️⃣ Read user input ---------- */
    const { message } = await req.json();

    if (!message || typeof message !== "string") {
      return NextResponse.json(
        { error: "Message is required" },
        { status: 400 }
      );
    }

    /* ---------- 2️⃣ Embed query ---------- */
    const queryEmbedding = await embedQuery(message);

    /* ---------- 3️⃣ Retrieve relevant chunks ---------- */
    const { data: chunks, error } = await supabase.rpc(
      "match_documents",
      {
        query_embedding: queryEmbedding,
        match_count: 8,
        filter: {} // IMPORTANT: no filter
      }
    );

    if (error) throw error;

    console.log("Retrieved chunks:", chunks?.length);

    if (!chunks || chunks.length === 0) {
      return NextResponse.json({
        answer:
          "I couldn’t find this in the provided document. Try rephrasing your question.",
        sources: []
      });
    }

    /* ---------- 4️⃣ Build RAG context ---------- */
    const context = chunks
      .map((c: any, i: number) => `[${i + 1}] ${c.content}`)
      .join("\n\n");

    /* ---------- 5️⃣ RAG prompt ---------- */
    const prompt = `
You are an expert assistant.
Answer ONLY using the context below.
2. FORMATTING INSTRUCTIONS
- **Markdown Tables:** If the question involves comparing items (e.g., "Heme vs Non-heme iron") or listing data, YOU MUST render a Markdown Table.
- **Lists:** Use bullet points for lists of symptoms, food sources, or functions.
- **Bold Text:** Use **bold** for key terms, specific nutrient values (e.g., **50mg**), and section headers.
- **Tone:** Keep the response academic, objective, and structured.
If the answer is not present, say:
"I couldn’t find this in the provided document."

CONTEXT:
${context}

QUESTION:
${message}
`;

    /* =====================================================
       6️⃣ Call Ollama (Gemma 2B)
===================================================== */
    const llmRes = await fetch("http://127.0.0.1:11434/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model: "gemma:2b",
        prompt,
        temperature: 0.2,
        stream: false
      })
    });

    if (!llmRes.ok) {
      const errText = await llmRes.text();
      throw new Error("Ollama error: " + errText);
    }

    const llmJson = await llmRes.json();
    const answer = llmJson.response;

    /* ---------- 7️⃣ Return answer + sources ---------- */
    return NextResponse.json({
      answer,
      sources: chunks.map((c: any) => ({
        doc_id: c.doc_id,
        chunk_index: c.chunk_index,
        similarity: c.similarity,
        content: c.content,
        page_number: c.metadata?.page_number ?? null
      }))
    });

  } catch (err: any) {
    console.error("API error:", err.message);
    return NextResponse.json(
      { error: err.message || "Internal server error" },
      { status: 500 }
    );
  }
}
