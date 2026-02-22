
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
from src.scraper import Scraper
from src.notifier import Notifier
import os
from datetime import datetime
from dotenv import load_dotenv
import atexit

load_dotenv(override=True)

app = Flask(__name__)
CORS(app)

# Database Config
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Initialize Helpers
scraper = Scraper()
notifier = Notifier()

# --- Database Models ---
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=True)
    url = db.Column(db.String(500), nullable=False)
    target_price = db.Column(db.Float, nullable=False)
    current_price = db.Column(db.Float, nullable=True)
    last_checked = db.Column(db.DateTime, default=datetime.utcnow)
    email = db.Column(db.String(120), nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title or 'Unknown Product',
            'url': self.url,
            'target_price': self.target_price,
            'current_price': self.current_price,
            'last_checked': self.last_checked.isoformat() if self.last_checked else None,
            'email': self.email
        }

# --- Background Job ---
def check_prices():
    with app.app_context():
        print(f"[{datetime.now()}] Running background price check...")
        products = Product.query.filter_by(is_active=True).all()
        
        for product in products:
            try:
                print(f"Checking: {product.url}")
                result = scraper.get_price(product.url)
                
                if result and result.get('price'):
                    new_price = result['price']
                    product.current_price = new_price
                    product.last_checked = datetime.utcnow()
                    
                    # Update title if missing
                    if not product.title and result.get('title'):
                        product.title = result['title']

                    # Check for alert
                    if new_price <= product.target_price and product.email:
                        print(f"!!! Price Drop Alert for {product.title}: {new_price}")
                        notifier.send_notification(
                            product.url, 
                            new_price, 
                            product.target_price, 
                            product.email
                        )
                    
                    db.session.commit()
            except Exception as e:
                print(f"Error checking {product.url}: {e}")
        
        print("Background check complete.")

# Initialize Scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=check_prices, trigger="interval", hours=1)
scheduler.start()

# Stop scheduler on exit
atexit.register(lambda: scheduler.shutdown())

# --- Routes ---

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/products', methods=['GET'])
def get_products():
    products = Product.query.order_by(Product.id.desc()).all()
    return jsonify([p.to_dict() for p in products])

@app.route('/api/products', methods=['POST'])
def add_product():
    data = request.json
    url = data.get('url')
    target_price = float(data.get('target_price', 0))
    email = data.get('email')

    if not url:
        return jsonify({'error': 'URL is required'}), 400

    # Initial Scrape
    try:
        scrape_result = scraper.get_price(url)
        current_price = scrape_result['price'] if scrape_result else None
        title = scrape_result['title'] if scrape_result else 'New Product'
        
        if current_price is None:
            return jsonify({'error': 'Could not fetch initial price. Check URL.'}), 400
            
        new_product = Product(
            url=url,
            title=title,
            target_price=target_price,
            current_price=current_price,
            email=email
        )
        
        db.session.add(new_product)
        db.session.commit()
        
        return jsonify(new_product.to_dict()), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/<int:id>', methods=['PUT'])
def update_product(id):
    product = Product.query.get_or_404(id)
    data = request.json
    
    if 'target_price' in data:
        product.target_price = float(data['target_price'])
    if 'email' in data:
        product.email = data['email']
        
    db.session.commit()
    return jsonify(product.to_dict())

@app.route('/api/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({'success': True})

import threading

@app.route('/api/check-now', methods=['GET', 'POST'])
def manual_check():
    try:
        # Run in background to prevent request timeout on Render
        threading.Thread(target=check_prices).start()
        return jsonify({'success': True, 'message': 'Price check started in background'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Create Tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, port=5000, use_reloader=False) 
    # use_reloader=False is important to prevent scheduler running twice
