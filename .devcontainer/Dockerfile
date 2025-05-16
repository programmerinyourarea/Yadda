FROM python:3.11-slim

WORKDIR /workspace

# Install dev tools
RUN apt-get update && apt-get install -y \
    curl git nano iputils-ping netcat && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

CMD ["bash"]
