from mangum import Mangum

# Import your FastAPI application instance
from main import app as fastapi_app

# Create handler for Vercel serverless function
handler = Mangum(fastapi_app, lifespan="off") 