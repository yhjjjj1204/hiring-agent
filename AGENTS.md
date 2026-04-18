# Hiring Agent Project: Agent Overview

This project implements an AI-driven hiring pipeline designed to streamline candidate evaluation while maintaining fairness and providing deep insights.

## Core Agents

### 1. HR Strategy Agent (`src/agents/hr_strategy`)
- **Role**: Requirements Definition & Refinement.
- **Mechanism**: A conversational agent built with **LangGraph**.
- **Function**: Engages in a dialogue with HR to understand the nuances of a role. It uses tools to finalize a structured `HRJobSpec` that includes required skills, bonus items, and culture-fit metrics.

### 2. Data Arrangement Agent (`src/agents/data_arrangement`)
- **Role**: Resume Structuring.
- **Mechanism**: LLM-based semantic parsing (GPT-4o-mini).
- **Function**: Takes raw OCR text from resumes and transforms it into a highly structured `ResumeStructuredProfile`. It includes built-in truncation and sanitization.

### 3. Background Analysis Agent (`src/agents/background_analysis`)
- **Role**: External Validation & Capability Mapping.
- **Mechanism**: Multi-source API orchestration (GitHub, OpenAlex, Semantic Scholar).
- **Function**: Generates a **Capability Overview Graph**. It calculates indices for code activity and academic impact, providing a visual and data-driven summary of a candidate's professional footprint.

### 4. Scoring Agent (`src/agents/scoring`)
- **Role**: Automated Matching & Evaluation.
- **Mechanism**: Structured LLM evaluation.
- **Function**: Performs a "Blind Match" by comparing the `HRJobSpec`, structured resume, and background analysis. It outputs a `Scorecard` with detailed scores and rationales.

### 5. Async Evaluation Pipeline (`src/api/routes_analyze.py`)
- **Role**: Non-blocking candidate experience.
- **Mechanism**: FastAPI BackgroundTasks + permanent file storage.
- **Function**: Immediately accepts candidate submissions and performs full LLM analysis in the background. Recruiter dashboard polls for real-time status updates (`evaluating` vs `ready`). Supports manual re-evaluation by re-processing stored resume files.

### 6. Authentication & Account System (`src/api/`)
- **Role**: Access Control & Multi-role Support.
- **Mechanism**: Token-based authentication with role-based access control (RBAC).
- **Function**: Manages user registration, login, and sessions. Differentiates between `candidate` (can upload resumes) and `recruiter` (can access the full ranking dashboard).

### 7. Jobs Management (`src/api/routes_jobs.py`)
- **Role**: Job lifecycle management.
- **Function**: Allows recruiters to create and edit job postings. Candidates can view available jobs and apply for specific roles, linking their analysis results to the selected job.

## Support Modules

### Fairness & Privacy (`src/fairness/`)
- **Blind Screening**: Automatically redacts PII (Names, Emails, Photos, Genders) from profiles before they reach the Scoring Agent to minimize unconscious bias.
- **Injection Sanitization**: Protects the pipeline from prompt injection attacks hidden within resume text.

### Monitoring & Observability (`src/monitoring/`)
- **Agent Registry**: Tracks the execution status (`running`, `completed`, `failed`) and the path taken by candidates through the multi-agent pipeline.
- **SSE Support**: Provides real-time updates to the dashboard via Server-Sent Events.

## Frontend Architecture (`frontend/`)
The frontend is a modular **Vue 3** application built with **Vite**.

- **Structure**:
  - `frontend/src/App.vue`: Main orchestration component.
  - `frontend/src/components/`: Modular UI components:
    - `ResumeUpload.vue`: Drag-and-drop file upload with validation.
    - `JobRequirementInput.vue`: Input management for Job Descriptions and background lookup overrides.
    - `AnalysisResult.vue`: Visualization of scores, confidence, and summaries.
    - `CandidateSnapshot.vue`: Structured resume data visualization.
    - `Auth.vue`: User registration and login.
    - `RecruiterDashboard.vue`: Multi-role dashboard with candidate tracking and evaluation status.
    - `JobManager.vue`: Job CRUD for recruiters.
    - `JobList.vue`: Job selection for candidates.
- **Serving Logic**: The FastAPI backend (`src/api/main.py`) serves the production build from `frontend/dist/` if present, falling back to `frontend/src/` for development mode.

## Project Structure
- `src/`: Core Python package containing all logic.
  - `agents/`: Individual agent implementations.
  - `api/`: FastAPI-based REST endpoints.
  - `graph/`: Workflow and pipeline definitions.
  - `db/`: Database connection management.
  - `fairness/`: PII redacting and sanitization.
  - `monitoring/`: Runtime tracking.
  - `config.py`: Centralized environment configuration.
  - `version.py`: Version metadata.
- `frontend/`: Vue 3 application source code.
- `uploads/`: Permanent storage for candidate resumes.

## LLM Interaction & Engineering Guidelines

1. **Commit Protocol**: When a major functionality or feature is added, the LLM must prompt the user to commit the changes to version control.
2. **Standard Language**: All code comments and documentation MUST be written in **English**, even if the user provides prompts in other languages (e.g., Chinese).
3. **Architectural Integrity**: Maintain clean, organized code. Before implementing changes, consider the entire system architecture. Avoid "patch-like" fixes; instead, act as a lead **Architectural Engineer** to ensure changes are seamless, idiomatic, and maintainable.
4. **Documentation Maintenance**: When the file structure is changed or updated, or new functionality is added, the LLM must check and update `AGENTS.md` to ensure it remains the accurate source of truth.
