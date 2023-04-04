FROM python:3-slim
WORKDIR /microservices
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY ./microservices/invokes.py ./microservices/file_report.py ./
CMD [ "python", "./file_report.py" ]