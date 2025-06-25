# AnalyQuiz - Syllabus-Based MCQ Quiz Platform

A full-stack web application that allows users to upload PDF syllabi and generate personalized multiple-choice question (MCQ) quizzes using AI/LLM technology. The system provides detailed feedback and analysis based on user performance.

## Features

- **PDF Upload**: Upload syllabus PDFs with automatic text extraction
- **AI-Powered Quiz Generation**: Generate MCQ quizzes based on syllabus content
- **Interactive Quiz Taking**: Timed quizzes with modern UI
- **Detailed Results**: Comprehensive score analysis and feedback
- **User Authentication**: Secure sign-up and login system
- **Quiz History**: Track and review past quiz attempts
- **AI Feedback**: Personalized study recommendations and analysis

## Tech Stack

### Frontend
- React 18 (via CDN)
- Tailwind CSS for styling
- Single-page HTML application
- Modern JavaScript (ES6+)

### Backend
- FastAPI (Python 3.10+)
- MongoDB with PyMongo
- JWT authentication
- PDF processing (PyPDF2, pdfplumber)
- LLM integration (placeholder for Grok API)

### Database
- MongoDB with collections for users, syllabi, quizzes, and results

## Project Structure

```
AnalyQuiz/
├── main.py                 # FastAPI application setup
├── requirements.txt        # Python dependencies
├── env_example.txt        # Environment variables template
├── index.html             # Frontend single-page application
├── components.js          # Additional React components
├── routers/               # FastAPI route handlers
│   ├── __init__.py
│   ├── auth.py           # Authentication endpoints
│   ├── syllabus.py       # PDF upload and management
│   ├── quiz.py           # Quiz generation and submission
│   └── feedback.py       # AI feedback generation
├── utils/                 # Utility functions
│   ├── __init__.py
│   ├── pdf_processor.py  # PDF text extraction
│   └── llm_client.py     # LLM API integration
└── uploads/              # PDF file storage (created automatically)
```

## Setup Instructions

### Prerequisites

- Python 3.10 or higher
- MongoDB (local installation or Docker)
- Modern web browser

### 1. Clone the Repository

```bash
git clone <repository-url>
cd AnalyQuiz
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up MongoDB

**Option A: Local MongoDB Installation**
- Download and install MongoDB from https://www.mongodb.com/try/download/community
- Start the MongoDB service
- Default connection: `mongodb://localhost:27017/`

**Option B: Docker**
```bash
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

### 4. Configure Environment Variables

1. Copy the environment template:
   ```bash
   cp env_example.txt .env
   ```

2. Edit `.env` file with your configuration:
   ```
   MONGODB_URI=mongodb://localhost:27017/
   JWT_SECRET_KEY=your-super-secret-jwt-key-here-change-this-in-production
   JWT_ALGORITHM=HS256
   JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
   LLM_API_KEY=your-llm-api-key-here
   LLM_API_URL=https://api.x.ai/v1/chat/completions
   ```

### 5. Run the Backend

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### 6. Serve the Frontend

**Option A: Using Python's built-in server**
```bash
python -m http.server 3000
```

**Option B: Using Node.js http-server**
```bash
npx http-server -p 3000
```

**Option C: Using Live Server (VS Code extension)**
- Install the Live Server extension in VS Code
- Right-click on `index.html` and select "Open with Live Server"

The frontend will be available at `http://localhost:3000`

## Usage

### 1. User Registration/Login
- Open the application in your browser
- Sign up with email and password or login if you already have an account

### 2. Upload Syllabus
- Click on the upload area on the homepage
- Select a PDF file (max 10MB)
- Wait for text extraction to complete

### 3. Generate Quiz
- Click "Generate Quiz" on any uploaded syllabus
- The system will create 10 MCQ questions based on the syllabus content
- Quiz generation may take a few seconds

### 4. Take Quiz
- Answer all questions within the time limit (30 minutes default)
- Submit your answers when complete

### 5. View Results
- See your score and detailed question-by-question analysis
- Generate AI feedback for personalized study recommendations
- Access your quiz history from the Results page

## API Endpoints

### Authentication
- `POST /api/auth/signup` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user info

### Syllabus Management
- `POST /api/syllabus/upload` - Upload PDF syllabus
- `GET /api/syllabus/list` - List user's syllabi
- `GET /api/syllabus/{id}` - Get syllabus details
- `DELETE /api/syllabus/{id}` - Delete syllabus

### Quiz Operations
- `POST /api/quiz/generate` - Generate quiz from syllabus
- `GET /api/quiz/{id}` - Get quiz questions
- `POST /api/quiz/submit` - Submit quiz answers
- `GET /api/quiz/results/{id}` - Get quiz result
- `GET /api/quiz/list/results` - List user's quiz results

### Feedback
- `POST /api/feedback/generate` - Generate AI feedback
- `GET /api/feedback/{id}` - Get feedback details

## Development

### LLM Integration

The application includes placeholder code for LLM integration. To implement actual LLM functionality:

1. Update `utils/llm_client.py` with your chosen LLM API
2. Replace the mock functions with actual API calls
3. Configure your LLM API key in the `.env` file

Example for Grok API integration is provided in the comments.

### Database Schema

The application uses the following MongoDB collections:

- **users**: User authentication and profile data
- **syllabi**: Uploaded PDF metadata and extracted text
- **quizzes**: Generated quiz questions and metadata
- **quiz_results**: User answers and scores
- **feedback**: AI-generated feedback and analysis

### Security Features

- Password hashing with bcrypt
- JWT token authentication
- File upload validation
- Input sanitization
- CORS configuration for cross-origin requests

## Troubleshooting

### Common Issues

1. **MongoDB Connection Error**
   - Ensure MongoDB is running
   - Check the `MONGODB_URI` in your `.env` file
   - Verify firewall settings

2. **PDF Upload Fails**
   - Check file size (max 10MB)
   - Ensure file is a valid PDF
   - Verify upload directory permissions

3. **Frontend Not Loading**
   - Check if the backend is running on port 8000
   - Ensure CORS is properly configured
   - Clear browser cache

4. **Quiz Generation Fails**
   - Check LLM API configuration
   - Verify the syllabus text was extracted properly
   - Check backend logs for errors

### Logs and Debugging

- Backend logs are displayed in the terminal where you run `uvicorn`
- Frontend errors can be viewed in the browser's developer console
- Enable debug mode in FastAPI for detailed error messages

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Support

For questions and support, please open an issue in the repository or contact the development team.

---

**Note**: This application includes placeholder implementations for LLM integration. For production use, implement actual LLM API calls and ensure proper error handling and rate limiting. 