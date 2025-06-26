from mangum import Mangum

# Import your FastAPI application instance
from main import app as fastapi_app

# Vercel looks for a `handler` callable compatible with AWS Lambda
handler = Mangum(fastapi_app) 