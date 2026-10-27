FROM python:3.11-slim

WORKDIR /app

# Install reflex dependencies (NodeJS/Bun requires unzip/curl)
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Expose ports for Reflex (8000 for backend, 3000 for frontend if running dev)
EXPOSE 8000
EXPOSE 3000

# Initialize and run reflex on 0.0.0.0 so it is accessible from outside the container
CMD ["reflex", "run", "--env", "prod", "--backend-host", "0.0.0.0"]
