import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NutriBot — AI Nutrition & Diet Chatbot",
  description:
    "Ask NutriBot about nutrition, diet plans, vitamins, macros, and healthy eating. " +
    "Powered by a RAG pipeline with HuggingFace embeddings, Supabase pgvector, and Groq Llama 3.",
  keywords: [
    "nutrition chatbot",
    "diet AI",
    "RAG chatbot",
    "healthy eating",
    "nutrition advice",
    "NutriBot",
  ],
  openGraph: {
    title: "NutriBot — AI Nutrition & Diet Chatbot",
    description: "Your free AI-powered nutritionist, backed by a curated knowledge base.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
