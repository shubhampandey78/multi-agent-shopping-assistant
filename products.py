import requests
import json

def fetch_products():
    """
    Fetch products from FakeStore API
    Returns list of product dicts with: id, title, price, description, image, category
    """
    try:
        response = requests.get('https://fakestoreapi.com/products')
        products = response.json()
        
        # Enrich products with category and clean data
        enriched_products = []
        for product in products:
            enriched_products.append({
                'id': product['id'],
                'title': product['title'],
                'price': product['price'],
                'description': product['description'][:200],  # Truncate long descriptions
                'image': product['image'],
                'category': product['category'],
                'rating': product.get('rating', {}).get('rate', 0)
            })
        
        return enriched_products
    
    except Exception as e:
        print(f"Error fetching products: {e}")
        return []

def save_products_to_json(products, filename='products.json'):
    """Save products to JSON file for debugging"""
    with open(filename, 'w') as f:
        json.dump(products, f, indent=2)
    print(f"✅ Saved {len(products)} products to {filename}")

if __name__ == "__main__":
    print("🛒 Fetching products from FakeStore API...")
    products = fetch_products()
    
    if products:
        print(f"✅ Successfully fetched {len(products)} products!")
        print("\n📦 First 2 products:")
        for product in products[:2]:
            print(f"  - {product['title']} (${product['price']})")
        
        # Save to JSON for later use
        save_products_to_json(products)
    else:
        print("❌ No products fetched")