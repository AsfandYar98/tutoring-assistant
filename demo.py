#!/usr/bin/env python3
"""
Demo script for the Tutoring Assistant API
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def print_section(title):
    """Print a section header."""
    print(f"\n{'='*50}")
    print(f" {title}")
    print('='*50)

def demo_authentication():
    """Demo user registration and login."""
    print_section("AUTHENTICATION DEMO")
    
    # Register a new user
    print("1. Registering a new user...")
    register_data = {
        "email": "demo@example.com",
        "username": "demo_user",
        "password": "password123",
        "first_name": "Demo",
        "last_name": "User",
        "tenant_name": "Demo University"
    }
    
    response = requests.post(f"{API_BASE}/auth/register", json=register_data)
    if response.status_code == 200:
        auth_data = response.json()
        print(f"✓ User registered successfully!")
        print(f"  User ID: {auth_data['user_id']}")
        print(f"  Tenant ID: {auth_data['tenant_id']}")
        return auth_data['access_token']
    else:
        print(f"✗ Registration failed: {response.text}")
        return None

def demo_course_management(token):
    """Demo course creation and management."""
    print_section("COURSE MANAGEMENT DEMO")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a course
    print("1. Creating a course...")
    course_data = {
        "name": "Introduction to Artificial Intelligence",
        "description": "A comprehensive course covering AI fundamentals, machine learning, and neural networks."
    }
    
    response = requests.post(f"{API_BASE}/content/courses", json=course_data, headers=headers)
    if response.status_code == 200:
        course = response.json()
        print(f"✓ Course created successfully!")
        print(f"  Course ID: {course['id']}")
        print(f"  Name: {course['name']}")
        return course['id']
    else:
        print(f"✗ Course creation failed: {response.text}")
        return None

def demo_chat_session(token, course_id):
    """Demo chat session creation and messaging."""
    print_section("CHAT SESSION DEMO")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a chat session
    print("1. Creating a chat session...")
    response = requests.post(f"{API_BASE}/chat/sessions?course_id={course_id}", 
                           json={"title": "AI Questions Session"}, 
                           headers=headers)
    
    if response.status_code == 200:
        session = response.json()
        print(f"✓ Chat session created!")
        print(f"  Session ID: {session['id']}")
        session_id = session['id']
    else:
        print(f"✗ Chat session creation failed: {response.text}")
        return
    
    # Send a message
    print("\n2. Sending a message...")
    message_data = {
        "message": "What is artificial intelligence?",
        "course_id": course_id
    }
    
    print("Sending: 'What is artificial intelligence?'")
    print("Response:")
    
    response = requests.post(f"{API_BASE}/chat/sessions/{session_id}/messages", 
                           json=message_data, 
                           headers=headers,
                           stream=True)
    
    if response.status_code == 200:
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line.decode('utf-8').replace('data: ', ''))
                    if 'content' in data:
                        print(data['content'], end='', flush=True)
                    elif 'done' in data:
                        print("\n")
                        break
                except json.JSONDecodeError:
                    continue
    else:
        print(f"✗ Message sending failed: {response.text}")

def demo_quiz_generation(token, course_id):
    """Demo quiz generation."""
    print_section("QUIZ GENERATION DEMO")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Generate a quiz
    print("1. Generating a quiz...")
    quiz_data = {
        "topic": "machine learning basics",
        "difficulty": "intermediate",
        "num_questions": 3,
        "course_id": course_id
    }
    
    response = requests.post(f"{API_BASE}/quiz/generate", json=quiz_data, headers=headers)
    if response.status_code == 200:
        quiz = response.json()
        print(f"✓ Quiz generated successfully!")
        print(f"  Quiz ID: {quiz['id']}")
        print(f"  Title: {quiz['title']}")
        print(f"  Difficulty: {quiz['difficulty']}")
        print(f"  Number of questions: {len(quiz['questions'])}")
        
        # Show first question
        if quiz['questions']:
            print(f"\n  Sample question:")
            print(f"    {quiz['questions'][0]['question']}")
            print(f"    Options: {quiz['questions'][0]['options']}")
        
        return quiz['id']
    else:
        print(f"✗ Quiz generation failed: {response.text}")
        return None

def demo_api_status():
    """Demo API status and health check."""
    print_section("API STATUS DEMO")
    
    # Health check
    print("1. Checking API health...")
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        health = response.json()
        print(f"✓ API is healthy!")
        print(f"  Status: {health['status']}")
        print(f"  Version: {health['version']}")
    else:
        print(f"✗ Health check failed: {response.status_code}")
    
    # Root endpoint
    print("\n2. Checking root endpoint...")
    response = requests.get(f"{BASE_URL}/")
    if response.status_code == 200:
        root = response.json()
        print(f"✓ Root endpoint working!")
        print(f"  Message: {root['message']}")
        print(f"  Version: {root['version']}")
    else:
        print(f"✗ Root endpoint failed: {response.status_code}")

def main():
    """Main demo function."""
    print("🎓 Tutoring Assistant API Demo")
    print("This demo will show you how to use the API endpoints.")
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ Server is not responding properly. Status: {response.status_code}")
            return
    except requests.exceptions.RequestException:
        print("❌ Server is not running. Please start it with:")
        print("   python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        return
    
    # Run demos
    demo_api_status()
    
    token = demo_authentication()
    if not token:
        print("❌ Authentication failed. Cannot continue with demo.")
        return
    
    course_id = demo_course_management(token)
    if not course_id:
        print("❌ Course management failed. Cannot continue with demo.")
        return
    
    demo_chat_session(token, course_id)
    demo_quiz_generation(token, course_id)
    
    print_section("DEMO COMPLETE")
    print("🎉 All demos completed successfully!")
    print("\nNext steps:")
    print("1. Configure your OpenAI API key in the environment variables")
    print("2. Upload documents to your course")
    print("3. Try the web frontend at frontend/index.html")
    print("4. Explore the API documentation")

if __name__ == "__main__":
    main()
