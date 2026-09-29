FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src ./src
COPY app.py params.yaml ./
COPY .streamlit ./.streamlit
COPY models ./models
COPY reports ./reports
RUN mkdir -p logs
EXPOSE 8000 8501
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
