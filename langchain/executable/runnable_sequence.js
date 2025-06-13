import { PromptTemplate } from "@langchain/core/prompts";
import {
  RunnableSequence,
  RunnablePassthrough,
} from "@langchain/core/runnables";
import { llm } from "../config/llm.js";
import { StringOutputParser } from "@langchain/core/output_parsers";

const punctuationTemplate = `Given a sentence, add punctuation where needed. sentence: {sentence}
sentence with punctuation: 
`;

const grammerTemplate = `Given a sentence correct the grammer.
sentence: {punctuated_sentence}
sentence with correct grammer:
`;

const translationTemplate = `Given a sentence , translate that sentence into {langauge}.
sentence: {grammatically_corrected_sentence}
translated sentence: `;

const punctuationPrompt = PromptTemplate.fromTemplate(punctuationTemplate);
const grammerPrompt = PromptTemplate.fromTemplate(grammerTemplate);
const translationPrompt = PromptTemplate.fromTemplate(translationTemplate);

const stringPass = new StringOutputParser();

const punctuation_chain = RunnableSequence.from([
  punctuationPrompt,
  llm,
  stringPass,
]);
const grammer_chain = RunnableSequence.from([grammerPrompt, llm, stringPass]);
const translation_chain = RunnableSequence.from([
  translationPrompt,
  llm,
  stringPass,
]);

// Initial RunnableSequence
const chain = RunnableSequence.from([
  {
    punctuated_sentence: punctuation_chain,
    original_input: new RunnablePassthrough(),
  },
  {
    grammatically_corrected_sentence: grammer_chain,
    langauge: ({ original_input }) => original_input.langauge,
  },
  translation_chain,
]);

const response = await chain.invoke({
  sentence: "i dont liked mondays",
  langauge: "hindi",
});

console.log(response);
