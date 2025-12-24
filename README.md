# Mecha-Ozzy – Multi-Provider LLM Chat Application

A modern, production-ready Flask web application that provides interactive chat with multiple Large Language Model providers, featuring advanced LaTeX math rendering, image analysis capabilities, and a beautiful dark-themed UI. Deployed with systemd service and Cloudflare tunnels for secure HTTPS access.

## 🏗️ Infrastructure Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Browser   │────│ Cloudflare      │────│   Gunicorn      │
│   (Internet)    │    │ Tunnels         │    │   (WSGI Server) │
│                 │    │ (Ports 80/443)  │    │   (Port 8080)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
       │                        │                        │
       ▼                        ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   HTTPS/HTTP    │    │   Flask App     │────│   AI Providers  │
│   (Secure)      │    │   (Python)      │    │   APIs          │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Templates     │    │ • Gemini API    │    │ Static Assets   │
│   (Jinja2)      │    │ • OpenAI API    │    │ (CSS/JS/Images) │
│ • index.html    │    │ • DeepSeek API  │    │ • style.css     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
       │                        │                        │
       ▼                        ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Systemd Service │    │ Environment     │    │ • chat.js       │
│ (Auto-start)    │    │ Variables       │    │ • images/       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## ✨ Features

- 🤖 **Multiple LLM Providers:**
  - **Gemini 2.5-flash (Google)** – Fast, reliable text generation
  - **OpenAI GPT-4o-mini** – Cost-effective, fast responses
  - **OpenAI GPT-4o** – Most capable model with higher rate limits
  - **OpenAI GPT-5-nano** – Advanced model (early access)
  - **DeepSeek** – Free high-quality model via OpenRouter

- 🖼️ **Advanced Image Analysis:**
  - Upload images with any OpenAI model (GPT-4o-mini, GPT-4o, GPT-5-nano)
  - Ask questions about images, math problems, charts, etc.
  - Base64 encoding with automatic format validation

- 📐 **Beautiful LaTeX Math Rendering:**
  - Automatic LaTeX detection and formatting for OpenAI models
  - MathJax integration for professional mathematical expressions
  - Handles complex equations, integrals, matrices, and more
  - Consistent formatting across all responses via system prompts

- 🎨 **Modern Dark UI:**
  - Beautiful dark theme with gradient accents
  - Responsive design that works on all devices
  - Real-time model switching without page refresh
  - Markdown rendering with syntax highlighting
  - Image preview with drag-and-drop upload

- 🚀 **Production Ready:**
  - Systemd service for automatic startup
  - Nginx reverse proxy configuration
  - Comprehensive error handling and logging
  - Environment-based configuration


## 📡 API Endpoints

- **`GET /`** – Main chat UI with modern dark theme
- **`GET /version`** – Health check and system status
- **`POST /api/chat`** – Main chat endpoint with AI providers

### Chat API Request Format:
```json
{
  "message": "Solve this integral: ∫ x² dx",    // Text message (required except for OpenAI with image)
  "provider": "gemini" | "openai-mini" | "openai" | "openai-5-nano" | "deepseek",  // AI provider
  "image": "data:image/png;base64,..."         // Optional: Base64 image for OpenAI vision models
}
```

### Chat API Response:
```json
{
  "reply": "$$\\int x^2 \\, dx = \\frac{x^3}{3} + C$$"  // LaTeX-formatted mathematical response
}
```

### Error Response:
```json
{
  "error": "API key not configured for selected provider"
}
```


## 🤖 Supported AI Providers & Configuration

### Environment Variables Setup:
```bash
# Required API Keys
export GEMINI_API_KEY="your-gemini-api-key"
export OPENAI_API_KEY="your-openai-api-key"
export OPENROUTER_API_KEY="your-openrouter-api-key"

# Optional Model Overrides
export OPENROUTER_DEEPSEEK_MODEL="nex-agi/deepseek-v3.1-nex-n1:free"
```

### Available Models:

| Provider | Model | Capabilities | Cost | Image Support |
|----------|-------|--------------|------|---------------|
| **Google** | Gemini 2.5 Flash | Text generation | Free tier | ❌ |
| **OpenAI** | GPT-4o-mini | Fast responses | Low | ✅ |
| **OpenAI** | GPT-4o | Most capable | Medium | ✅ |
| **OpenAI** | GPT-5-nano | Advanced | Medium-High | ✅ |
| **DeepSeek** | DeepSeek v3.1 | High quality | Free | ❌ |

### Key Features by Provider:

- **🎨 LaTeX Math Rendering**: OpenAI models with automatic LaTeX detection and MathJax rendering
- **🖼️ Image Analysis**: OpenAI vision models can analyze uploaded images
- **📝 System Prompts**: Consistent formatting across all OpenAI responses
- **🔄 Dynamic Switching**: Change models instantly without restarting the app


## 🚀 Quick Start

