# Ingenium Nutrium

This is an AI-powered chatbot chef that takes ingredients you give it for a meal you'd like to make,
and whips up a recipe for you, with nutrient values of the final ingredients from the USDA Food Central API:

https://fdc.nal.usda.gov/api-guide.html

The chatbot is built in Python using the following technologies:
- OpenAI
- Gradio
- LangChain
- the USDA Food Central API

## Docker Deployment

- Copy the `.env.sample` file to a new file named `.env`.
- Edit the `.env` file and update the environment variable settings below with real keys:
```
OPENAI_API_KEY=xxx
UDSA_API_KEY=xxx
```
- For `OPENAI_API_KEY` you need to register for OpenAI and get your API key here: https://platform.openai.com/settings/profile?tab=api-keys
- For `UDSA_API_KEY` you need to register for the USDA Food Central API here: https://fdc.nal.usda.gov/api-key-signup.html
- Note for `OPENAI_MODEL` you may set the value to one of the models here: https://platform.openai.com/docs/models/continuous-model-upgrades (`gpt-4o` is recommended)

Save your changes to the `.env` file, then build the Docker image, and finally run the Docker container based on the image:
```bash
docker build -t ingenium_nutrium .
docker run --name ingenium_nutrium_container -p 7860:7860 -t ingenium_nutrium
```

Once you see the following log in the Docker container console, the chatbot is running and accessible:
```bash
Running on local URL:  http://0.0.0.0:7860
```

Access the chatbot interface on your host machine in a browser via: http://localhost:7860
