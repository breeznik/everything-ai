import { PromptTemplate } from "@langchain/core/prompts";
import * as readline from "node:readline/promises";
import { StringOutputParser } from "@langchain/core/output_parsers";
import { retriever } from "../utils/retriever.js";
import { combineDocuments, formateConvHistory } from "../utils/utils.js";
import { llm } from "../config/llm.js";
import {
  RunnablePassthrough,
  RunnableSequence,
} from "@langchain/core/runnables";

const terminal = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
});

const standTemplate = `Given some conversation history if any and a question , convert it to a standalone question. converstation_history:{conv_history} question: {question} standalone question:`;

const contextTemplate = `you are story teller of the world of fantasy, Answer based on Given a contxt , Question and converstaion history. 
  context: {context}
  conversation history: {conv_history},
  question: {question},
  
  answer: 
  `;

const contextPrompt = PromptTemplate.fromTemplate(contextTemplate);
const standPrompt = PromptTemplate.fromTemplate(standTemplate);
const stringPass = new StringOutputParser();
const memory = [];

// passing question
// making it standalone
// reteriving info [question being lost here]
// making a contextual answer
// replying

const contextChian = RunnableSequence.from([
  standPrompt,
  llm,
  stringPass,
  retriever,
  combineDocuments,
  stringPass,
]);

const FinalResponse = RunnableSequence.from([contextPrompt, llm, stringPass]);

const mainChain = RunnableSequence.from([
  {
    context: contextChian,
    original_input: new RunnablePassthrough(),
  },
  {
    question: ({ original_input }) => original_input.question,
    context: (original_input) => original_input.context,
    conv_history: ({ original_input }) => original_input.conv_history,
  },
  FinalResponse,
]);

while (true) {
  const userInput = await terminal.question("You: ");
  memory.push(userInput);

  const response = await mainChain.invoke({
    question: userInput,
    conv_history: formateConvHistory(memory),
  });

  // const userMemObj = { role: "user", content: userInput };
  // const assistantMemObj = { role: "assistant", content: response };

  const humanMessage = `Human: ${userInput}`;
  const AIMessage = `AI: ${response}`;

  memory.push(humanMessage);
  memory.push(AIMessage);

  console.log(response);
}
