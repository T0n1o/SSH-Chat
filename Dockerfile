FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY ssh_chat /app/ssh_chat

EXPOSE 2222

# Por padrão usa user=chat e password vindo de env SSH_CHAT_PASSWORD
CMD ["python", "-m", "ssh_chat.server", "--host", "0.0.0.0", "--port", "2222", "--user", "chat"]

