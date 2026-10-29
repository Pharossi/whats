FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py rules.py ./
RUN useradd --uid 10001 --create-home worker
USER worker
EXPOSE 8000
CMD ["python", "app.py"]
