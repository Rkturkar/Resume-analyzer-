# ═══════════════════════════════════════════
# prompts.py — Domain-specific resume prompts
#
# Each domain has its own expected tech stack
# so the LLM gives targeted, relevant feedback.
# ═══════════════════════════════════════════

# Domain context: skills, tools, and job titles for each track
DOMAIN_CONTEXT = {
    "Data Science": {
        "skills": ["Python", "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch",
                   "Scikit-learn", "Pandas", "NumPy", "SQL", "Statistics", "NLP", "OpenCV"],
        "tools":  ["Jupyter Notebook", "Matplotlib", "Seaborn", "Spark", "Hadoop",
                   "Tableau", "Power BI", "Hugging Face", "Keras"],
        "titles": ["Data Scientist", "ML Engineer", "AI Engineer", "Research Scientist"]
    },
    "MERN Stack": {
        "skills": ["MongoDB", "Express.js", "React.js", "Node.js", "JavaScript",
                   "TypeScript", "REST APIs", "Redux", "Tailwind CSS", "JWT", "GraphQL"],
        "tools":  ["Git", "Docker", "Postman", "Webpack", "Vite", "Vercel", "AWS S3"],
        "titles": ["Full Stack Developer", "MERN Developer", "Frontend Developer", "Backend Developer"]
    },
    "Data Analytics": {
        "skills": ["SQL", "Excel", "Power BI", "Tableau", "Python", "R",
                   "Data Cleaning", "Statistical Analysis", "DAX", "ETL", "A/B Testing"],
        "tools":  ["Power Query", "Google Analytics", "BigQuery", "Snowflake",
                   "Looker", "Databricks", "dbt"],
        "titles": ["Data Analyst", "Business Analyst", "BI Analyst", "Analytics Engineer"]
    },
    "Java Fullstack": {
        "skills": ["Java", "Spring Boot", "Hibernate", "JPA", "REST APIs",
                   "Microservices", "Maven", "Gradle", "MySQL", "PostgreSQL", "React.js"],
        "tools":  ["IntelliJ IDEA", "Git", "Jenkins", "Docker", "Kubernetes",
                   "SonarQube", "Swagger", "Redis"],
        "titles": ["Java Developer", "Java Full Stack Developer", "Backend Engineer", "Software Engineer"]
    },
    "Python Developer": {
        "skills": ["Python", "Django", "Flask", "FastAPI", "REST APIs",
                   "SQLAlchemy", "PostgreSQL", "Redis", "pytest", "OOP", "Celery"],
        "tools":  ["Git", "Docker", "Postman", "PyCharm", "Linux", "AWS Lambda",
                   "Nginx", "Gunicorn"],
        "titles": ["Python Developer", "Backend Developer", "Software Engineer", "API Developer"]
    },
    "DevOps Engineer": {
        "skills": ["Docker", "Kubernetes", "CI/CD", "Jenkins", "GitHub Actions",
                   "Terraform", "Ansible", "AWS", "Linux", "Shell Scripting",
                   "Prometheus", "Grafana"],
        "tools":  ["Git", "ELK Stack", "ArgoCD", "Datadog", "Vault",
                   "Helm", "Packer", "Pulumi"],
        "titles": ["DevOps Engineer", "SRE", "Cloud Engineer", "Platform Engineer", "Infrastructure Engineer"]
    },
}


def build_prompt(resume_text: str, domain: str) -> str:
    """
    Builds a domain-specific, structured JSON analysis prompt.
    Trims resume to 3000 chars for speed (Groq is fast but still costs tokens).
    """
    ctx = DOMAIN_CONTEXT.get(domain, DOMAIN_CONTEXT["Python Developer"])

    # Trim resume to keep tokens low + inference fast
    # Groq's llama3-70b handles 8k context but we stay efficient
    trimmed_resume = resume_text[:3000]

    skills_list  = ", ".join(ctx["skills"][:10])
    tools_list   = ", ".join(ctx["tools"][:7])
    titles_list  = ", ".join(ctx["titles"])

    return f"""Analyze this resume for a {domain} role. Return ONLY a valid JSON object.

TARGET DOMAIN: {domain}
EXPECTED SKILLS: {skills_list}
EXPECTED TOOLS: {tools_list}
TYPICAL JOB TITLES: {titles_list}

RESUME TEXT:
\"\"\"
{trimmed_resume}
\"\"\"

Return this exact JSON structure (no extra text, no markdown, raw JSON only):
{{
  "ats_score": <integer 0-100>,
  "domain": "{domain}",
  "experience_level": "<Fresher|Junior|Mid-Level|Senior|Lead>",
  "overall_verdict": "<Excellent|Good|Needs Work|Poor>",
  "summary": "<2-3 honest sentences about this candidate for a {domain} role>",
  "skills_quality": [
    {{"skill": "<skill name>", "score": <0-100>, "found": <true|false>}}
  ],
  "keywords_found": ["<keyword1>", "<keyword2>"],
  "missing_keywords": ["<keyword1>", "<keyword2>"],
  "missing_sections": ["<section name>"],
  "strengths": ["<strength1>", "<strength2>"],
  "suggestions": [
    {{"priority": "<High|Medium|Low>", "text": "<specific actionable improvement>"}}
  ],
  "section_scores": {{
    "contact_info": <0-100>,
    "professional_summary": <0-100>,
    "work_experience": <0-100>,
    "education": <0-100>,
    "skills_section": <0-100>,
    "projects": <0-100>,
    "formatting": <0-100>
  }}
}}

RULES:
- skills_quality: include ALL {domain} skills from the expected list above (mark found:true/false)
- keywords_found: list actual keywords you found in the resume text
- missing_keywords: list important {domain} keywords NOT in resume
- suggestions: give 4-6 specific, actionable items (not generic advice)
- ats_score: be honest — a weak resume should score 30-50, a good one 70-90
- Start response with {{ — no explanation before or after the JSON"""