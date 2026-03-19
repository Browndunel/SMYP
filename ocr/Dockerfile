FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    libglib2.0-0 \
    libgl1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    easyocr \
    spacy \
    python-multipart \
    pillow \
    pdf2image \
    numpy

RUN python -m spacy download fr_core_news_sm

RUN python -c "import easyocr; easyocr.Reader(['fr', 'en'], gpu=False)"


COPY app.py .

RUN mkdir -p uploads

EXPOSE 8001

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]
