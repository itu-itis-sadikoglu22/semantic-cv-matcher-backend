# Semantic CV Matcher Backend API Contract

This document defines the backend API contract for the React frontend.

## Base URLs

Backend API base URL:

http://127.0.0.1:8000/api

Swagger documentation:

http://127.0.0.1:8000/docs

---

# 1. Health Check

## GET /health

Checks whether the backend service is running.

### Response

{
  "status": "healthy",
  "service": "semantic-cv-matcher-backend"
}

---

# 2. CV Ingestion from Raw Text

## POST /cvs

Creates a temporary CV record from raw text.

### Request

{
  "candidate_name": "Ahmet Yilmaz",
  "email": "ahmet@example.com",
  "phone": "+905551112233",
  "raw_text": "Ahmet Yilmaz Bilgisayar Mühendisliği mezunudur. Python, FastAPI, PostgreSQL, Docker, SQL ve REST API bilen Backend Developer olarak 3 yıl deneyime sahiptir.",
  "location": "Istanbul",
  "years_experience": 3
}

### Response

{
  "id": 1,
  "candidate_name": "Ahmet Yilmaz",
  "email": "ahmet@example.com",
  "phone": "+905551112233",
  "location": "Istanbul",
  "years_experience": 3,
  "raw_text_preview": "Ahmet Yilmaz Bilgisayar Mühendisliği mezunudur...",
  "extracted_entities": {
    "skills": ["Docker", "FastAPI", "PostgreSQL", "Python", "REST API", "SQL"],
    "roles": ["Backend Developer"],
    "companies": [],
    "dates": ["3 yıl"],
    "education": ["Bilgisayar Mühendisliği"]
  }
}

---

# 3. List CVs

## GET /cvs

Returns all temporarily stored CV records.

### Response

[
  {
    "id": 1,
    "candidate_name": "Ahmet Yilmaz",
    "email": "ahmet@example.com",
    "phone": "+905551112233",
    "location": "Istanbul",
    "years_experience": 3,
    "raw_text_preview": "Ahmet Yilmaz Bilgisayar Mühendisliği mezunudur...",
    "extracted_entities": {
      "skills": ["Docker", "FastAPI", "PostgreSQL", "Python", "REST API", "SQL"],
      "roles": ["Backend Developer"],
      "companies": [],
      "dates": ["3 yıl"],
      "education": ["Bilgisayar Mühendisliği"]
    }
  }
]

---

# 4. CV File Upload

## POST /cvs/upload

Uploads a CV file and extracts text from PDF, DOCX, or TXT format.

### Request Type

multipart/form-data

### Form Data

candidate_name: string, required  
file: PDF, DOCX, or TXT file, required  
email: string, optional  
phone: string, optional  
location: string, optional  
years_experience: number, optional  

### Response

{
  "id": 1,
  "candidate_name": "Ahmet Yilmaz",
  "email": "ahmet@example.com",
  "phone": "+905551112233",
  "location": "Istanbul",
  "years_experience": 3,
  "raw_text_preview": "Ahmet Yilmaz Bilgisayar Mühendisliği mezunudur...",
  "extracted_entities": {
    "skills": ["Docker", "FastAPI", "PostgreSQL", "Python"],
    "roles": ["Backend Developer"],
    "companies": [],
    "dates": ["3 yıl"],
    "education": ["Bilgisayar Mühendisliği"]
  }
}

---

# 5. Job Ingestion from Raw Text

## POST /jobs

Creates a temporary job posting record from raw text and metadata.

### Request

{
  "title": "Backend Developer",
  "company_name": "Example Tech",
  "description": "Python, FastAPI, PostgreSQL, Docker, SQL ve REST API deneyimi olan Backend Developer arıyoruz. Adayın veritabanı tasarımı, backend servis geliştirme ve API geliştirme konularında deneyimli olması beklenmektedir.",
  "location": "Istanbul",
  "seniority": "Mid-Level",
  "min_years_experience": 2
}

### Response

{
  "id": 1,
  "title": "Backend Developer",
  "company_name": "Example Tech",
  "location": "Istanbul",
  "seniority": "Mid-Level",
  "min_years_experience": 2,
  "description_preview": "Python, FastAPI, PostgreSQL, Docker, SQL ve REST API deneyimi olan Backend Developer arıyoruz...",
  "extracted_entities": {
    "skills": ["Docker", "FastAPI", "PostgreSQL", "Python", "REST API", "SQL"],
    "roles": ["Backend Developer"],
    "companies": [],
    "dates": [],
    "education": []
  }
}

---

# 6. List Jobs

## GET /jobs

Returns all temporarily stored job postings.

### Response

[
  {
    "id": 1,
    "title": "Backend Developer",
    "company_name": "Example Tech",
    "location": "Istanbul",
    "seniority": "Mid-Level",
    "min_years_experience": 2,
    "description_preview": "Python, FastAPI, PostgreSQL, Docker, SQL ve REST API deneyimi olan Backend Developer arıyoruz...",
    "extracted_entities": {
      "skills": ["Docker", "FastAPI", "PostgreSQL", "Python", "REST API", "SQL"],
      "roles": ["Backend Developer"],
      "companies": [],
      "dates": [],
      "education": []
    }
  }
]