### Development Setup:
```bash
# 1. Clone and setup
cd /path/to/mecha-ozzy

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set API keys
export GEMINI_API_KEY="your-key-here"
export OPENAI_API_KEY="your-key-here"
export OPENROUTER_API_KEY="your-key-here"

# 4. Run development server
python app.py
# Server starts on http://localhost:8080
```

### Production Setup (Current):
- **Gunicorn Service**: Runs on port 8080 with systemd auto-start
- **Cloudflare Tunnels**: Forwards ports 80/443 to localhost:8080
- **HTTPS Access**: Available via your Cloudflare tunnel domain

### Production Deployment:

#### Systemd Service + Cloudflare Tunnels (Current Setup)
```bash
# 1. Copy service file
sudo cp mecha-ozzy.service /etc/systemd/system/

# 2. Set environment variables in systemd
sudo systemctl edit mecha-ozzy.service
# Add: [Service] section with Environment= lines for API keys

# 3. Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable mecha-ozzy
sudo systemctl start mecha-ozzy

# 4. Configure Cloudflare tunnels to forward ports 80/443 to localhost:8080
# Your tunnels should point to: http://localhost:8080
```

#### Alternative: Direct Gunicorn (Development)
```bash
# For development/testing without systemd
gunicorn --workers 4 --bind 0.0.0.0:8080 app:app
```

### Access Points:
- **Production URL**: Your Cloudflare tunnel domain (HTTPS)
- **Local Development**: http://localhost:8080/
- **Health Check**: `/version` endpoint
- **API Endpoint**: POST `/api/chat`


## 📦 Dependencies

```txt
Flask==3.0.3              # Web framework
google-generativeai>=0.7.2 # Gemini API
openai>=2.14.0           # OpenAI API (GPT-4o, GPT-5-nano)
requests==2.32.5         # HTTP client for OpenRouter
gunicorn==23.0.0         # WSGI server for production
```

Install: `pip install -r requirements.txt`

## 💡 Usage Examples

### Text Chat:
```bash
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Explain quantum computing", "provider": "openai"}'
```

### Image Analysis:
```bash
# Upload an image and ask about it
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What mathematical concepts are shown here?",
    "provider": "openai",
    "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..."
  }'
```

### Web Interface Features:
- **Model Switching**: Change AI providers instantly via dropdown
- **Math Rendering**: Automatic LaTeX → beautiful equations
- **Image Upload**: Drag & drop images for OpenAI models
- **Responsive Design**: Works on desktop, tablet, and mobile

### Advanced Features:
- **System Prompts**: Consistent formatting across OpenAI models
- **Error Handling**: Graceful fallbacks and user feedback
- **Rate Limiting**: Built-in handling of API limits
- **Logging**: Comprehensive request/response logging

## 🔗 Useful Links

- [OpenAI API](https://platform.openai.com/) - GPT-4o and GPT-5-nano
- [Google Gemini](https://ai.google.dev/) - Gemini API
- [OpenRouter](https://openrouter.ai/) - DeepSeek and other models
- [Cloudflare Tunnels](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/) - Secure tunneling
- [MathJax](https://www.mathjax.org/) - LaTeX rendering engine
- [Flask](https://flask.palletsprojects.com/) - Web framework
- [Gunicorn](https://gunicorn.org/) - WSGI server

## 🛠️ Technical Architecture

### Frontend Stack:
- **HTML5** with Jinja2 templating
- **CSS3** with modern dark theme and animations
- **Vanilla JavaScript** with async/await for API calls
- **MathJax 3** for LaTeX rendering
- **Responsive design** with mobile-first approach

### Backend Stack:
- **Flask** web framework with REST API
- **Gunicorn** WSGI server for production
- **Systemd** service management for auto-startup
- **Cloudflare Tunnels** for secure HTTPS access (ports 80/443 → 8080)
- **Environment-based configuration**

### AI Integration:
- **OpenAI SDK** for GPT models with vision capabilities
- **Google Generative AI SDK** for Gemini
- **OpenRouter API** for DeepSeek
- **System prompts** for consistent response formatting
- **Automatic LaTeX detection** and MathJax rendering

### Security & Performance:
- **API key management** via environment variables
- **Input validation** and sanitization
- **Error handling** with graceful degradation
- **Rate limiting awareness** and retry logic
- **Logging** for monitoring and debugging

## 🏆 Key Improvements Over Original

- ✅ **5 AI Models** (vs 4) with GPT-5-nano support
- ✅ **Universal Image Support** (all OpenAI models, not just Amazon Nova)
- ✅ **Advanced LaTeX Processing** with automatic detection and rendering
- ✅ **System Prompts** for consistent formatting across all models
- ✅ **Production Deployment** with systemd service and Cloudflare tunnels
- ✅ **Modern UI** with dark theme and responsive design
- ✅ **Robust Error Handling** and comprehensive logging
- ✅ **Secure HTTPS Access** via Cloudflare tunnels (ports 80/443)
- ✅ **Infrastructure Diagram** showing complete architecture
- ✅ **Multi-environment Support** (development + production)
