import os
from openai import OpenAI
from pydantic import BaseModel , Field
import dotenv
import json

dotenv.load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def sum(num1 , num2):
    """This is funciton for addition of two numbers"""
    print("hello" , num1 , num2)
    return (num1 + num2)

def sub(num1 , num2):
    """This is funciton for subtraction of two numbers"""
    return (num1 - num2)

sum_def = {
    "type": "function",
    "function":{
        "name":"addition",
        "description":"get the adddition provided for the two input numbers",
        "parameters":{
            "type":"object",
            "properties":{
                "num1":{"type":"number"},
                "num2":{"type":"number"},
            },
            "required":["num1", "num2"] ,
            "additionalProperties":False
        },
        "strict":True
    }
}

sub_def = {
    "type": "function",
    "function":{
        "name":"subtraction",
        "description":"get the subtraction provided for the two input numbers",
        "parameters":{
            "type":"object",
            "properties":{
                "num1":{"type":"number"},
                "num2":{"type":"number"},
            },
            "required":["num1", "num2"] ,
            "additionalProperties":False,
        },
        "strict":True
    }
}
tools = [sum_def , sub_def]
system_prompt = "you are an helpful assistant"

user_prompt = "what will be the addition and subtraction for 1 and 4"

messages = [
    {"role":"system", "content":system_prompt},
    {"role":"user", "content":user_prompt},
]


completion = client.chat.completions.create( model="gpt-4o", messages=messages , tools=tools    )

print(completion.choices[0].message.content)

#  execute the functions 
def call_function(name, args):
    if name == "addition":
        return sum(++args)
    elif name == "subtraction":
        return sub(++args)
    
for tool_call in completion.choices[0].message.tool_calls:
    name = tool_call.function.name
    args = json.loads(tool_call.function.arguments)
    
    messages.append({"role":"tool" , "tool_call_id":tool_call.id , content:""})