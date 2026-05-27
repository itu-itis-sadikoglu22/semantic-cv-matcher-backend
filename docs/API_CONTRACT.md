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


---

## 7. CV File Upload

POST /cvs/upload

Uploads a CV file and extracts text from PDF, DOCX, or TXT format.

Form Data:

candidate_name: string  
email: string | optional  
phone: string | optional  
location: string | optional  
years_experience: number | optional  
file: PDF, DOCX, or TXT file  

Response:

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

## 8. Job File Upload

POST /jobs/upload

Uploads a job posting file and extracts text from PDF, DOCX, or TXT format.

Form Data:

title: string  
company_name: string | optional  
location: string | optional  
seniority: string | optional  
min_years_experience: number | optional  
file: PDF, DOCX, or TXT file  

Response:

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

## 9. Top-K Job Matching

POST /match/job/{job_id}

Matches a stored job posting with all stored CVs and returns top-k ranked candidates.

Query Parameters:

job_id: integer  
top_k: integer, default 5  
location: string | optional  
min_final_score: number | optional  

Example:

POST /match/job/1?top_k=5&location=Istanbul&min_final_score=70

Response:

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
      "matched_skills": ["Docker", "FastAPI", "PostgreSQL", "Python"],
      "explanation": "The CV and job posting have a semantic score of 88.34%. The skill match score is 100.0%, and the experience score is 100.0%."
    }
  ]
}