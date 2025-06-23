
import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from google.cloud import firestore
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')

# Initialize Firestore DB
db = firestore.Client()

@app.before_first_request
def init_books():
    books_ref = db.collection('books')
    if not list(books_ref.stream()):
        sample_books = [
            {'title': 'The Great Gatsby', 'author': 'F. Scott Fitzgerald', 'price': 10.99, 
             'description': 'A story of wealth and love in the Jazz Age', 'image_url': 'https://m.media-amazon.com/images/I/71FTb9X6wsL._AC_UF1000,1000_QL80_.jpg'},
            {'title': 'To Kill a Mockingbird', 'author': 'Harper Lee', 'price': 12.50,
             'description': 'A powerful story of racial injustice', 'image_url': 'https://m.media-amazon.com/images/I/71FxgtFKcQL._AC_UF1000,1000_QL80_.jpg'},
            {'title': '1984', 'author': 'George Orwell', 'price': 9.99,
             'description': 'Dystopian novel about totalitarianism', 'image_url': 'https://m.media-amazon.com/images/I/71kxa1-0mfL._AC_UF1000,1000_QL80_.jpg'}
        ]
        for book in sample_books:
            books_ref.add(book)

@app.route('/')
def home():
    books = [doc.to_dict() | {'id': doc.id} for doc in db.collection('books').stream()]
    return render_template('home.html', books=books)

@app.route('/book/<book_id>')
def book_detail(book_id):
    doc = db.collection('books').document(book_id).get()
    if not doc.exists:
        flash('Book not found', 'danger')
        return redirect(url_for('home'))
    return render_template('book_detail.html', book=doc.to_dict())

@app.route('/search')
def search():
    query = request.args.get('q', '')
    results = [doc.to_dict() for doc in db.collection('books').stream()
               if query.lower() in doc.to_dict().get('title', '').lower() or query.lower() in doc.to_dict().get('author', '').lower()]
    return render_template('search_results.html', results=results, query=query)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        docs = db.collection('users').where('username', '==', username).stream()
        user = next(docs, None)
        if user:
            user_data = user.to_dict()
            if check_password_hash(user_data['password'], password):
                session['user_id'] = user.id
                session['username'] = user_data['username']
                flash('Login successful!', 'success')
                return redirect(url_for('home'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        email = request.form['email']
        existing = list(db.collection('users').where('username', '==', username).stream())
        if existing:
            flash('Username already exists', 'danger')
        else:
            db.collection('users').add({
                'username': username,
                'password': password,
                'email': email
            })
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), debug=True)
