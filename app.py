from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from agents import ShoppingAssistant

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Multi-Agent Shopping Assistant")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize shopping assistant
assistant = ShoppingAssistant()

# ============================================================================
# SERVE HTML UI AT ROOT
# ============================================================================

@app.get("/", include_in_schema=False)
async def serve_ui():
    """Serve the main HTML UI"""
    html_path = os.path.join("static", "index.html")
    
    if os.path.exists(html_path):
        with open(html_path, 'r') as f:
            return HTMLResponse(content=f.read())
    else:
        return HTMLResponse(content="<h1>❌ Error: static/index.html not found</h1><p>Make sure the file exists in the static folder</p>")

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class MessageRequest(BaseModel):
    message: str

class MessageResponse(BaseModel):
    response: str
    cart_total: float
    cart_items: int

class CartResponse(BaseModel):
    items: list
    total: float
    item_count: int

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/api/status")
def api_status():
    """API status"""
    return {"status": "✅ Running", "service": "Multi-Agent Shopping Assistant"}

@app.post("/chat", response_model=MessageResponse)
def chat_with_assistant(request: MessageRequest):
    """Send message to assistant"""
    try:
        user_message = request.message.strip()
        
        if not user_message:
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Process through agents
        response = assistant.process_message(user_message)
        
        # Get cart status
        cart_total = sum(
            float(item['price']) * item['quantity'] 
            for item in assistant.order_agent.cart
        )
        cart_items = len(assistant.order_agent.cart)
        
        return MessageResponse(
            response=response,
            cart_total=cart_total,
            cart_items=cart_items
        )
    
    except Exception as e:
        print(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cart", response_model=CartResponse)
def get_cart():
    """Get shopping cart"""
    try:
        cart_total = sum(
            float(item['price']) * item['quantity'] 
            for item in assistant.order_agent.cart
        )
        
        return CartResponse(
            items=assistant.order_agent.cart,
            total=cart_total,
            item_count=len(assistant.order_agent.cart)
        )
    
    except Exception as e:
        print(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/cart/clear")
def clear_cart():
    """Clear cart"""
    try:
        assistant.order_agent.cart = []
        return {"message": "✅ Cart cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/orders")
def get_orders():
    """Get order history"""
    try:
        return {
            "orders": assistant.order_agent.order_history,
            "total_orders": len(assistant.order_agent.order_history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/preferences")
def get_preferences():
    """Get user preferences"""
    try:
        return {"preferences": assistant.preference_agent.user_preferences}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reset")
def reset_session():
    """Reset conversation"""
    try:
        assistant.preference_agent.conversation_history = []
        assistant.preference_agent.user_preferences = {
            'budget': None,
            'category': None,
            'style': None,
            'needs': []
        }
        assistant.order_agent.cart = []
        assistant.conversation_history = []
        
        return {"message": "✅ Session reset"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    """Health check"""
    return {
        "status": "healthy",
        "service": "Multi-Agent Shopping Assistant"
    }

# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*70)
    print("🚀 MULTI-AGENT SHOPPING ASSISTANT")
    print("="*70)
    print("\n📡 Server starting...")
    print("🌐 Open browser: http://localhost:8000")
    print("📖 API docs: http://localhost:8000/docs")
    print("\n⏳ Press Ctrl+C to stop\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )