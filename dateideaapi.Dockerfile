FROM python:3-slim
WORKDIR /microservices
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY ./microservices/dateideaapi.py ./
CMD [ "python", "./dateideaapi.py" ]