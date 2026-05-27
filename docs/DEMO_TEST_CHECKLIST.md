# Backend Demo Test Checklist

This document defines the recommended backend demo test flow for the Semantic CV Matcher project.

## Current Demo Status

The backend currently supports an end-to-end MVP demo using temporary in-memory storage.

The following features are ready for local demonstration:

- Health check
- CV creation from raw text
- CV file upload
- Job posting creation from raw text
- Job posting file upload
- NER/entity extraction
- Embedding generation
- Semantic CV-job matching
- Top-k candidate ranking for a stored job
- Metadata filtering by location and minimum final score
- CV detail endpoint
- Job detail endpoint

Important note:

The current backend uses temporary in-memory storage. This means all CV and job records are deleted when the backend server restarts.

---

## 1. Start Backend Server

Run the backend locally:

```powershell
uvicorn app.main:app --reload

Expected terminal output:

Application startup complete.
Uvicorn running on http://127.0.0.1:8000

Open Swagger:

http://127.0.0.1:8000/docs
2. Health Check

Endpoint:

GET /api/health

Expected status:

200 OK

Expected response:

{
  "status": "healthy",
  "service": "semantic-cv-matcher-backend"
}
3. Create First CV

Endpoint:

POST /api/cvs

Request body:

{
  "candidate_name": "Ahmet Yilmaz",
  "email": "ahmet@example.com",
  "phone": "+905551112233",
  "raw_text": "Ahmet Yilmaz Bilgisayar Mühendisliği mezunudur. Python, FastAPI, PostgreSQL, Docker, SQL ve REST API bilen Backend Developer olarak 3 yıl deneyime sahiptir. Veritabanı tasarımı ve backend servis geliştirme konularında çalışmıştır.",
  "location": "Istanbul",
  "years_experience": 3
}

Expected status:

200 OK

Expected checks:

Response contains "id": 1
Response contains extracted skills
Response contains "Backend Developer" under roles
Response contains "3 yıl" under dates
4. Create Second CV

Endpoint:

POST /api/cvs

Request body:

{
  "candidate_name": "Zeynep Kaya",
  "email": "zeynep@example.com",
  "phone": "+905554445566",
  "raw_text": "Zeynep Kaya Yazılım Mühendisliği mezunudur. React, JavaScript, Git ve REST API entegrasyonu konularında 2 yıl deneyime sahiptir. Frontend Developer olarak çalışmıştır.",
  "location": "İstanbul",
  "years_experience": 2
}

Expected status:

200 OK

Expected checks:

Response contains "id": 2
Response contains frontend-related skills
Location may be written as "İstanbul"
5. Create Third CV

Endpoint:

POST /api/cvs

Request body:

{
  "candidate_name": "Mehmet Demir",
  "email": "mehmet@example.com",
  "phone": "+905557778899",
  "raw_text": "Mehmet Demir Bilgisayar Mühendisliği mezunudur. Python, Machine Learning, NLP, Deep Learning ve PostgreSQL konularında 4 yıl deneyime sahiptir. Data Scientist olarak çalışmıştır.",
  "location": "Ankara",
  "years_experience": 4
}

Expected status:

200 OK

Expected checks:

Response contains "id": 3
Response contains data/AI-related skills
Location is "Ankara"
6. List CVs

Endpoint:

GET /api/cvs

Expected status:

200 OK

Expected checks:

Response contains 3 CV records
Ahmet Yilmaz, Zeynep Kaya, and Mehmet Demir are listed
7. Create Job Posting

Endpoint:

POST /api/jobs

Request body:

{
  "title": "Backend Developer",
  "company_name": "Example Tech",
  "description": "Python, FastAPI, PostgreSQL, Docker, SQL ve REST API deneyimi olan Backend Developer arıyoruz. Adayın veritabanı tasarımı, backend servis geliştirme ve API geliştirme konularında deneyimli olması beklenmektedir.",
  "location": "Istanbul",
  "seniority": "Mid-Level",
  "min_years_experience": 2
}

Expected status:

200 OK

Expected checks:

Response contains "id": 1
Response contains backend-related extracted skills
Response contains "Backend Developer" under roles
8. List Jobs

Endpoint:

GET /api/jobs

Expected status:

200 OK

Expected checks:

Response contains the Backend Developer job posting
Response contains "id": 1
9. Test NER Extraction

Endpoint:

POST /api/ner/extract

Request body:

{
  "text": "Ayşe Python, FastAPI ve PostgreSQL bilen Backend Developer olarak 3 yıl çalıştı. Bilgisayar Mühendisliği mezunudur."
}

Expected status:

200 OK

Expected checks:

Skills include Python, FastAPI, PostgreSQL
Roles include Backend Developer
Dates include 3 yıl
Education includes Bilgisayar Mühendisliği
10. Test Embedding Generation

Endpoint:

POST /api/embeddings/generate

Request body:

{
  "text": "Python, FastAPI ve PostgreSQL bilen backend developer adayı."
}

Expected status:

200 OK

Expected checks:

Response contains model name
Response contains dimension
Dimension should be 768
Response contains vector preview
11. Test Text-to-Text Matching

Endpoint:

POST /api/match/text

Request body:

{
  "cv_text": "Ahmet Yilmaz Bilgisayar Mühendisliği mezunudur. Python, FastAPI, PostgreSQL ve Docker bilen Backend Developer olarak 3 yıl deneyime sahiptir.",
  "job_text": "Python, FastAPI, PostgreSQL ve Docker deneyimi olan Backend Developer arıyoruz.",
  "candidate_years_experience": 3,
  "required_years_experience": 2
}

Expected status:

200 OK

Expected checks:

Response contains semantic_score
Response contains skill_score
Response contains experience_score
Response contains final_score
Response contains matched_skills
Response contains explanation
12. Test Top-K Matching

Endpoint:

POST /api/match/job/1

Query parameters:

top_k: 5
location: İstanbul
min_final_score: 70

Full example URL:

http://127.0.0.1:8000/api/match/job/1?top_k=5&location=İstanbul&min_final_score=70

Expected status:

200 OK

Expected checks:

Response contains job_id 1
Response contains filters
Response contains results
Ahmet Yilmaz should appear as a strong candidate
final_score should be visible
matched_skills should be visible
explanation should be visible
13. Test Location Normalization

Endpoint:

POST /api/match/job/1

Run the same request with different location values:

location=Istanbul
location=İstanbul
location=istanbul
location=ISTANBUL

Expected status:

200 OK

Expected checks:

Istanbul and İstanbul should match
Case differences should not break filtering
14. Test Query Parameter Validation

Endpoint:

POST /api/match/job/1

Invalid query parameters:

top_k: 999
location: İstanbul
min_final_score: 70

Expected status:

422 Unprocessable Content

Reason:

top_k must be between 1 and 20.

Another invalid test:

top_k: 5
location: İstanbul
min_final_score: 500

Expected status:

422 Unprocessable Content

Reason:

min_final_score must be between 0 and 100.

15. Test CV Detail Endpoint

Endpoint:

GET /api/cvs/1

Expected status:

200 OK

Expected checks:

Response contains Ahmet Yilmaz
Response contains extracted_entities

Invalid test:

GET /api/cvs/999

Expected status:

404 Not Found
16. Test Job Detail Endpoint

Endpoint:

GET /api/jobs/1

Expected status:

200 OK

Expected checks:

Response contains Backend Developer
Response contains extracted_entities

Invalid test:

GET /api/jobs/999

Expected status:

404 Not Found
Demo Notes

During the demo, emphasize the following points:

The system is designed for Turkish CV and job posting matching.
The backend exposes modular API endpoints for the React frontend.
Matching is not based only on keywords.
The system uses semantic embeddings for text similarity.
Final ranking also considers extracted skills and experience compatibility.
The response includes explainable matching information.
Location filtering supports Turkish spelling differences such as Istanbul and İstanbul.
Current storage is temporary and will later be replaced by PostgreSQL and pgvector.
Known Limitations at This Stage
Data is stored in memory.
Records disappear after backend restart.
pgvector-based database search is not active yet.
Current NER uses a rule-based fallback approach.
File upload text extraction depends on the quality of the uploaded document.