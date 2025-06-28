from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
import os
import re

# Read the text file
with open("AetheriumOfKalen.txt", "r", encoding="utf-8") as file:
    content = file.read()

# This function splits the text into sections using lines that look like headers
# For example: 'LOGLINE:', '1. WORLD LORE:', etc.
def split_into_sections(text):
    sections = []
    header = None
    section_lines = []
    for line in text.splitlines():
        # If the line looks like a section header
        if re.match(r"^[A-Z0-9 .\-]+:.*$", line.strip()):
            # Save the previous section if it exists
            if header and section_lines:
                sections.append((header, "\n".join(section_lines).strip()))
            header = line.strip()
            section_lines = []
        else:
            section_lines.append(line)
    # Add the last section
    if header and section_lines:
        sections.append((header, "\n".join(section_lines).strip()))
    return sections

# Create the embedding model
embeddings = OllamaEmbeddings(model="mxbai-embed-large")

# Set the location for the database
db_location = "./chrome_langchain_db"

# If the database does not exist, add the documents
if not os.path.exists(db_location):
    documents = []
    ids = []
    for i, (header, section) in enumerate(split_into_sections(content)):
        if section:
            # Create a Document for each section
            doc = Document(page_content=section, metadata={"section": header})
            documents.append(doc)
            ids.append(f"AetheriumOfKalen_{i}")
    # Create the Chroma database and add the documents
    db = Chroma.from_documents(documents, embeddings, persist_directory=db_location, ids=ids)
    # No need to call db.persist(); Chroma saves automatically when using persist_directory
else:
    # If the database exists, just load it
    db = Chroma(persist_directory=db_location, embedding_function=embeddings)

print("Chroma DB is ready with section-based embeddings.")
