from dotenv import load_dotenv
load_dotenv()

import gradio as gr
import os

from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(temperature=1.0, model=os.getenv('OPENAI_MODEL'))

def ask_ai_for_recipe(message: str, history: list[tuple[str, str]]) -> str:
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

def ask_ai_to_extract_ingredients(recipe: str):
    gpt_response = llm.invoke([HumanMessage(content=
f'''
Extract the ingredients from the recipe below.
Only list the ingredients as food names, nothing else.
Return a single line with each food name separated by a comma.
I will split your one-line response by comma and send each food to the USDA Food Central API to get that food's nutrients.
Do not include any other text in your response or you will cause my call to the USDA API to fail.
Make sure you only return one line.
If the input is NOT a recipe or you can't extract any ingredients, respond with an empty string so I know not to call the API.

<recipe>
{recipe}
</recipe>
'''.strip()
    )])
    recipe_ingredients = gpt_response.content.split(',')
    print(f'{recipe_ingredients=}')
    return recipe_ingredients

def submit_message(message: str, history: list[tuple[str, str]]) -> tuple[list[str], list[tuple[str, str]], str]:
    response: str = ask_ai_for_recipe(message, history)
    history.append((message, response))

    latest_ingredients: list[str] = ask_ai_to_extract_ingredients(response)

    return latest_ingredients, history, '' # '' clears the input text box

def retry_message(history: list[tuple[str, str]]) -> tuple[list[str], list[tuple[str, str]], str]:
    if history:
        last_message: str = history[-1][0]
        return submit_message(last_message, history[:-1])
    return [], history, ''

def undo_message(history: list[tuple[str, str]]) -> tuple[list[str], list[tuple[str, str]], str]:
    if history:
        return [], history[:-1], ''
    return [], history, ''

def clear_messages() -> tuple[list[str], list[tuple[str, str]], str]:
    return [], [], ''

with gr.Blocks() as demo:
    latest_ingredients_var = gr.State([])

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
'''.strip()
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

    send_button.click(submit_message, inputs=[msg, chatbot], outputs=[latest_ingredients_var, chatbot, msg])
    retry_button.click(retry_message, inputs=[chatbot], outputs=[latest_ingredients_var, chatbot, msg])
    undo_button.click(undo_message, inputs=[chatbot], outputs=[latest_ingredients_var, chatbot, msg])
    clear_button.click(clear_messages, outputs=[latest_ingredients_var, chatbot, msg])

demo.launch(server_name='0.0.0.0')
