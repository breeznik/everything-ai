import os

from openai import OpenAI
import dotenv

dotenv.load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

completion = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role":"system" , "content":"You're a helpful assistant."},
        {"role":"user" , "content":"Write a limerick about the python programming language."}
    ]
)

response = completion.choices[0].message.content
print(completion)
