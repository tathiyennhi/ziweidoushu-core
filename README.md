# Zi Wei Dou Shu Core

This is the core for future Zi Wei Dou Shu (紫微斗数) astrology computation built with **FastAPI** and **Uvicorn**.  

---

## Setup & Run

### 1. Clone and enter the project
```bash
git clone https://github.com/tathiyennhi/ziweidoushu-core.git
cd ziweidoushu-core
```
### 2. Create and activate a virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```
### 3. Install dependencies
```bash
pip install -U pip
pip install -e .
``` 
### 3. Run the API server
```bash
uvicorn ziweidoushu_core.app.main:app --reload --port 8000
``` 
#### API docs available at:
#### 👉 http://127.0.0.1:8000/docs