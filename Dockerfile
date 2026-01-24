# Use an official NVIDIA CUDA runtime as a parent image
FROM nvidia/cuda:12.4.0-devel-ubuntu22.04

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-pip \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt
RUN pip3 install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on
EXPOSE 8888

# Define the command to run the app
CMD ["python3", "app.py"]