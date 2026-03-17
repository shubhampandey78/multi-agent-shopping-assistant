import os
import json
import chromadb
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Google Gemini
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

# Initialize ChromaDB client
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_collection(name="products")

# ============================================================================
# AGENT 1: PREFERENCE AGENT
# ============================================================================

class PreferenceAgent:
    """Extracts user preferences from messages"""
    
    def __init__(self):
        self.user_preferences = {
            'budget': None,
            'category': None,
            'needs': []
        }
    
    def extract(self, user_message):
        """Extract preferences from user message"""
        user_lower = user_message.lower()
        
        # Reset preferences for each query
        self.user_preferences = {
            'budget': None,
            'category': None,
            'needs': []
        }
        
        # Budget extraction
        if '$' in user_message or 'under' in user_lower:
            import re
            prices = re.findall(r'(\d+)', user_message)
            if prices:
                self.user_preferences['budget'] = int(prices[-1])  # Take the last number
        
        # Category extraction - use EXACT category names from dataset
        # Dataset has: "jewelery" (not jewelry), "men's clothing", "women's clothing", "electronics"
        categories_map = {
            'electronics': ['electronics', 'phone', 'smartphone', 'monitor', 'ssd', 'hard drive', 'display', 'drive', 'storage'],
            'jewelery': ['jewelry', 'jewelery', 'jewellery', 'bracelet', 'ring', 'earring', 'necklace', 'ornament', 'gold'],
            "men's clothing": ['men', "men's", 'mens', 'jacket', 'shirt', 'backpack', 'tshirt', 't-shirt'],
            "women's clothing": ['women', "women's", 'womens', 'coat', 'dress', 'raincoat', 'snowboard']
        }
        
        for category, keywords in categories_map.items():
            for keyword in keywords:
                if keyword in user_lower:
                    self.user_preferences['category'] = category
                    break
            if self.user_preferences['category']:
                break
        
        # Needs extraction - more comprehensive
        needs_keywords = [
            'backpack', 'bag', 'laptop', 'comfortable', 'affordable', 'cheap', 
            'shirt', 'jacket', 'phone', 'smartphone', 'watch', 'monitor', 'display',
            'ring', 'bracelet', 'earring', 'necklace', 'dress', 'coat', 'pants',
            'ssd', 'drive', 'storage', 'gaming', 'slim', 'casual', 'premium', 'gold',
            'ornament', 'raincoat', 'snowboard', 'tshirt', 't-shirt'
        ]
        for keyword in needs_keywords:
            if keyword in user_lower and keyword not in self.user_preferences['needs']:
                self.user_preferences['needs'].append(keyword)
        
        return self.user_preferences

# ============================================================================
# AGENT 2: RECOMMENDATION AGENT
# ============================================================================

class RecommendationAgent:
    """RAG-based product recommendation using ChromaDB"""
    
    def recommend(self, user_preferences, user_message, limit=5):
        """Search ChromaDB for matching products"""
        
        # Build search query
        query = user_message
        if user_preferences['budget']:
            query += f" under ${user_preferences['budget']}"
        if user_preferences['needs']:
            query += " " + " ".join(user_preferences['needs'])
        if user_preferences['category']:
            query += f" {user_preferences['category']}"
        
        # Search ChromaDB
        results = collection.query(
            query_texts=[query],
            n_results=20
        )
        
        # Filter and format results
        recommendations = []
        if results['ids'] and len(results['ids']) > 0:
            for product_id, metadata, distance in zip(
                results['ids'][0],
                results['metadatas'][0],
                results['distances'][0]
            ):
                relevance = (1 - distance) * 100
                
                # RELAXED Quality filter
                if relevance < 25:  # Further relaxed to 25
                    continue
                
                # Budget filter (STRICT)
                if user_preferences['budget']:
                    price = float(metadata['price'])
                    if price > user_preferences['budget']:
                        continue
                
                # Get product info
                product_title = metadata['title'].lower()
                product_category = metadata['category'].lower()
                product_description = metadata.get('description', '').lower()
                combined_text = f"{product_title} {product_category} {product_description}"
                
                # If user specified category, MUST match exactly
                if user_preferences['category']:
                    user_category = user_preferences['category'].lower()
                    
                    # Exact category match
                    if user_category not in product_category:
                        # Try keyword match
                        category_words = user_category.split()
                        category_match = False
                        for word in category_words:
                            if word in product_category:
                                category_match = True
                                break
                        if not category_match:
                            continue
                
                # Check for needs/keyword matches
                if user_preferences['needs']:
                    needs_match = False
                    for need in user_preferences['needs']:
                        if need.lower() in combined_text:
                            needs_match = True
                            break
                    # If no needs match, still include (soft filter)
                
                recommendations.append({
                    'id': product_id,
                    'title': metadata['title'],
                    'price': metadata['price'],
                    'category': metadata['category'],
                    'image': metadata['image'],
                    'rating': metadata['rating'],
                    'relevance': round(relevance, 1)
                })
                
                if len(recommendations) >= limit:
                    break
        
        return recommendations

# ============================================================================
# AGENT 3: ORDER AGENT
# ============================================================================

