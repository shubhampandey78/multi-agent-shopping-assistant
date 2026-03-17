# 🛒 Multi-Agent AI Shopping Assistant

## Overview
A complete AI-powered shopping assistant with 3 intelligent agents, RAG-based search, and a beautiful web interface.

## Features
- ✅ 3 Coordinated AI Agents (Preference, Recommendation, Order)
- ✅ RAG Search with ChromaDB Vector Database
- ✅ Semantic Product Search with Sentence-Transformers
- ✅ Beautiful Gradient UI with Real-time Updates
- ✅ Full Shopping Experience (Search → Add → Checkout)

## Tech Stack
- **Backend:** Python, FastAPI
- **Frontend:** HTML, JavaScript, CSS
- **AI:** Google Gemini API, Sentence-Transformers
- **Database:** ChromaDB (Vector Store)

## Installation

### 1. Clone Repository
```bash
git clone https://github.com/YOUR_USERNAME/shopping-assistant.git
cd shopping-assistant
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip3 install -r requirements.txt
```

### 4. Set Up Environment
```bash
cp .env.example .env
# Edit .env and add your Google API key from https://ai.google.dev/
```

### 5. Run Server
```bash
python3 app.py
```

Visit: http://localhost:8000

## How to Use

### Search for Products
```
User: "jewelry under $100"
→ Shows jewelry items within budget
```

### Add to Cart
```
User: "add 1"
→ Adds first product to cart
```

### Checkout
```
User: "checkout"
→ Processes order
```

## Project Structure
```
shopping-assistant/
├── agents.py           # 3 AI agents
├── app.py              # FastAPI backend
├── products.py         # Fetch products
├── embed_products.py   # Create embeddings
├── products.json       # 20 products
├── static/index.html   # Web UI
├── requirements.txt    # Dependencies
└── .env.example        # Template
```

## Team
Built by: [Your Team Names]

## License
MIT


