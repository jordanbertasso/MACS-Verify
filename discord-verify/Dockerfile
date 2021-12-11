FROM python:rc-buster

WORKDIR /bot

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install -U git+https://github.com/Rapptz/discord-ext-menus

COPY . .

ENV AWS_CONFIG_FILE=./aws/config
ENV AWS_SHARED_CREDENTIALS_FILE=./aws/credentials

CMD ["python", "-m", "src.bot"]