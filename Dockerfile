FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8
RUN pip install --no-cache-dir fastapi uvicorn aiofiles aiohttp python-dotenv requests

COPY requirements.txt .
RUN pip install -r requirements.txt

EXPOSE 80
COPY ./app app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "9346"]
