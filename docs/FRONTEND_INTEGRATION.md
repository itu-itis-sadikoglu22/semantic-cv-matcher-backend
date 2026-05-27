# Frontend Integration Notes

This document explains how the React frontend should integrate with the Semantic CV Matcher backend.

## Current Backend Status

The backend currently supports the main demo flow using temporary in-memory storage.

Implemented features:

- CV ingestion from raw text
- Job posting ingestion from raw text
- CV file upload
- Job posting file upload
- NER/entity extraction
- Embedding generation
- CV-job semantic matching
- Top-k candidate ranking for a stored job
- Metadata filtering by location and minimum final score
- Turkish city name normalization for location filtering
- CV detail endpoint
- Job detail endpoint

Important note:

The current backend stores CVs and job postings in memory. This means stored records are reset when the backend server restarts. PostgreSQL and pgvector persistence will be added later.

---

## Backend Base URL

Use this base URL during local development:

```text
http://127.0.0.1:8000/api


Swagger documentation:
http://127.0.0.1:8000/docs


Recommended Demo Flow

The recommended frontend demo flow is:

Add or upload one or more CVs
Add or upload one job posting
Run top-k matching for the selected job
Display ranked CV results
Show matched skills, scores, and explanation
Optionally open CV or job detail page by ID
Main Endpoints for Frontend
1. Create CV from Raw Text
POST /cvs

Request body:

{
  "candidate_name": "Ahmet Yilmaz",
  "email": "ahmet@example.com",
  "phone": "+905551112233",
  "raw_text": "Ahmet Yilmaz Bilgisayar Mühendisliği mezunudur. Python, FastAPI, PostgreSQL, Docker, SQL ve REST API bilen Backend Developer olarak 3 yıl deneyime sahiptir.",
  "location": "Istanbul",
  "years_experience": 3
}
2. Upload CV File
POST /cvs/upload

Request type:

multipart/form-data

Form fields:

candidate_name: required
file: required, PDF/DOCX/TXT
email: optional
phone: optional
location: optional
years_experience: optional

Frontend should use FormData.

Example logic:

const formData = new FormData();

formData.append("candidate_name", candidateName);
formData.append("file", selectedFile);
formData.append("email", email);
formData.append("phone", phone);
formData.append("location", location);
formData.append("years_experience", yearsExperience);

const response = await fetch("http://127.0.0.1:8000/api/cvs/upload", {
  method: "POST",
  body: formData
});

Do not manually set the Content-Type header for FormData. The browser will set it automatically.

3. List CVs
GET /cvs

Returns all temporarily stored CV records.

4. Get CV Detail
GET /cvs/{cv_id}

Example:

GET /cvs/1
5. Create Job Posting from Raw Text
POST /jobs

Request body:

{
  "title": "Backend Developer",
  "company_name": "Example Tech",
  "description": "Python, FastAPI, PostgreSQL, Docker, SQL ve REST API deneyimi olan Backend Developer arıyoruz. Adayın veritabanı tasarımı, backend servis geliştirme ve API geliştirme konularında deneyimli olması beklenmektedir.",
  "location": "Istanbul",
  "seniority": "Mid-Level",
  "min_years_experience": 2
}
6. Upload Job Posting File
POST /jobs/upload

Request type:

multipart/form-data

Form fields:

title: required
file: required, PDF/DOCX/TXT
company_name: optional
location: optional
seniority: optional
min_years_experience: optional

Frontend should use FormData.

Example logic:

const formData = new FormData();

formData.append("title", title);
formData.append("file", selectedFile);
formData.append("company_name", companyName);
formData.append("location", location);
formData.append("seniority", seniority);
formData.append("min_years_experience", minYearsExperience);

const response = await fetch("http://127.0.0.1:8000/api/jobs/upload", {
  method: "POST",
  body: formData
});
7. List Jobs
GET /jobs

Returns all temporarily stored job postings.

8. Get Job Detail
GET /jobs/{job_id}

Example:

GET /jobs/1
9. Run Top-K Matching for a Stored Job
POST /match/job/{job_id}

Example URL:

POST /match/job/1?top_k=5&location=Istanbul&min_final_score=70

Query parameters:

top_k: optional, default 5, minimum 1, maximum 20
location: optional
min_final_score: optional, minimum 0, maximum 100

Example response:

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
Recommended Frontend Pages

Suggested frontend pages/components:

CV upload/create page
Job posting upload/create page
CV list page
Job list page
Matching results page
CV detail modal or page
Job detail modal or page
Score Explanation

The backend returns multiple scores:

semantic_score: semantic similarity between CV and job text
skill_score: overlap between extracted CV skills and job skills
experience_score: compatibility between candidate experience and required experience
final_score: weighted final ranking score

The frontend should primarily sort and display candidates by final_score.

Location Filtering Note

The backend normalizes Turkish city names during filtering.

The following values should match:

Istanbul
İstanbul
istanbul
ISTANBUL
Error Handling Notes

Common status codes:

200 OK: request successful
400 Bad Request: uploaded file is unsupported or unreadable
404 Not Found: CV or job record does not exist
422 Unprocessable Content: request validation failed

Example 422 cases:

Required field is missing
raw_text is too short
top_k is greater than 20
min_final_score is outside 0–100
Current Limitations

Current limitations of the backend:

Data is stored temporarily in memory
Data is reset after backend restart
PostgreSQL persistence is not active yet
pgvector similarity search is not active yet
Current NER implementation uses a rule-based fallback approach
Hugging Face model is currently used for embedding generation

These limitations are expected at this stage and will be improved in later backend phases.