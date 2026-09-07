FROM python:3.12-slim-bookworm

# WeasyPrint (PDF generation) needs Pango/HarfBuzz/fontconfig at runtime,
# loaded via cffi - see app/pdf.py. Not GTK/cairo; WeasyPrint 60+ dropped that.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libfontconfig1 \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

RUN mkdir -p /app/uploads /app/data
VOLUME ["/app/uploads", "/app/data"]

ENV DATABASE_URL=sqlite:////app/data/snoeks.db

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
