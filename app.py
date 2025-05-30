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

