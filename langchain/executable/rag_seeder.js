import fs from "fs";
import dotenv from "dotenv";
import { RecursiveCharacterTextSplitter } from "langchain/text_splitter";
import { createClient } from "@supabase/supabase-js";
import { SupabaseVectorStore } from "@langchain/community/vectorstores/supabase";
import { OpenAIEmbeddings } from "@langchain/openai";

dotenv.config();

(async () => {
  try {
    // Validate environment variables
    const supabaseApiKey = process.env.SUPABASE_API_KEY;
    const supabaseUrl = process.env.SUPABASE_URL;
    const openAIApiKey = process.env.OPEN_AI_API_KEY;

    if (!supabaseApiKey || !supabaseUrl || !openAIApiKey) {
      throw new Error("Missing required environment variables.");
    }

    // Read the input file
    const data = fs.readFileSync("./data.txt", "utf-8");
    if (!data || data.trim() === "") {
      throw new Error("Input file is empty or unreadable.");
    }

    // Split into documents
    const splitter = new RecursiveCharacterTextSplitter({
      chunkSize: 500,
      chunkOverlap: 50,
      separators: ["\n\n", "\n", " ", "", "##"],
    });

    const documents = await splitter.createDocuments([data]);

    console.log(`✅ Split into ${documents.length} chunks.`);

    // Initialize Supabase and LangChain embedding logic
    const client = createClient(supabaseUrl, supabaseApiKey);

    await SupabaseVectorStore.fromDocuments(
      documents,
      new OpenAIEmbeddings({ openAIApiKey }),
      {
        client,
        tableName: "documents",
      }
    );

    console.log("🎉 Embeddings successfully stored in Supabase.");
  } catch (error) {
    console.error("❌ Error:", error.message || error);
  }
})();
