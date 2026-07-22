FROM python:3.11-slim
WORKDIR /app
COPY whisper_adaptation ./whisper_adaptation
COPY experiments ./experiments
COPY fixtures ./fixtures
CMD ["python", "-m", "whisper_adaptation", "demo"]
