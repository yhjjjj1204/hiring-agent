import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
HIRING_AGENT_API_KEY = os.getenv("HIRING_AGENT_API_KEY")
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "hiring_agent")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
