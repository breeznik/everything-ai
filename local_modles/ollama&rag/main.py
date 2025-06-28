from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

model = OllamaLLM(model="llama3.2")

template = """
You are an story teller and will intoduce the user to the story and guide them into the tale of Aetherium of Kalen

here is the relvent context for the story: {story_context}

here is the user query: {query}
"""
prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model

while True:
    query = input("Input your query (q to quit): ")
    if query == 'q':
        break

    result = chain.invoke({"story_context":"In a world where magic is woven from sound, a deaf artificer discovers a forbidden form of power that relies on silence, attracting the attention of an ancient order sworn to prevent its return." , "query":{query}})

    print(result)