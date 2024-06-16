FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Add the requirements file to the container
ADD requirements.txt .

# Install the app dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code into the container
COPY . .

# Command to run the app on container startup
CMD ["python", "-u", "/app/gradio_ui.py"]
