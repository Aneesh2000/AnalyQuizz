from pymongo import MongoClient
import os
from dotenv import load_dotenv
import certifi

# Load environment variables
load_dotenv()

# Global database variables
client = None
db = None

def initialize_database():
    """Initialize database connection and return database instance."""
    global client, db
    
    try:
        client = MongoClient(os.getenv("MONGODB_URI", "mongodb://localhost:27017/"), tlsCAFile=certifi.where())
        db = client.analyquiz
        
        # Create indexes for better performance
        db.users.create_index("email", unique=True)
        db.syllabi.create_index("user_id")
        db.quizzes.create_index("user_id")
        db.quiz_results.create_index("user_id")
        db.feedback.create_index("user_id")
        
        print("Connected to MongoDB successfully")
        return db
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
        raise

def get_database():
    """Return the database instance, initializing it if necessary.

    Some serverless platforms (e.g., Vercel) do not always trigger FastAPI
    lifespan events, which means ``initialize_database`` may never run on the
    cold-start of a function.  To make the code more robust we perform a lazy
    initialization here rather than raising an error.
    """

    global db
    if db is None:
        # Attempt a one-time initialization. Any errors are propagated so the
        # caller still receives a clear 500 response with a meaningful log.
        initialize_database()

    return db

def close_database():
    """Close database connection."""
    global client
    if client:
        client.close()
        print("MongoDB connection closed") 