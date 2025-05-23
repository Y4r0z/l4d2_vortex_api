# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.12

EXPOSE 3005

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Logs directory
RUN mkdir -p /app/logs && chmod 777 /app/logs

# Install pip requirements
COPY requirements.txt .
RUN python -m pip install -r requirements.txt

WORKDIR /app
COPY . /app

# During debugging, this entry point will be overridden.
CMD ["gunicorn", "--bind", "0.0.0.0:3005", "-k", "uvicorn.workers.UvicornWorker", "-t", "40", "-w", "4", "main:app"]