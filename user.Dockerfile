FROM python:3-slim
WORKDIR /templates
COPY /templates /templates/
WORKDIR /static
COPY /static /static/
WORKDIR /microservices
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY ./microservices/user.py .
CMD [ "python", "./user.py" ]