import { SupabaseVectorStore } from "@langchain/community/vectorstores/supabase";
import { OpenAIEmbeddings } from "@langchain/openai";
import { createClient } from "@supabase/supabase-js";
import dotenv from "dotenv";

dotenv.config();
const sbApiKey = process.env.SUPABASE_API_KEY;
const sbUrl = process.env.SUPABASE_URL;

// turn input in vector representation
const embeddings = new OpenAIEmbeddings();

//client to supabase
const client = createClient(sbUrl, sbApiKey);

//vectorstore config - supabase client , openai embeddings , query function
const vectorStore = new SupabaseVectorStore(embeddings, {
  client,
  tableName: "documents",
  queryName: "match_documents",
});

const retriever = vectorStore.asRetriever();
export { retriever };
