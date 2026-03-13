import json
import chromadb
from sentence_transformers import SentenceTransformer
import os

def load_products(filename='products.json'):
    """Load products from JSON file created by products.py"""
    if not os.path.exists(filename):
        print(f"❌ Error: {filename} not found. Run products.py first!")
        return []
    
    with open(filename, 'r') as f:
        products = json.load(f)
    
    print(f"✅ Loaded {len(products)} products from {filename}")
    return products

def create_product_texts(products):
    """
    Convert each product into a searchable text format
    This text will be embedded and searchable by the recommendation agent
    """
    product_texts = []
    
    for product in products:
        # Create rich text representation for embedding
        text = f"""
        Product: {product['title']}
        Category: {product['category']}
        Price: ${product['price']}
        Description: {product['description']}
        Rating: {product['rating']}/5
        """
        product_texts.append(text.strip())
    
    return product_texts

def setup_chromadb():
    """Initialize ChromaDB and create/get collection"""
    # Use persistent client (saves to disk)
    client = chromadb.PersistentClient(path="./chroma_db")
    
    # Delete old collection if exists (for fresh start)
    try:
        client.delete_collection(name="products")
    except:
        pass
    
    # Create new collection
    collection = client.get_or_create_collection(
        name="products",
        metadata={"hnsw:space": "cosine"}
    )
    
    print("✅ ChromaDB initialized")
    return client, collection

def embed_and_store_products(products, product_texts, collection):
    """
    Embed product texts using sentence-transformers
    Store embeddings + metadata in ChromaDB
    """
    print("\n🔄 Loading embedding model (first time takes ~30 seconds)...")
    model = SentenceTransformer('all-MiniLM-L6-v2')  # Fast, lightweight model
    
    print("🔄 Creating embeddings for products...")
    embeddings = model.encode(product_texts)
    
    print("💾 Storing in ChromaDB...")
    
    # Prepare data for ChromaDB
    ids = [str(product['id']) for product in products]
    documents = product_texts
    metadatas = [
        {
            'title': product['title'],
            'price': str(product['price']),
            'category': product['category'],
            'image': product['image'],
            'rating': str(product['rating'])
        }
        for product in products
    ]
    
    # Add to collection
    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings.tolist()
    )
    
    print(f"✅ Embedded and stored {len(products)} products in ChromaDB!")

def test_search(collection):
    """Test the RAG search functionality"""
    print("\n" + "="*50)
    print("🧪 TESTING SEARCH FUNCTIONALITY")
    print("="*50)
    
    test_queries = [
        "I want a comfortable laptop backpack",
        "Show me affordable clothing options",
        "I'm looking for jewelry or accessories"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        results = collection.query(
            query_texts=[query],
            n_results=3
        )
        
        print("📌 Top 3 Results:")
        for i, (doc_id, metadata, distance) in enumerate(zip(
            results['ids'][0],
            results['metadatas'][0],
            results['distances'][0]
        ), 1):
            print(f"  {i}. {metadata['title']}")
            print(f"     Price: ${metadata['price']} | Category: {metadata['category']}")
            print(f"     Relevance: {(1-distance)*100:.1f}%")

if __name__ == "__main__":
    print("="*50)
    print("🛒 PRODUCT EMBEDDING & CHROMADB SETUP")
    print("="*50)
    
    # Step 1: Load products
    products = load_products('products.json')
    if not products:
        exit(1)
    
    # Step 2: Create searchable text for each product
    product_texts = create_product_texts(products)
    print(f"✅ Created searchable text for {len(product_texts)} products")
    
    # Step 3: Setup ChromaDB
    client, collection = setup_chromadb()
    
    # Step 4: Embed and store
    embed_and_store_products(products, product_texts, collection)
    
    # Step 5: Test the search
    test_search(collection)
    
    print("\n" + "="*50)
    print("✅ SETUP COMPLETE!")
    print("="*50)
    print("ChromaDB is ready for product recommendations!")