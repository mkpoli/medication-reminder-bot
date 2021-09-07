FROM python:3.9

WORKDIR /app

ENV DEPLOY_MODE=prod

RUN pip install --upgrade pip && pip install pipenv
COPY ["Pipfile", "Pipfile.lock", "./"]
RUN pipenv install --system --deploy

COPY . .

CMD ["python", "bot.py"]
