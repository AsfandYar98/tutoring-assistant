"""Example script demonstrating API usage."""

import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def register_user():
    """Register a new user."""
    url = f"{API_BASE}/auth/register"
    data = {
        "email": "instructor@example.com",
        "username": "instructor",
        "password": "password123",
        "first_name": "John",
        "last_name": "Doe",
        "tenant_name": "Example University"
    }
    
    response = requests.post(url, json=data)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Registration failed: {response.text}")
        return None

def login_user():
    """Login user."""
    url = f"{API_BASE}/auth/login"
    data = {
        "email": "instructor@example.com",
        "password": "password123"
    }
    
    response = requests.post(url, json=data)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Login failed: {response.text}")
        return None

def create_course(token):
    """Create a course."""
    url = f"{API_BASE}/content/courses"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "name": "Introduction to Machine Learning",
        "description": "A comprehensive course on ML fundamentals"
    }
    
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Course creation failed: {response.text}")
        return None

def create_chat_session(token, course_id):
    """Create a chat session."""
    url = f"{API_BASE}/chat/sessions"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"course_id": course_id}
    
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Chat session creation failed: {response.text}")
        return None

def send_message(token, session_id, message):
    """Send a message to chat session."""
    url = f"{API_BASE}/chat/sessions/{session_id}/messages"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"message": message}
    
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        # Handle streaming response
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line.decode('utf-8').replace('data: ', ''))
                    if 'content' in data:
                        print(data['content'], end='', flush=True)
                    elif 'done' in data:
                        print("\n--- Response Complete ---")
                        break
                except json.JSONDecodeError:
                    continue
    else:
        print(f"Message sending failed: {response.text}")

def generate_quiz(token, course_id):
    """Generate a quiz."""
    url = f"{API_BASE}/quiz/generate"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "topic": "machine learning basics",
        "difficulty": "intermediate",
        "num_questions": 3,
        "course_id": course_id
    }
    
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Quiz generation failed: {response.text}")
        return None

def main():
    """Main example flow."""
    print("Tutoring Assistant API Example")
    print("=" * 40)
    
    # Step 1: Register or login
    print("\n1. Registering user...")
    auth_data = register_user()
    if not auth_data:
        print("Registration failed, trying login...")
        auth_data = login_user()
    
    if not auth_data:
        print("Authentication failed!")
        return
    
    token = auth_data["access_token"]
    print(f"✓ Authenticated as {auth_data['user_id']}")
    
    # Step 2: Create course
    print("\n2. Creating course...")
    course = create_course(token)
    if not course:
        return
    
    course_id = course["id"]
    print(f"✓ Created course: {course['name']}")
    
    # Step 3: Create chat session
    print("\n3. Creating chat session...")
    session = create_chat_session(token, course_id)
    if not session:
        return
    
    session_id = session["id"]
    print(f"✓ Created chat session: {session['title']}")
    
    # Step 4: Send message
    print("\n4. Sending message...")
    send_message(token, session_id, "What is machine learning?")
    
    # Step 5: Generate quiz
    print("\n5. Generating quiz...")
    quiz = generate_quiz(token, course_id)
    if quiz:
        print(f"✓ Generated quiz: {quiz['title']}")
        print(f"  Questions: {len(quiz['questions'])}")
        for i, q in enumerate(quiz['questions'], 1):
            print(f"  {i}. {q['question']}")
    
    print("\n✓ Example completed successfully!")

if __name__ == "__main__":
    main()
