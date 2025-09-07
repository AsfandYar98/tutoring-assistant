# 🎨 AI Tutoring Assistant Frontend

A beautiful, modern web interface for the AI Tutoring Assistant platform.

## 🌟 Features

### 🏠 Landing Page (`landing.html`)
- **Hero Section**: Eye-catching introduction with call-to-action
- **Features Showcase**: Highlight key capabilities
- **How It Works**: Step-by-step guide
- **Responsive Design**: Works on all devices

### 🔐 Authentication (`index.html`)
- **User Registration**: Create new accounts
- **Login System**: Secure authentication
- **Auto-redirect**: Seamless flow to dashboard
- **Form Validation**: Real-time input validation

### 📊 Dashboard (`dashboard.html`)
- **Modern Sidebar Navigation**: Clean, intuitive interface
- **Statistics Cards**: Real-time learning metrics
- **Course Management**: Create and manage courses
- **AI Chat Interface**: Interactive Q&A with context
- **Quiz Generator**: AI-powered quiz creation
- **Settings Panel**: Customize your experience

## 🎨 Design Features

### ✨ Visual Elements
- **Gradient Backgrounds**: Modern, professional look
- **Smooth Animations**: Hover effects and transitions
- **Icon Integration**: Font Awesome icons throughout
- **Typography**: Inter font for clean readability

### 📱 Responsive Design
- **Mobile-First**: Optimized for all screen sizes
- **Flexible Grid**: Adapts to different viewports
- **Touch-Friendly**: Large buttons and touch targets
- **Collapsible Sidebar**: Mobile navigation

### 🎯 User Experience
- **Intuitive Navigation**: Clear menu structure
- **Real-time Feedback**: Status messages and loading states
- **Error Handling**: User-friendly error messages
- **Progressive Enhancement**: Works without JavaScript

## 🚀 Getting Started

1. **Open the Landing Page**:
   ```bash
   open frontend/landing.html
   ```

2. **Start with Authentication**:
   ```bash
   open frontend/index.html
   ```

3. **Access the Dashboard**:
   ```bash
   open frontend/dashboard.html
   ```

## 🔧 Configuration

### API Endpoint
Update the API base URL in all JavaScript files:
```javascript
const API_BASE = 'http://localhost:8000';
```

### Environment Variables
The frontend automatically handles:
- Authentication tokens
- User session management
- Course and chat data

## 📁 File Structure

```
frontend/
├── landing.html          # Marketing landing page
├── index.html            # Authentication page
├── dashboard.html        # Main application dashboard
└── README.md            # This file
```

## 🎨 Customization

### Colors
The design uses a consistent color palette:
- **Primary**: `#667eea` (Blue)
- **Secondary**: `#764ba2` (Purple)
- **Success**: `#48bb78` (Green)
- **Error**: `#f56565` (Red)
- **Warning**: `#ed8936` (Orange)

### Typography
- **Font Family**: Inter (Google Fonts)
- **Weights**: 300, 400, 500, 600, 700, 800

### Components
- **Cards**: Rounded corners, subtle shadows
- **Buttons**: Gradient backgrounds, hover effects
- **Forms**: Clean inputs with focus states
- **Messages**: Color-coded status indicators

## 🔗 Integration

The frontend integrates with:
- **FastAPI Backend**: RESTful API calls
- **ChromaDB**: Vector search capabilities
- **OpenAI**: AI-powered responses
- **PostgreSQL**: Data persistence

## 📱 Browser Support

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+
- ✅ Mobile browsers

## 🚀 Performance

- **Lightweight**: Minimal dependencies
- **Fast Loading**: Optimized assets
- **Efficient**: Minimal API calls
- **Cached**: Local storage for session data

## 🎯 Future Enhancements

- [ ] Dark mode toggle
- [ ] Advanced analytics dashboard
- [ ] Real-time notifications
- [ ] File upload interface
- [ ] Voice input support
- [ ] Mobile app version

---

**Built with ❤️ for intelligent learning**
