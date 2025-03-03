# Use an official Python runtime as the base image
FROM python:3.11-slim

# Install git (needed for installing py_ecc from GitHub)
RUN apt-get update && apt-get install -y git

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements.txt to the container
COPY requirements.txt /app/

# Install the dependencies from the requirements.txt file
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files into the container
COPY . /app/

# Expose the port the app will run on
EXPOSE 8000

# Set the environment variable to avoid Python buffering output
ENV PYTHONUNBUFFERED 1

# Set the command to run the app
CMD ["python", "StorageServer.py"]
