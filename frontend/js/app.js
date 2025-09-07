/**
 * AI Tutoring Assistant - Frontend Application
 * Main JavaScript file for enhanced user experience
 */

class TutoringApp {
    constructor() {
        this.API_BASE = 'http://localhost:8000';
        this.authToken = localStorage.getItem('authToken');
        this.currentCourseId = null;
        this.currentSessionId = null;
        this.currentQuiz = null;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.checkAuthStatus();
        this.loadInitialData();
    }

    setupEventListeners() {
        // Global keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch(e.key) {
                    case 'k':
                        e.preventDefault();
                        this.focusSearch();
                        break;
                    case 'n':
                        e.preventDefault();
                        this.createNewCourse();
                        break;
                }
            }
        });

        // Auto-save form data
        document.querySelectorAll('input, textarea, select').forEach(input => {
            input.addEventListener('input', () => {
                this.autoSaveFormData();
            });
        });
    }

    checkAuthStatus() {
        if (this.authToken) {
            this.showAuthenticatedUI();
        } else {
            this.showUnauthenticatedUI();
        }
    }

    showAuthenticatedUI() {
        // Hide login forms, show dashboard
        const authForms = document.querySelectorAll('.auth-form');
        const dashboardElements = document.querySelectorAll('.dashboard-content');
        
        authForms.forEach(form => form.style.display = 'none');
        dashboardElements.forEach(element => element.style.display = 'block');
        
        this.loadUserData();
    }

    showUnauthenticatedUI() {
        // Show login forms, hide dashboard
        const authForms = document.querySelectorAll('.auth-form');
        const dashboardElements = document.querySelectorAll('.dashboard-content');
        
        authForms.forEach(form => form.style.display = 'block');
        dashboardElements.forEach(element => element.style.display = 'none');
    }

    async loadUserData() {
        try {
            const response = await fetch(`${this.API_BASE}/api/v1/auth/me`, {
                headers: {
                    'Authorization': `Bearer ${this.authToken}`
                }
            });
            
            if (response.ok) {
                const userData = await response.json();
                this.updateUserInfo(userData);
            }
        } catch (error) {
            console.error('Error loading user data:', error);
        }
    }

    updateUserInfo(userData) {
        const userNameElement = document.getElementById('userName');
        const userEmailElement = document.getElementById('userEmail');
        const userAvatarElement = document.getElementById('userAvatar');
        
        if (userNameElement) {
            userNameElement.textContent = userData.first_name || 'User';
        }
        if (userEmailElement) {
            userEmailElement.textContent = userData.email || 'user@example.com';
        }
        if (userAvatarElement) {
            userAvatarElement.textContent = (userData.first_name || 'U').charAt(0).toUpperCase();
        }
    }

    async loadInitialData() {
        if (this.authToken) {
            await this.loadCourses();
            await this.loadRecentActivity();
            this.updateStats();
        }
    }

    async loadCourses() {
        try {
            const response = await fetch(`${this.API_BASE}/api/v1/content/courses`, {
                headers: {
                    'Authorization': `Bearer ${this.authToken}`
                }
            });

            if (response.ok) {
                const courses = await response.json();
                this.displayCourses(courses);
            }
        } catch (error) {
            console.error('Error loading courses:', error);
        }
    }

    displayCourses(courses) {
        const courseSelect = document.getElementById('courseSelect');
        const courseList = document.getElementById('courseList');
        
        if (courseSelect) {
            courseSelect.innerHTML = '<option value="">Select a course to start chatting</option>';
            courses.forEach(course => {
                const option = document.createElement('option');
                option.value = course.id;
                option.textContent = course.name;
                courseSelect.appendChild(option);
            });
        }

        if (courseList) {
            courseList.innerHTML = '';
            if (courses.length === 0) {
                courseList.innerHTML = '<p>No courses yet. Create your first course!</p>';
                return;
            }

            courses.forEach(course => {
                const courseDiv = document.createElement('div');
                courseDiv.className = 'course-card';
                courseDiv.innerHTML = `
                    <h4>${course.name}</h4>
                    <p>${course.description}</p>
                    <div class="course-actions">
                        <button class="btn btn-secondary" onclick="app.selectCourse('${course.id}')">
                            <i class="fas fa-play"></i> Start Learning
                        </button>
                        <button class="btn" onclick="app.editCourse('${course.id}')">
                            <i class="fas fa-edit"></i> Edit
                        </button>
                    </div>
                `;
                courseList.appendChild(courseDiv);
            });
        }
    }

    selectCourse(courseId) {
        const courseSelect = document.getElementById('courseSelect');
        if (courseSelect) {
            courseSelect.value = courseId;
        }
        this.showSection('chat');
    }

    async loadRecentActivity() {
        // Load recent chat sessions, quiz attempts, etc.
        try {
            const response = await fetch(`${this.API_BASE}/api/v1/chat/sessions`, {
                headers: {
                    'Authorization': `Bearer ${this.authToken}`
                }
            });

            if (response.ok) {
                const sessions = await response.json();
                this.displayRecentActivity(sessions);
            }
        } catch (error) {
            console.error('Error loading recent activity:', error);
        }
    }

    displayRecentActivity(activities) {
        const activityContainer = document.getElementById('recentActivity');
        if (!activityContainer) return;

        if (activities.length === 0) {
            activityContainer.innerHTML = '<p>No recent activity</p>';
            return;
        }

        activityContainer.innerHTML = activities.slice(0, 5).map(activity => `
            <div class="activity-item">
                <i class="fas fa-comments"></i>
                <span>Chat session in ${activity.course_name || 'Unknown Course'}</span>
                <small>${new Date(activity.created_at).toLocaleDateString()}</small>
            </div>
        `).join('');
    }

    updateStats() {
        const messages = document.querySelectorAll('.message').length;
        const courses = document.querySelectorAll('.course-card').length;
        const sessions = this.currentSessionId ? 1 : 0;
        const quizzes = this.currentQuiz ? 1 : 0;

        this.updateStatCard('totalMessages', messages);
        this.updateStatCard('totalCourses', courses);
        this.updateStatCard('totalSessions', sessions);
        this.updateStatCard('totalQuizzes', quizzes);
    }

    updateStatCard(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value;
        }
    }

    showSection(sectionId) {
        // Hide all sections
        document.querySelectorAll('.content-section').forEach(section => {
            section.classList.remove('active');
        });
        
        // Show selected section
        const targetSection = document.getElementById(sectionId);
        if (targetSection) {
            targetSection.classList.add('active');
        }
        
        // Update active nav link
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        
        const activeLink = document.querySelector(`[onclick="showSection('${sectionId}')"]`);
        if (activeLink) {
            activeLink.classList.add('active');
        }
        
        // Update page title
        const titles = {
            'dashboard': 'Dashboard',
            'courses': 'Courses',
            'chat': 'AI Chat',
            'quiz': 'Quiz Generator',
            'analytics': 'Analytics',
            'settings': 'Settings'
        };
        
        const pageTitle = document.getElementById('pageTitle');
        if (pageTitle) {
            pageTitle.textContent = titles[sectionId] || 'Dashboard';
        }
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            <span>${message}</span>
            <button onclick="this.parentElement.remove()">×</button>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }

    focusSearch() {
        const searchInput = document.querySelector('input[type="text"]');
        if (searchInput) {
            searchInput.focus();
        }
    }

    createNewCourse() {
        this.showSection('courses');
        const courseNameInput = document.getElementById('courseName');
        if (courseNameInput) {
            courseNameInput.focus();
        }
    }

    autoSaveFormData() {
        const formData = {};
        document.querySelectorAll('input, textarea, select').forEach(input => {
            if (input.id) {
                formData[input.id] = input.value;
            }
        });
        
        localStorage.setItem('formData', JSON.stringify(formData));
    }

    loadFormData() {
        const savedData = localStorage.getItem('formData');
        if (savedData) {
            const formData = JSON.parse(savedData);
            Object.entries(formData).forEach(([id, value]) => {
                const element = document.getElementById(id);
                if (element) {
                    element.value = value;
                }
            });
        }
    }

    // Utility methods
    formatDate(dateString) {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new TutoringApp();
});

// Global utility functions for backward compatibility
function showSection(sectionId) {
    if (window.app) {
        window.app.showSection(sectionId);
    }
}

function showStatus(message, type) {
    if (window.app) {
        window.app.showNotification(message, type);
    }
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TutoringApp;
}
