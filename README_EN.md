# AutoDiagenti AI v2.0

> AI-powered tool for automatically analyzing and visualizing API flows in Java Spring projects

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.43.0-red.svg)](https://streamlit.io)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.11-green.svg)](https://fastapi.tiangolo.com)
[![LangChain](https://img.shields.io/badge/LangChain-0.3.19-yellow.svg)](https://langchain.com)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

## 🌐 Language Selection

- [한국어](README.md)
- **English** (current page)

---

## 📋 Table of Contents

- [Project Overview](#-project-overview)
- [Key Features](#-key-features)
- [Target Users](#-target-users)
- [Installation & Setup](#️-installation--setup)
- [Usage](#-usage)
- [API Documentation](#-api-documentation)
- [Architecture](#️-architecture)
- [Development Guide](#️-development-guide)
- [Contributing](#-contributing)
- [License](#-license)
- [Support](#-support)

## 🚀 Project Overview

**AutoDiagenti AI** is a tool that automatically analyzes complex API call flows in Java Spring Framework-based projects using AI and provides developers with intuitive visualization and explanations.

### ✨ Key Features

- **🔍 Automatic API Detection**: Automatic extraction of entry points based on Spring annotations
- **🌳 Call Flow Analysis**: Recursive analysis of method call relationships
- **🖥️ AI-based Interpretation**: Code flow interpretation and summarization using LLM
- **📊 Visualization**: Intuitive representation with Mermaid sequence diagrams
- **📋 History Management**: Analysis result storage and retrieval functionality

### 🎯 Target Users

- **Java Spring Developers**: Developers who want to understand and document complex API flows
- **System Architects**: Architects who want to understand and optimize overall system structure
- **Junior Developers**: Developers who want to quickly learn code flows of existing projects
- **QA Engineers**: QA engineers who need flow analysis for API test case creation

## 🛠️ Installation & Setup

### 1. System Requirements

- **Python**: 3.8 or higher
- **Java**: 21 or higher (for Java code parsing)
- **Memory**: Minimum 4GB RAM recommended
- **Disk**: Minimum 2GB free space

### 2. Clone Repository

```bash
git clone https://github.com/your-username/autodiagenti-ai.git
cd autodiagenti-ai
```

### 3. Virtual Environment Setup

#### 3.1 Create Virtual Environment

```bash
# Create virtual environment
python -m venv .venv
```

#### 3.2 Activate Virtual Environment

**PowerShell (Windows)**
```powershell
# Change execution policy (first time only)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

# Activate virtual environment
.\.venv\Scripts\Activate.ps1
```

**Git Bash (Windows)**
```bash
# Activate virtual environment
source .venv/Scripts/activate
```

**macOS/Linux**
```bash
# Activate virtual environment
source .venv/bin/activate
```

### 4. Install Dependencies

```bash
# Install basic dependencies
pip install -r requirements.txt
```

### 5. Environment Variables Setup

The project uses two `.env` files:

#### 5.1 Server .env file (`server/.env`)

```bash
# Create .env file in server directory
touch server/.env
```

```env
# Azure OpenAI API settings (required)
AOAI_API_KEY=your_azure_openai_api_key_here
AOAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AOAI_DEPLOY_GPT=your-gpt-deployment-name
AOAI_EMBEDDING_DEPLOYMENT=your-embedding-deployment-name
AOAI_API_VERSION=2024-10-21

```

#### 5.2 Client .env file (`app/.env`)

```bash
# Create .env file in app directory
touch app/.env
```

```env
# API server URL settings (required)
AUTODIAGENTI_API_BASE_URL=http://localhost:8002/api/v1/autodiagenti
```

### 6. Server Execution

#### Method 1: Integrated Execution (Development)
```bash
# Run FastAPI server and Streamlit UI simultaneously
python run_app.py
```

#### Method 2: Individual Execution (Recommended)
```bash
# Run FastAPI server (Terminal 1)
uvicorn server.main:app --reload --port=8002

# Run Streamlit app (Terminal 2)
streamlit run app/main.py --server.port 8501
```

### 7. Access Verification

- **Streamlit UI**: http://localhost:8501
- **FastAPI API**: http://localhost:8002
- **API Documentation**: http://localhost:8002/docs

## ⚡ Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Application
```bash
python run_app.py
```

### 3. Test with Sample Data
1. Open browser and go to `http://localhost:8501`
2. **Download sample file**: Download `data/sample_project-master.zip` file
3. Click "프로젝트 업로드" button
4. Upload the downloaded `sample_project-master.zip` file
5. Click "분석 시작" to test the complete workflow

### 4. Sample Project Structure
The sample project includes:
- Spring Boot application with `@RestController` and `@Service` annotations
- Multiple service layers with method calls
- Database repository patterns
- Perfect structure for testing the analysis workflow

## 📖 Usage

### 1. Basic Usage

#### 1.1 Project Upload
1. Access Streamlit UI
2. Select ZIP file in "프로젝트 업로드" section
3. Compress Java Spring project into ZIP and upload

#### 1.2 Analysis Configuration
1. **Analysis Options Settings**:
   - **Include Method Body**: Checkbox to select whether to include method internal code analysis
   - **Custom Annotations**: Input annotations for entry point identification (e.g., `RestController,RequestMapping,PostMapping`)
   - **Exclude Package Prefixes**: Input packages to exclude from analysis (e.g., `com.example.test,org.junit`)

2. **LLM Model Selection**:
   - Select Azure OpenAI model using radio buttons
   - Model version is automatically set

#### 1.3 Analysis Execution
1. Click "분석 시작" button
2. Check real-time progress
3. Check results after analysis completion

### 2. Usage Examples

#### 2.1 Spring Boot REST API Analysis

```java
// Example: UserController.java
@RestController
@RequestMapping("/api/users")
public class UserController {
    
    @Autowired
    private UserService userService;
    
    @GetMapping
    public ResponseEntity<List<User>> getUsers() {
        List<User> users = userService.findAllUsers();
        return ResponseEntity.ok(users);
    }
    
    @PostMapping
    public ResponseEntity<User> createUser(@RequestBody User user) {
        User savedUser = userService.saveUser(user);
        return ResponseEntity.ok(savedUser);
    }
}
```

**Analysis Results:**
- **API Entry Points**: `/api/users` (GET, POST)
- **Call Flow**: Controller → Service → Repository
- **Sequence Diagram**: Automatically generated Mermaid diagram
- **AI Interpretation**: Business logic analysis and summarization

#### 2.2 Complex Business Logic Analysis

```java
// Example: OrderController.java
@RestController
@RequestMapping("/api/orders")
public class OrderController {
    
    @PostMapping
    public ResponseEntity<Order> createOrder(@RequestBody OrderRequest request) {
        // 1. Order validation
        validationService.validateOrder(request);
        
        // 2. Stock check
        inventoryService.checkStock(request.getItems());
        
        // 3. Order creation
        Order order = orderService.createOrder(request);
        
        // 4. Payment processing
        paymentService.processPayment(order);
        
        // 5. Email sending
        emailService.sendOrderConfirmation(order);
        
        return ResponseEntity.ok(order);
    }
}
```

**Analysis Results:**
- **Complex Call Chain**: 5-step business process
- **Dependency Analysis**: Dependencies between each service
- **Error Handling**: Exception handling flows
- **Performance Optimization**: Bottleneck identification

## 📚 API Documentation

### Actually Used API List

#### File Upload API
- **POST** `/api/v1/autodiagenti/file/upload`
- **Purpose**: Java Spring project ZIP file upload
- **Request**: multipart/form-data (file)
- **Response**: session_id, project_id, project_name, analyzed_date, file_info

#### Analysis Related APIs
- **POST** `/api/v1/autodiagenti/analyze/run-analysis`
- **Purpose**: Project analysis execution
- **Request**: session_id, project_id, project_name, analyzed_date, file_info, filter_options

- **POST** `/api/v1/autodiagenti/analyze/status`
- **Purpose**: Analysis progress status check
- **Request**: project_id

- **POST** `/api/v1/autodiagenti/analyze/result`
- **Purpose**: Analysis result retrieval (sequence diagram, LLM summary included)
- **Request**: analyzed_date, project_id, entry_point

#### Entry Point API
- **POST** `/api/v1/autodiagenti/entry-point/get-entry-point-list`
- **Purpose**: Project entry point list retrieval
- **Request**: project_id

#### History API
- **POST** `/api/v1/autodiagenti/history/recent-analysis-projects`
- **Purpose**: Recent analysis project list retrieval
- **Request**: limit (optional, default: 3)

- **POST** `/api/v1/autodiagenti/history/search-analysis-projects`
- **Purpose**: Analysis project search by keyword
- **Request**: keyword, limit (optional, default: 3)

- **POST** `/api/v1/autodiagenti/history/delete-project`
- **Purpose**: Analysis project deletion
- **Request**: analyzed_date, project_id

### Basic Information

- **Base URL**: `http://localhost:8002`
- **API Version**: v1
- **Content-Type**: `application/json`
- **Response Format**: JSON

### Main Endpoints

#### 1. File Upload

```http
POST /api/v1/autodiagenti/file/upload
Content-Type: multipart/form-data

Parameters:
- file: ZIP file (multipart/form-data)

Response:
{
  "success": true,
  "message": "",
  "result": {
    "session_id": "uuid-string",
    "project_id": "sample_project_20250914",
    "project_name": "sample_project",
    "file_info": {
      "file_name": "sample_project_20250914.zip",
      "file_path": "server/storage/tmp/unpacked",
      "orig_file_name": "sample_project"
    },
    "analyzed_date": "20250914"
  }
}
```

#### 2. Analysis Execution

```http
POST /api/v1/autodiagenti/analyze/run-analysis
Content-Type: application/json

Request Body:
{
  "session_id": "uuid-string",
  "project_id": "sample_project_20250914",
  "project_name": "sample_project",
  "analyzed_date": "20250914",
  "file_info": {
    "file_name": "sample_project_20250914.zip",
    "file_path": "server/storage/tmp/unpacked",
    "orig_file_name": "sample_project"
  },
  "filter_options": {
    "include_method_text": true,
    "exclude_packages": "com.example.test",
    "custom_annotations": "@RestController",
    "llm_model": "your-gpt-deployment-name",
    "llm_version": "2024-10-21"
  }
}

Response:
{
  "success": true,
  "message": "",
  "result": {
    "message": "Analysis started: sample_project_20250914"
  }
}
```

#### 3. Analysis Status Check

```http
POST /api/v1/autodiagenti/analyze/status
Content-Type: application/json

Request Body:
{
  "project_id": "sample_project_20250914"
}

Response:
{
  "success": true,
  "message": "",
  "result": {
    "status": "done",
    "step": 13,
    "total_steps": 13,
    "updated_at": "2025-09-14T17:07:44.578665",
    "message": "🟢 Complete"
  }
}
```

#### 4. Analysis Result Retrieval

```http
POST /api/v1/autodiagenti/analyze/result
Content-Type: application/json

Request Body:
{
  "analyzed_date": "20250914",
  "project_id": "sample_project_20250914",
  "entry_point": "/api/users"
}

Response:
{
  "success": true,
  "message": "",
  "result": {
    "entry_point": "/api/users",
    "llm_model": "your-gpt-deployment-name",
    "llm_version": "2024-10-21",
    "llm_temperature": 0.7,
    "mermaid_code": "sequenceDiagram\n    participant Client\n    participant Controller\n    participant Service\n    participant Repository\n    \n    Client->>Controller: GET /api/users\n    Controller->>Service: findAllUsers()\n    Service->>Repository: findAll()\n    Repository-->>Service: List<User>\n    Service-->>Controller: List<User>\n    Controller-->>Client: JSON Response",
    "summary_title": "User List Retrieval API",
    "insight": "User management system following RESTful API pattern",
    "reasoning": "Implemented with Controller-Service-Repository layered architecture",
    "method_definitions": {...},
    "analyzed_at": "2025-09-14T17:07:44.578665"
  }
}
```

#### 5. Entry Point List Retrieval

```http
POST /api/v1/autodiagenti/entry-point/get-entry-point-list
Content-Type: application/json

Request Body:
{
  "project_id": "sample_project_20250914"
}

Response:
{
  "success": true,
  "message": "",
  "result": {
    "GET_/api/users": {
      "analyzed_date": "20250914",
      "project_id": "sample_project_20250914",
      "session_id": "uuid-string",
      "entry_point": "/api/users",
      "api_name": "/api/users",
      "api_method": "GET",
      "annotation": "@GetMapping(\"/api/users\")",
      "analyze_at": "2025-09-14T17:07:44.578665"
    },
    "POST_/api/users": {
      "analyzed_date": "20250914",
      "project_id": "sample_project_20250914",
      "session_id": "uuid-string",
      "entry_point": "/api/users",
      "api_name": "/api/users",
      "api_method": "POST",
      "annotation": "@PostMapping(\"/api/users\")",
      "analyze_at": "2025-09-14T17:07:44.578665"
    }
  }
}
```

### Error Response

All APIs use a consistent error response format:

```json
{
  "success": false,
  "message": "Detailed error message",
  "result": null
}
```

### Status Codes

- **200 OK**: Request successful
- **400 Bad Request**: Invalid request
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Internal server error

## 🏗️ Architecture

### System Configuration

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   AI Agents     │
│   (Streamlit)   │◄──►│   (FastAPI)     │◄──►│   (LangGraph)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Database      │
                       │   (SQLite)      │
                       └─────────────────┘
```

### Technology Stack

#### Frontend
- **Streamlit**: Web UI framework
- **Mermaid**: Diagram rendering

#### Backend
- **FastAPI**: REST API server
- **SQLAlchemy**: ORM
- **SQLite**: Database
- **FAISS**: Vector search

#### AI/ML
- **LangChain**: AI framework
- **LangGraph**: AI workflow management
- **Azure OpenAI GPT**: Code analysis and summarization

#### Java Analysis
- **Custom Java Parser**: JAR file-based analysis

## 🛠️ Development Guide

### Project Structure

```
autodiagenti-ai/
├── app/                    # Streamlit frontend
├── server/                 # FastAPI backend
│   ├── workflow/agents/    # AI agents
│   ├── routers/            # API routers
│   ├── db/                 # Database models
│   └── storage/            # File storage
└── tests/                  # Test code
```

### Development Environment Setup

#### 1. Development Tools Installation and Execution

```bash
# Install development dependencies
pip install -r requirements.txt
pip install pytest pytest-cov mutpy

# Run tests
pytest

# Measure test coverage
pytest --cov=app --cov=server --cov-report=html
```

### Code Style

- **Type Hints**: Apply type hints to all functions
- **Docstring**: Documentation strings for major functions

### Git Commit Messages

```
feat: new feature
fix: bug fix
docs: documentation changes
style: code formatting
refactor: refactoring
test: add tests
chore: build/setting changes
```

### Test Writing

```python
# PITEST optimization test example
def test_sanitize_name_special_chars():
    """Test that all special characters are removed"""
    assert sanitize_name("file<>|*?:\\/\"") == "file"
    assert sanitize_name("test{value}") == "test-value-"
```

## 🤝 Contributing

### 1. Fork and Clone

```bash
# Fork repository and clone
git clone https://github.com/your-username/autodiagenti-ai.git
cd autodiagenti-ai

# Add original repository
git remote add upstream https://github.com/original-username/autodiagenti-ai.git
```

### 2. Create Branch

```bash
# Create feature branch
git checkout -b feature/amazing-feature

# Create bug fix branch
git checkout -b fix/bug-description
```

### 3. Development and Testing

```bash
# Write code
# ...

# Run tests
pytest

# Commit
git add .
git commit -m "feat: add amazing feature"
```

### 4. Create Pull Request

1. Create Pull Request on GitHub
2. Write description of changes
3. Link related issues
4. Assign reviewers

### Contribution Guidelines

- **Code Quality**: Write PITEST tests, use type hints
- **Documentation**: Write documentation for new features
- **Testing**: Write test cases for new features
- **Issues**: Provide detailed descriptions for bug reports or feature requests

### Issue Reporting

Found a bug? Please create an issue with the following information:

- **Environment Info**: OS, Python version, browser
- **Reproduction Steps**: Step-by-step description to reproduce the problem
- **Expected Result**: Expected result
- **Actual Result**: Actual result that occurred
- **Logs**: Related error logs or screenshots

## 📄 License

This project is distributed under the MIT License. See the [LICENSE](LICENSE) file for details.

### MIT License Summary

- ✅ **Commercial use** allowed
- ✅ **Modification** allowed
- ✅ **Distribution** allowed
- ✅ **Private use** allowed
- ❌ **No warranty**
- ❌ **No liability**

### Open Source Library Licenses Used

This project uses the following open source libraries:

| Library | License | Compatibility | Purpose |
|---------|---------|---------------|---------|
| FastAPI | MIT | ✅ | REST API server |
| Streamlit | Apache 2.0 | ✅ | Web UI framework |
| LangChain | Apache 2.0 | ✅ | AI framework |
| SQLAlchemy | MIT | ✅ | ORM |
| Azure OpenAI | MIT | ✅ | LLM API |
| FAISS | MIT | ✅ | Vector search |
| JavaParser | Apache 2.0 | ✅ | Java code parsing |

**All used libraries are compatible with the MIT License.**

#### JavaParser License Notice
This project uses the [JavaParser](https://github.com/javaparser/javaparser) library for Java code analysis.
- **License**: Apache License 2.0
- **Copyright**: Copyright (c) 2015-2023 JavaParser contributors
- **License URL**: http://www.apache.org/licenses/LICENSE-2.0
- **Purpose**: Java source code AST (Abstract Syntax Tree) generation and analysis

For detailed license information, see the [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md) file.

## 🆘 Support

### Documentation

- **README**: This file
- **API Documentation**: http://localhost:8002/docs

### Community

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and discussions
- **Wiki**: Additional documentation and guides

### Contact

- **Project Manager**: [GitHub Profile](https://github.com/sg-dev-co)
- **Email**: dev.sg.comp@gmail.com, krsoogom@sk.com

### Frequently Asked Questions (FAQ)

#### Q: What Java version is supported?
A: Java 21 or higher is supported.

#### Q: Can large projects be analyzed?
A: Yes, it's possible. However, memory usage may be high, so ensure sufficient RAM.

#### Q: Are other frameworks supported?
A: Currently only Spring Framework is supported. Support for other frameworks is planned for the future.

#### Q: Can it be used offline?
A: Yes, it's possible. However, internet connection is required to use Azure OpenAI LLM features.

#### Q: Can other LLMs be used instead of Azure OpenAI?
A: Currently only Azure OpenAI is supported. Support for other LLM providers is planned for the future.

---

**AutoDiagenti AI** - Java Spring Project Analysis Tool 🚀

*Made by dev.sg.comp@gmail.com, krsoogom@sk.com*
