from dotenv import load_dotenv
load_dotenv()

import gradio as gr
import os

from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from nutrients_service import get_nutrient_data

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

def ask_ai_to_format_nutrients(nutrients_by_ingredient: list[dict[str, list[dict[str, str | int | float]]]]):
    gpt_response = llm.invoke([HumanMessage(content=
f'''
Format the Python list of dicts below for a non-technical user who wants to know the nutrient values of ingredients ("foods") in a recipe.
Each dict in the list has key 'food' (str) and value set to a list of other dictionaries, each representing a nutrient with the following keys:
- 'nutrientName' (str)
- 'value' (int or float)
- 'unitName' (str)

Format your response in Markdown to make it easy for the user to read the nutrients for each food in the recipe they're interested in.
Do not re-order the nutrients, they are already sorted by weight.
Use user-friendly labels but keep the same unit names for weight, which are in Metric.

Your response will be shown directly to the user, so DO NOT begin your response with anything like "Here is a formatted list..." that is meant for me.
I am not going to review your response at all, I will show it directly to the user!
You can start with a title like "Nutrient Values of Ingredients in the Recipe" that will make sense to the user.

<nutrients_by_ingredient>
{nutrients_by_ingredient}
</nutrients_by_ingredient>
'''.strip()
    )])
    return gpt_response.content

# send_button click handler
def submit_message(message: str, history: list[tuple[str, str]]) -> tuple[list[str], list[tuple[str, str]], str]:
    response: str = ask_ai_for_recipe(message, history)
    history.append((message, response))

    latest_ingredients: list[str] = ask_ai_to_extract_ingredients(response)

    return latest_ingredients, history, '' # '' clears the input text box

# retry_button click handler
def retry_message(history: list[tuple[str, str]]) -> tuple[list[str], list[tuple[str, str]], str]:
    if history:
        last_message: str = history[-1][0]
        return submit_message(last_message, history[:-1])
    return [], history, ''

# undo_message click handler
def undo_message(history: list[tuple[str, str]]) -> tuple[list[str], list[tuple[str, str]], str]:
    if history:
        return [], history[:-1], ''
    return [], history, ''

# clear_button click handler
def clear_messages() -> tuple[list[str], list[tuple[str, str]], str]:
    return [], [], ''

# nutrients_button click handler
def get_nutrients(history: list[tuple[str, str]], latest_ingredients: list[str]) -> tuple[list[str], list[tuple[str, str]]]:
    ingredients = [ingredient for ingredient in latest_ingredients if ingredient.strip()]
    if not ingredients:
        return [], history

    nutrients_by_ingredient = []
    for ingredient in ingredients:
        print(f'\ngetting nutrients from USDA for [{ingredient}]...')
        nutrients = get_nutrient_data(ingredient)
        if nutrients:
            nutrients_by_ingredient.append(nutrients)

    if nutrients_by_ingredient:
        formatted_nutrients = ask_ai_to_format_nutrients(nutrients_by_ingredient)
        history.append((None, formatted_nutrients))

    return [], history

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

    nutrients_button.click(get_nutrients, inputs=[chatbot, latest_ingredients_var], outputs=[latest_ingredients_var, chatbot])

demo.launch(server_name='0.0.0.0')
