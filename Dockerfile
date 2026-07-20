FROM python:3.11-slim

# ffmpeg is required by pytgcalls to transcode/stream audio into voice chats
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg git && \
    rm -rf /var/lib/apt/lists/*   
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir --no-deps py-tgcalls==2.1.2b3

COPY . .

CMD ["python", "main.py"]
