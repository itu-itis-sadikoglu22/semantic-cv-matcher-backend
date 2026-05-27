# Semantic CV Matcher Backend API Contract

Base URL:

http://127.0.0.1:8000/api

Swagger URL:

http://127.0.0.1:8000/docs

## 1. Health Check

GET /health

Response:

{
  "status": "healthy",
  "service": "semantic-cv-matcher-backend"
}

## 2. CV Ingestion

POST /cvs

Request:

{
  "candidate_name": "Ahmet Yilmaz",
  "email": "ahmet@example.com",
  "phone": "+905551112233",
  "raw_text": "Ahmet Yilmaz Bilgisayar Mühendisliği mezunudur. Python, FastAPI, PostgreSQL ve Docker bilen Backend Developer olarak 3 yıl deneyime sahiptir.",
  "location": "Istanbul",
  "years_experience": 3
}

## 3. Job Ingestion

POST /jobs

Request:

{
  "title": "Backend Developer",
  "company_name": "Example Tech",
  "description": "Python, FastAPI, PostgreSQL ve Docker deneyimi olan Backend Developer arıyoruz.",
  "location": "Istanbul",
  "seniority": "Mid-Level",
  "min_years_experience": 2
}

## 4. NER Extraction

POST /ner/extract

Request:

{
  "text": "Ahmet Python, FastAPI ve PostgreSQL bilen Backend Developer olarak 3 yıl çalıştı."
}

## 5. Embedding Generation

POST /embeddings/generate

Request:

{
  "text": "Python, FastAPI ve PostgreSQL bilen backend developer adayı."
}

## 6. Semantic Text Matching

POST /match/text

Request:

{
  "cv_text": "Ahmet Yilmaz Bilgisayar Mühendisliği mezunudur. Python, FastAPI, PostgreSQL ve Docker bilen Backend Developer olarak 3 yıl deneyime sahiptir.",
  "job_text": "Python, FastAPI, PostgreSQL ve Docker deneyimi olan Backend Developer arıyoruz.",
  "candidate_years_experience": 3,
  "required_years_experience": 2
}

Frontend should use this base URL:

http://127.0.0.1:8000/api