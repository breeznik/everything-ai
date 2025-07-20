import os
from openai import OpenAI
from pydantic import BaseModel
import dotenv

dotenv.load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# response formate
class CalenderEvent(BaseModel):
    name: str
    date: str
    participants: list[str]
    
# call the model
completion = client.beta.chat.completions.parse(
    model="gpt-4o",
    messages=[
        {"role":"system" , "content":"Extract the even information"},
        {"role":"user", "content":"Nikhil and Jhon is at science fair on 21st of june 2025"} 
    ],
    response_format=CalenderEvent
)


print(dict(completion.choices[0].message.parsed))
    
    