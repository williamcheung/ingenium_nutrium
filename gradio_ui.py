from dotenv import load_dotenv
load_dotenv()

import gradio as gr
import os

from langchain.schema import AIMessage, HumanMessage
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(temperature=1.0, model=os.getenv('OPENAI_MODEL'))

def ask_ai(message: str, history: list[tuple[str, str]]) -> str:
    history_langchain_format: list[HumanMessage|AIMessage] = []

    for human, ai in history:
        if human:
            history_langchain_format.append(HumanMessage(content=human))
        history_langchain_format.append(AIMessage(content=ai))

    history_langchain_format.append(HumanMessage(content=message))

    gpt_response = llm.invoke(history_langchain_format)
    return gpt_response.content

interface = gr.ChatInterface(ask_ai,
                 title='Ingenium Nutrium',
                 chatbot=gr.Chatbot(
                     height=750,
                     value=[(None,
"""
Hi, give me a list of ingredients for a meal you'd like to make...
and I'll whip up a recipe for you!
plus I'll even give you the nutritional value of your meal :)
"""
                    )])
                 )
interface.launch(server_name='0.0.0.0')
