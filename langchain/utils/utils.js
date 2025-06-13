
export function combineDocuments(docs) {
  return docs.map((doc) => doc.pageContent).join("\n\n");
}

export function formateConvHistory(messages) {
  return messages.join("\n");
}
