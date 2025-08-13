FROM python:3.13.5-slim-bookworm
RUN pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cpu
RUN apt-get update && apt-get install -y wget nano procps
WORKDIR /workspace
COPY . .
CMD [ "python", "./call_toy_gpt_lib.py"]
EOF