class OrderAgent:
    """Manages shopping cart and orders"""
    
    def __init__(self):
        self.cart = []
        self.order_history = []
        self.order_id_counter = 1000
    
    def add_to_cart(self, product):
        """Add product to cart"""
        for item in self.cart:
            if item['id'] == product['id']:
                item['quantity'] += 1
                return f"✅ Added another {product['title']} to cart (Qty: {item['quantity']})"
        
        product_copy = product.copy()
        product_copy['quantity'] = 1
        self.cart.append(product_copy)
        return f"✅ Added {product['title']} to cart (${product['price']})"
    
    def view_cart(self):
        """View current cart"""
        if not self.cart:
            return "Your cart is empty"
        
        cart_text = "🛒 **Your Cart:**\n"
        total = 0
        for item in self.cart:
            price = float(item['price'])
            subtotal = price * item['quantity']
            total += subtotal
            cart_text += f"- {item['title']} x{item['quantity']} = ${subtotal:.2f}\n"
        
        cart_text += f"\n**Total: ${total:.2f}**"
        return cart_text
    
    def checkout(self):
        """Process order checkout"""
        if not self.cart:
            return "❌ Cart is empty. Add items before checkout."
        
        total = sum(float(item['price']) * item['quantity'] for item in self.cart)
        order_id = self.order_id_counter
        self.order_id_counter += 1
        
        order = {
            'order_id': order_id,
            'items': self.cart.copy(),
            'total': total,
            'status': 'Confirmed'
        }
        
        self.order_history.append(order)
        cart_count = len(self.cart)
        self.cart = []
        
        confirmation = f"""✅ **ORDER CONFIRMED!**
Order ID: #{order_id}
Total: ${total:.2f}
Items: {cart_count} product(s)

Thank you for shopping! Your order will be delivered soon. 🚚"""
        
        return confirmation
    
    def remove_from_cart(self, product_id):
        """Remove product from cart"""
        self.cart = [item for item in self.cart if item['id'] != product_id]
        return f"✅ Removed from cart"
    
    def get_order_history(self):
        """Get order history"""
        if not self.order_history:
            return "No orders yet"
        
        history = "📋 **Order History:**\n"
        for order in self.order_history:
            history += f"- Order #{order['order_id']}: ${order['total']:.2f} ({order['status']})\n"
        
        return history

# ============================================================================
# SHOPPING ASSISTANT
# ============================================================================

class ShoppingAssistant:
    """Coordinates all 3 agents"""
    
    def __init__(self):
        self.preference_agent = PreferenceAgent()
        self.recommendation_agent = RecommendationAgent()
        self.order_agent = OrderAgent()
    
    def process_message(self, user_message):
        """Process message through all agents"""
        
        user_lower = user_message.lower()
        import re
        
        # ===== HANDLE COMMANDS FIRST (no recommendations) =====
        
        if 'add' in user_lower:
            product_ids = re.findall(r'add\s+(\d+)', user_lower)
            if product_ids:
                product_id = product_ids[0]
                # Find product in ChromaDB
                results = collection.query(query_texts=[""], n_results=20)
                for rid, metadata in zip(results['ids'][0], results['metadatas'][0]):
                    if rid == product_id:
                        product = {
                            'id': rid,
                            'title': metadata['title'],
                            'price': metadata['price'],
                            'category': metadata['category'],
                            'image': metadata['image'],
                            'rating': metadata['rating'],
                            'relevance': 100
                        }
                        return self.order_agent.add_to_cart(product)
                return f"❌ Product {product_id} not found"
        
        if 'checkout' in user_lower or 'buy' in user_lower:
            return self.order_agent.checkout()
        
        if 'view cart' in user_lower:
            return self.order_agent.view_cart()
        
        if 'remove' in user_lower:
            product_ids = re.findall(r'remove\s+(\d+)', user_lower)
            if product_ids:
                return self.order_agent.remove_from_cart(product_ids[0])
        
        if 'order history' in user_lower:
            return self.order_agent.get_order_history()
        
        # ===== FOR SEARCH QUERIES: Show recommendations =====
        
        preferences = self.preference_agent.extract(user_message)
        recommendations = self.recommendation_agent.recommend(preferences, user_message, limit=5)
        
        # Build response with recommendations
        response = ""
        
        # Add greeting based on preferences
        if preferences['budget'] and preferences['needs']:
            response += f"Great! I'm searching for {', '.join(preferences['needs'])} under ${preferences['budget']}. Found some perfect options! 🎯\n\n"
        elif preferences['budget']:
            response += f"Perfect! Let me find items under ${preferences['budget']} for you. 💰\n\n"
        elif preferences['needs']:
            response += f"Excellent! Searching for {', '.join(preferences['needs'])}. Here are my recommendations! ✨\n\n"
        else:
            response += "Let me find the best products for you! 🔍\n\n"
        
        # Add product recommendations
        if recommendations:
            response += "🛍️ **Recommended Products:**\n"
            for i, product in enumerate(recommendations, 1):
                response += f"\n{i}. **{product['title']}**\n"
                response += f"   💰 Price: ${product['price']}\n"
                response += f"   ⭐ Rating: {product['rating']}/5\n"
                response += f"   📁 Category: {product['category']}\n"
                response += f"   ✨ Match: {product['relevance']}%\n"
                response += f"   🖼️ Image: {product['image']}\n"
                response += f"   *[Product ID: {product['id']} - Say 'add {product['id']}' to add to cart]*"
        else:
            response += "❌ No products found matching your criteria. Try a different search!"
        
        return response