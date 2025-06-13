import { ChatOpenAI } from "@langchain/openai";
import dotenv from "dotenv";
dotenv.config();

const openAIApiKey = process.env.OPENAI_API_KEY;

//open AI LLM
export const llm = new ChatOpenAI({ openAIApiKey });
