from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import os
from datetime import datetime, timedelta
from functools import wraps
import csv

app = Flask(__name__)

# --- 1. การตั้งค่า Session และ Secret Key ---
# SECRET_KEY เป็นสิ่งจำเป็นสำหรับการใช้ session เพื่อความปลอดภัย
# ควรตั้งเป็นค่าสุ่มยาวๆ ที่ไม่สามารถเดาได้
app.config['SECRET_KEY'] = 'your-very-secret-and-random-key'

# ตั้งเวลาหมดอายุของ session (Logout อัตโนมัติ) เป็นเวลา 30 นาที
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)


# --- 2. ฟังก์ชันจัดการข้อมูลและ Log ---
def load_posts():
    """โหลดข้อมูลโพสต์จากไฟล์ posts.json"""
    if not os.path.exists('posts.json'):
        return []
    with open('posts.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def save_posts(posts):
    """บันทึกข้อมูลโพสต์ลงในไฟล์ posts.json"""
    with open('posts.json', 'w', encoding='utf-8') as f:
        json.dump(posts, f, indent=4)

def log_user_activity(username):
    """บันทึกชื่อผู้ใช้, วันที่, และเวลาที่เข้าสู่ระบบลงในไฟล์ CSV"""
    file_exists = os.path.isfile('user_log.csv')
    with open('user_log.csv', 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        # ถ้าเป็นไฟล์ใหม่ ให้เขียนหัวข้อคอลัมน์ก่อน
        if not file_exists:
            writer.writerow(['username', 'login_datetime'])
        
        # บันทึกข้อมูล
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        writer.writerow([username, now])


# --- 3. Decorator สำหรับตรวจสอบการ Login ---
def login_required(f):
    """Decorator เพื่อตรวจสอบว่าผู้ใช้ล็อกอินอยู่หรือไม่"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('กรุณาเข้าสู่ระบบเพื่อดูเนื้อหาส่วนนี้', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# --- 4. Routes ของเว็บแอปพลิเคชัน ---

# @app.route('/')
# def index():
#     """Route หลักสำหรับตรวจสอบและ Redirect ไปยังหน้า Home หรือ Login"""
#     if 'username' in session:
#         return redirect(url_for('home'))
#     return redirect(url_for('login'))

@app.route('/')
def index():
    # ล้าง session ของผู้ใช้ออกทุกครั้งที่เข้ามาที่หน้าแรกสุด
    session.pop('username', None)
    
    # จากนั้นส่งผู้ใช้ไปที่หน้า Login เสมอ
    return redirect(url_for('login'))

@app.route('/home')
@login_required
def home():
    """หน้าหลักของบล็อก (แสดงรายการโพสต์)"""
    posts = load_posts()
    return render_template('index.html', posts=posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """หน้าสำหรับเข้าสู่ระบบ"""
    if 'username' in session:
        return redirect(url_for('home'))

    if request.method == 'POST':
        username = request.form['username']
        keyword = request.form['keyword']
        
        # เงื่อนไขการล็อกอิน: แค่กรอกข้อมูลให้ครบทั้ง 2 ช่อง
        if username.strip() and keyword.strip():
            session.permanent = True
            session['username'] = username
            log_user_activity(username)
            flash(f'ยินดีต้อนรับ, {username}!', 'success')
            return redirect(url_for('home'))
        else:
            flash('กรุณากรอกข้อมูลให้ครบทั้งสองช่อง', 'danger')
            return redirect(url_for('login'))
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Route สำหรับออกจากระบบ"""
    session.pop('username', None)
    flash('คุณได้ออกจากระบบเรียบร้อยแล้ว', 'info')
    return redirect(url_for('login'))

@app.route('/works')
@login_required
def works():
    """หน้าสำหรับแสดงผลงาน (Thesis)"""
    return render_template('works.html')

@app.route('/new', methods=['GET', 'POST'])
@login_required
def new_post():
    """หน้าสำหรับสร้างโพสต์ใหม่"""
    if request.method == 'POST':
        posts = load_posts()
        new_post = {'title': request.form['title'], 'content': request.form['content']}
        posts.append(new_post)
        save_posts(posts)
        return redirect(url_for('home'))
    return render_template('post.html', post=None)


# --- 5. ส่วนสำหรับรันแอปพลิเคชัน ---
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)