---

# 7. Job File Upload

## POST /jobs/upload

Uploads a job posting file and extracts text from PDF, DOCX, or TXT format.

### Request Type

multipart/form-data

### Form Data

title: string, required  
file: PDF, DOCX, or TXT file, required  
company_name: string, optional  
location: string, optional  
seniority: string, optional  
min_years_experience: number, optional  

### Response

{
  "id": 1,
  "title": "Backend Developer",
  "company_name": "Example Tech",
  "location": "Istanbul",
  "seniority": "Mid-Level",
  "min_years_experience": 2,
  "description_preview": "Python, FastAPI, PostgreSQL ve Docker deneyimi olan Backend Developer arıyoruz.",
  "extracted_entities": {
    "skills": ["Docker", "FastAPI", "PostgreSQL", "Python"],
    "roles": ["Backend Developer"],
    "companies": [],
    "dates": [],
    "education": []
  }
}

---

# 8. NER Extraction

## POST /ner/extract

Extracts structured entities from raw CV or job posting text.

### Request

{
  "text": "Ahmet Python, FastAPI ve PostgreSQL bilen Backend Developer olarak 3 yıl çalıştı."
}

### Response

{
  "skills": ["FastAPI", "PostgreSQL", "Python"],
  "roles": ["Backend Developer"],
  "companies": [],
  "dates": ["3 yıl"],
  "education": []
}

---

# 9. Embedding Generation

## POST /embeddings/generate

Generates a dense vector embedding preview from raw text.

### Request

{
  "text": "Python, FastAPI ve PostgreSQL bilen backend developer adayı."
}

### Response

{
  "model_name": "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
  "dimension": 768,
  "vector_preview": [0.0123, -0.0456, 0.0789, 0.0111, -0.0022]
}

---

# 10. Semantic Text Matching

## POST /match/text

Matches one CV text and one job text using semantic similarity, skill overlap, and experience compatibility.

### Request

{
  "cv_text": "Ahmet Yilmaz Bilgisayar Mühendisliği mezunudur. Python, FastAPI, PostgreSQL ve Docker bilen Backend Developer olarak 3 yıl deneyime sahiptir.",
  "job_text": "Python, FastAPI, PostgreSQL ve Docker deneyimi olan Backend Developer arıyoruz.",
  "candidate_years_experience": 3,
  "required_years_experience": 2
}

### Response

{
  "result": {
    "similarity_score": 0.8421,
    "semantic_score": 92.1,
    "skill_score": 100.0,
    "experience_score": 100.0,
    "final_score": 95.26,
    "matched_skills": ["Docker", "FastAPI", "PostgreSQL", "Python"],
    "explanation": "The CV and job posting have a semantic score of 92.1%. The skill match score is 100.0%, and the experience score is 100.0%. The final weighted ranking score is 95.26%. Matched skills: Docker, FastAPI, PostgreSQL, Python.",
    "cv_entities": {
      "skills": ["Docker", "FastAPI", "PostgreSQL", "Python"],
      "roles": ["Backend Developer"],
      "companies": [],
      "dates": ["3 yıl"],
      "education": ["Bilgisayar Mühendisliği"]
    },
    "job_entities": {
      "skills": ["Docker", "FastAPI", "PostgreSQL", "Python"],
      "roles": ["Backend Developer"],
      "companies": [],
      "dates": [],
      "education": []
    }
  }
}

---

# 11. Top-K Job Matching

## POST /match/job/{job_id}

Matches a stored job posting with all temporarily stored CVs and returns top-k ranked candidates.

### Path Parameter

job_id: integer, required

### Query Parameters

top_k: integer, optional, default 5  
location: string, optional  
min_final_score: number, optional  

### Example URL

http://127.0.0.1:8000/api/match/job/1?top_k=5&location=Istanbul&min_final_score=70

### Response

{
  "job_id": 1,
  "job_title": "Backend Developer",
  "top_k": 5,
  "filters": {
    "location": "Istanbul",
    "min_final_score": 70
  },
  "results": [
    {
      "cv_id": 1,
      "candidate_name": "Ahmet Yilmaz",
      "job_id": 1,
      "job_title": "Backend Developer",
      "final_score": 93.0,
      "semantic_score": 88.34,
      "skill_score": 100.0,
      "experience_score": 100.0,
      "matched_skills": ["Docker", "FastAPI", "PostgreSQL", "Python", "REST API", "SQL"],
      "explanation": "The CV and job posting have a semantic score of 88.34%. The skill match score is 100.0%, and the experience score is 100.0%. The final weighted ranking score is 93.0%. Matched skills: Docker, FastAPI, PostgreSQL, Python, REST API, SQL."
    }
  ]
}

---

# Frontend Integration Notes

- Frontend should send JSON requests for raw text endpoints.
- Frontend should send multipart/form-data requests for file upload endpoints.
- Backend local API base URL is http://127.0.0.1:8000/api.
- Swagger documentation is available at http://127.0.0.1:8000/docs.
- Current CV and job storage is temporary in-memory storage.
- Stored CVs and jobs are reset when the backend server restarts.
- PostgreSQL and pgvector persistence will be added later.
- Location filter is normalized, so Istanbul, İstanbul, istanbul, and ISTANBUL should match.