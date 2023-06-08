FROM python:3.10.6

RUN python -m pip install -q --upgrade pip

WORKDIR app/

COPY . /app/

RUN pip install -r /app/requirements.txt

CMD ["uvicorn", "--host", "0.0.0.0", "--port", "5000", "main:app"]
