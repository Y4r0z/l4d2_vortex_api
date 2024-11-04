# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.12

# Install SSH client
RUN apt-get update && apt-get install -y openssh-client

EXPOSE 3005

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install pip requirements
COPY requirements.txt .
RUN python -m pip install -r requirements.txt

# Setup SSH for root
COPY .ssh /root/.ssh
RUN chmod 700 /root/.ssh && \
    chmod 600 /root/.ssh/id_ed25519

WORKDIR /app
COPY . /app

# During debugging, this entry point will be overridden.
CMD ["gunicorn", "--bind", "0.0.0.0:3005", "-k", "uvicorn.workers.UvicornWorker", "-t 40", "-w 4", "main:app"]