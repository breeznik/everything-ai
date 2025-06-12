import * as readline from "node:readline/promises";

export const terminal = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
});

const messages = [];

// message template
const msgTemp = (role, content) => ({ role, content });

async function main() {
  while (true) {
    const userInput = await terminal.question("You: ");
    if (userInput.trim()) {
      messages.push(msgTemp("user", userInput));
      console.log("user message", userInput);
      console.log("message array", messages);
    } else {
      console.error("empty messages are not allowed");
    }
  }
}
main().catch(console.error);
