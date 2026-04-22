import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
HIRING_AGENT_API_KEY = os.getenv("HIRING_AGENT_API_KEY")
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://ferret_hr:digging_for_gold_resumes@127.0.0.1:27017/hiring_agent")
MONGODB_DB = os.getenv("MONGODB_DB", "hiring_agent")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HTTP_USER_AGENT_CONTACT = os.getenv("HTTP_USER_AGENT_CONTACT", "admin@example.com")
UPLOADS_DIR = os.getenv("UPLOADS_DIR", "uploads")
