# AI Tutoring Assistant

A comprehensive AI-powered tutoring platform built with FastAPI, PostgreSQL, and OpenAI integration.

## Features

- 🤖 **AI Chat Assistant**: Interactive Q&A with OpenAI GPT-4
- 📚 **Course Management**: Create and manage educational courses
- 🧠 **Quiz Generation**: AI-generated quizzes from course content
- 🔍 **Semantic Search**: Vector-based document search with ChromaDB
- 👥 **Multi-tenant Architecture**: Support for multiple organizations
- 🔐 **Secure Authentication**: JWT-based authentication system
- 📊 **Real-time Analytics**: Track learning progress and engagement

## Tech Stack

- **Backend**: FastAPI, Python 3.9+
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Vector Database**: ChromaDB for semantic search
- **AI/LLM**: OpenAI GPT-4 API
- **Authentication**: JWT tokens
- **Frontend**: HTML, CSS, JavaScript (Vanilla)
- **Deployment**: Vercel (Frontend) + Railway/Render (Backend)

## Quick Start

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd tutoring-assistant
```

### 2. Set Up Environment Variables

Copy the environment template and fill in your values:

```bash
cp env.template .env
```

Edit `.env` with your actual values:

```bash
# Required: OpenAI API Key
OPENAI_API_KEY=your-openai-api-key-here

# Required: Database URL (for production)
DATABASE_URL=postgresql://username:password@host:port/database

# Required: JWT Secret (generate a secure random string)
JWT_SECRET_KEY=your-super-secret-jwt-key-here

# Optional: Other configurations
DEBUG=false
LOG_LEVEL=INFO
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Application

```bash
# Start the FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Access the Application

- **Frontend**: http://localhost:8000/frontend/index.html
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login

### Courses
- `GET /api/v1/content/courses` - List courses
- `POST /api/v1/content/courses` - Create course

### Chat
- `POST /api/v1/chat/sessions` - Create chat session
- `POST /api/v1/chat/sessions/{session_id}/messages` - Send message

### Quizzes
- `POST /api/v1/quiz/generate` - Generate quiz

## Deployment

### Frontend (Vercel)

1. Connect your GitHub repository to Vercel
2. Set build command: `echo "Static files ready"`
3. Set output directory: `frontend`
4. Deploy!

### Backend (Railway/Render)

1. Connect your GitHub repository
2. Set environment variables in the platform
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Deploy!

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `OPENAI_API_KEY` | OpenAI API key for GPT-4 | Yes | - |
| `DATABASE_URL` | PostgreSQL connection string | Yes | - |
| `JWT_SECRET_KEY` | Secret key for JWT tokens | Yes | - |
| `DEBUG` | Enable debug mode | No | `false` |
| `LOG_LEVEL` | Logging level | No | `INFO` |

## Development

### Running Tests

```bash
python -m pytest tests/
```

### Code Formatting

```bash
black .
isort .
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migration
alembic upgrade head
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For support, please open an issue in the GitHub repository.