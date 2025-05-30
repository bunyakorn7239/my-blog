from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
import os

app = Flask(__name__)

def load_posts():
    if not os.path.exists('posts.json'):
        return []
    with open('posts.json', 'r') as f:
        return json.load(f)

def save_posts(posts):
    with open('posts.json', 'w') as f:
        json.dump(posts, f, indent=4)

@app.route('/')
def index():
    posts = load_posts()
    return render_template('index.html', posts=posts)

@app.route('/post/<int:post_id>')
def post(post_id):
    posts = load_posts()
    return render_template('post.html', post=posts[post_id])

@app.route('/new', methods=['GET', 'POST'])
def new_post():
    if request.method == 'POST':
        posts = load_posts()
        new_post = {
            'title': request.form['title'],
            'content': request.form['content']
        }
        posts.append(new_post)
        save_posts(posts)
        return redirect(url_for('index'))
    return render_template('post.html', post=None)

@app.route('/contact')
def contact():
    return render_template('contact.html')


# if __name__ == '__main__':
#     app.run(debug=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)

# from flask import Flask, render_template, request, redirect, url_for
# from flask_sqlalchemy import SQLAlchemy
# import os

# app = Flask(__name__)

# # ใช้ SQLite หรือ Render สามารถเปลี่ยนเป็น PostgreSQL ได้
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# db = SQLAlchemy(app)

# # โมเดล Post แทน posts.json
# class Post(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     title = db.Column(db.String(255), nullable=False)
#     content = db.Column(db.Text, nullable=False)

# @app.route('/')
# def index():
#     posts = Post.query.all()
#     return render_template('index.html', posts=posts)

# @app.route('/post/<int:post_id>')
# def post(post_id):
#     post = Post.query.get_or_404(post_id)
#     return render_template('post.html', post=post)

# @app.route('/new', methods=['GET', 'POST'])
# def new_post():
#     if request.method == 'POST':
#         new_post = Post(title=request.form['title'], content=request.form['content'])
#         db.session.add(new_post)
#         db.session.commit()
#         return redirect(url_for('index'))
#     return render_template('post.html', post=None)

# @app.route('/contact')
# def contact():
#     return render_template('contact.html')

# if __name__ == '__main__':
#     port = int(os.environ.get('PORT', 5000))
#     app.run(debug=True, host='0.0.0.0', port=port)
