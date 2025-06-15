from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Global database variables
client = None
db = None

def initialize_database():
    """Initialize database connection and return database instance."""
    global client, db
    
    try:
        client = MongoClient(os.getenv("MONGODB_URI", "mongodb://localhost:27017/"))
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
    """Get the database instance."""
    if db is None:
        raise RuntimeError("Database not initialized. Call initialize_database() first.")
    return db

def close_database():
    """Close database connection."""
    global client
    if client:
        client.close()
        print("MongoDB connection closed") 