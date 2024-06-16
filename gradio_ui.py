from dotenv import load_dotenv
load_dotenv()

import gradio as gr
import os

from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(temperature=1.0, model=os.getenv('OPENAI_MODEL'))

def ask_ai(message: str, history: list[tuple[str, str]]) -> str:
    history_langchain_format: list[HumanMessage|AIMessage] = [
        SystemMessage(
            content='You are a friendly and creative chef. But you only answer questions about recipes, nothing else!'
        )
    ]

    for human, ai in history:
        if human:
            history_langchain_format.append(HumanMessage(content=human))
        history_langchain_format.append(AIMessage(content=ai))

    print(f'user: {message}')
    history_langchain_format.append(HumanMessage(content=message))

    gpt_response = llm.invoke(history_langchain_format)
    return gpt_response.content

def submit_message(message: str, history: list[tuple[str, str]]) -> tuple[list[tuple[str, str]], str]:
    response: str = ask_ai(message, history)
    history.append((message, response))
    return history, '' # '' clears the input text box

def retry_message(history: list[tuple[str, str]]) -> tuple[list[tuple[str, str]], str]:
    if history:
        last_message: str = history[-1][0]
        return submit_message(last_message, history[:-1])
    return history, ''

def undo_message(history: list[tuple[str, str]]) -> tuple[list[tuple[str, str]], str]:
    if history:
        return history[:-1], ''
    return history, ''

def clear_messages() -> tuple[list[tuple[str, str]], str]:
    return [], ''

with gr.Blocks() as demo:
    gr.Markdown('<h1 style="text-align:center;">Ingenium Nutrium</h1>')

    chatbot = gr.Chatbot(
        label='Chatbot Chef',
        height='60vh',
        show_copy_button=True,
        value=[(None,
'''
Hi, give me a list of ingredients for a meal you'd like to make...
and I'll whip up a recipe for you!
plus I'll even give you the nutritional value of your meal :)
'''
        )]
    )

    with gr.Row(variant='panel'):
        with gr.Column(scale=6):
            msg = gr.Textbox(autofocus=True, label='Your ingredients', lines=2)
        with gr.Column(scale=2):
            send_button = gr.Button('Get Recipe')
            nutrients_button = gr.Button('Get Nutrients from USDA')

    with gr.Row():
        retry_button = gr.Button('Retry')
        undo_button = gr.Button('Undo')
        clear_button = gr.Button('Clear')

    send_button.click(submit_message, inputs=[msg, chatbot], outputs=[chatbot, msg])
    retry_button.click(retry_message, inputs=[chatbot], outputs=[chatbot, msg])
    undo_button.click(undo_message, inputs=[chatbot], outputs=[chatbot, msg])
    clear_button.click(clear_messages, outputs=[chatbot, msg])

demo.launch(server_name='0.0.0.0')
