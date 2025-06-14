from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import os
from datetime import datetime, timedelta
from functools import wraps
import csv

# --- เพิ่ม Library ใหม่สำหรับการเชื่อมต่อ Database ---
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# --- 1. การตั้งค่า Session และ Secret Key ---
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a-very-strong-secret-key-for-dev')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)


# --- *** ส่วนแก้ไขสำคัญ: ตรวจสอบการรันบน RENDER อย่างแม่นยำ *** ---

# Render.com จะตั้งค่าตัวแปร 'RENDER' เป็น 'true' ให้โดยอัตโนมัติ
# นี่เป็นวิธีที่ดีที่สุดในการตรวจสอบว่าแอปกำลังรันบนเซิร์ฟเวอร์จริงหรือไม่
IS_PRODUCTION = os.environ.get('RENDER') == 'true'

if IS_PRODUCTION:
    # --- โหมด Production (รันบน Render) ---
    print(">>> RUNNING IN PRODUCTION MODE ON RENDER <<<")
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL:
        raise ValueError("No DATABASE_URL set for Flask application on Render")
    # แก้ไข URL จาก 'postgres://' เป็น 'postgresql://' เพื่อความเข้ากันได้
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL.replace("postgres://", "postgresql://", 1)
else:
    # --- โหมด Development (รันบนเครื่อง Local) ---
    print(">>> RUNNING IN LOCAL DEVELOPMENT MODE <<<")
    # ใช้ SQLite เสมอเมื่อรันบนเครื่องคอมพิวเตอร์ส่วนตัว
    # จะเป็นการสร้างไฟล์ชื่อ 'local_dev.db' ในโฟลเดอร์โปรเจกต์
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///local_dev.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# --- สร้าง Model (เหมือนเดิม) ---
class UserLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    used_for = db.Column(db.String(50), nullable=False)
    login_datetime = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<UserLog {self.username}>'


# --- สร้างตารางใน Database (ถ้ายังไม่มี) ---
# ใช้ with app.app_context() เพื่อให้แน่ใจว่า Flask ทำงานถูกต้อง
with app.app_context():
    db.create_all()


# --- ฟังก์ชันจัดการข้อมูลและ Log (เหมือนเดิม) ---

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

def log_user_activity(username, keyword):
    """บันทึกชื่อผู้ใช้, keyword, วันที่, และเวลาที่เข้าสู่ระบบลงในไฟล์ CSV"""
    file_path = 'user_log.csv'
    try:
        file_exists = os.path.isfile(file_path)
        with open(file_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists or os.path.getsize(file_path) == 0:
                writer.writerow(['username', 'used_for', 'login_datetime'])
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            writer.writerow([username, keyword, now])
    except (IOError, OSError) as e:
        print(f"Could not write to CSV file: {e}")


# --- Decorator (เหมือนเดิม) ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('กรุณาเข้าสู่ระบบเพื่อดูเนื้อหาส่วนนี้', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# --- Routes ทั้งหมดยังคงเหมือนเดิม ---

@app.route('/')
def index():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/home')
@login_required
def home():
    posts = load_posts()
    return render_template('index.html', posts=posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form.get('username')
        keyword = request.form.get('keyword')
        if username and username.strip() and keyword:
            session.permanent = True
            session['username'] = username
            log_user_activity(username, keyword)
            try:
                new_log_entry = UserLog(username=username, used_for=keyword)
                db.session.add(new_log_entry)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"DATABASE ERROR: {e}")
                flash('เกิดข้อผิดพลาดในการบันทึกข้อมูลลงฐานข้อมูล', 'danger')
            flash(f'ยินดีต้อนรับ, {username}!', 'success')
            return redirect(url_for('home'))
        else:
            flash('กรุณากรอกข้อมูลให้ครบทั้งสองช่อง', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('คุณได้ออกจากระบบเรียบร้อยแล้ว', 'info')
    return redirect(url_for('login'))

@app.route('/works')
@login_required
def works():
    return render_template('works.html')

@app.route('/new', methods=['GET', 'POST'])
@login_required
def new_post():
    if request.method == 'POST':
        posts = load_posts()
        posts.append({'title': request.form.get('title'), 'content': request.form.get('content')})
        save_posts(posts)
        return redirect(url_for('home'))
    return render_template('post.html', post=None)

# --- ส่วนสำหรับรันแอปพลิเคชัน ---
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    # debug=True เหมาะสำหรับตอนพัฒนาบนเครื่อง Local
    app.run(debug=True, host='0.0.0.0', port=port)
    
    #############################################################
    ##############################################################
    #############################################################
# from flask import Flask, render_template, request, redirect, url_for, session, flash
# import json
# import os
# from datetime import datetime, timedelta
# from functools import wraps
# import csv

# app = Flask(__name__)

# # --- 1. การตั้งค่า Session และ Secret Key ---
# app.config['SECRET_KEY'] = 'your-very-secret-and-random-key'
# app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)


# # --- 2. ฟังก์ชันจัดการข้อมูลและ Log ---

# def load_posts():
#     """โหลดข้อมูลโพสต์จากไฟล์ posts.json"""
#     if not os.path.exists('posts.json'):
#         return []
#     with open('posts.json', 'r', encoding='utf-8') as f:
#         return json.load(f)

# def save_posts(posts):
#     """บันทึกข้อมูลโพสต์ลงในไฟล์ posts.json"""
#     with open('posts.json', 'w', encoding='utf-8') as f:
#         json.dump(posts, f, indent=4)

# # ***************************************************************
# # *** จุดแก้ไขที่ 1: อัปเดตฟังก์ชัน log_user_activity ***
# # ***************************************************************
# def log_user_activity(username, keyword):
#     """บันทึกชื่อผู้ใช้, keyword, วันที่, และเวลาที่เข้าสู่ระบบลงในไฟล์ CSV"""
#     file_path = 'user_log.csv'
#     file_exists = os.path.isfile(file_path)
    
#     # กำหนดหัวข้อคอลัมน์ใหม่
#     header = ['username', 'used_for', 'login_datetime']
    
#     with open(file_path, 'a', newline='', encoding='utf-8') as f:
#         writer = csv.writer(f)
        
#         # ถ้าไฟล์ยังไม่มี หรือไฟล์ว่างเปล่า ให้เขียนหัวข้อคอลัมน์ก่อน
#         if not file_exists or os.path.getsize(file_path) == 0:
#             writer.writerow(header)
        
#         # เตรียมข้อมูลที่จะบันทึก
#         now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#         log_data = [username, keyword, now]
        
#         # บันทึกข้อมูล
#         writer.writerow(log_data)


# # --- 3. Decorator สำหรับตรวจสอบการ Login ---
# def login_required(f):
#     """Decorator เพื่อตรวจสอบว่าผู้ใช้ล็อกอินอยู่หรือไม่"""
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         if 'username' not in session:
#             flash('กรุณาเข้าสู่ระบบเพื่อดูเนื้อหาส่วนนี้', 'warning')
#             return redirect(url_for('login'))
#         return f(*args, **kwargs)
#     return decorated_function


# # --- 4. Routes ของเว็บแอปพลิเคชัน ---

# @app.route('/')
# def index():
#     """Route หลักสำหรับเคลียร์ Session และบังคับไปหน้า Login"""
#     session.pop('username', None)
#     return redirect(url_for('login'))

# @app.route('/home')
# @login_required
# def home():
#     """หน้าหลักของบล็อก"""
#     posts = load_posts()
#     return render_template('index.html', posts=posts)

# # ***************************************************************
# # *** จุดแก้ไขที่ 2: อัปเดต Route /login ***
# # ***************************************************************
# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     """หน้าสำหรับเข้าสู่ระบบ"""
#     if 'username' in session:
#         return redirect(url_for('home'))

#     if request.method == 'POST':
#         # ใช้ .get() เพื่อความปลอดภัย ป้องกัน error หากไม่มีค่าส่งมา
#         username = request.form.get('username')
#         keyword = request.form.get('keyword')
        
#         # ตรวจสอบว่ามีการกรอก username และเลือก keyword ครบถ้วน
#         if username and username.strip() and keyword:
#             session.permanent = True
#             session['username'] = username
            
#             # ส่งค่า username และ keyword ไปยังฟังก์ชันบันทึก log
#             log_user_activity(username, keyword)
            
#             flash(f'ยินดีต้อนรับ, {username}!', 'success')
#             return redirect(url_for('home'))
#         else:
#             flash('กรุณากรอกข้อมูลให้ครบทั้งสองช่อง', 'danger')
#             return redirect(url_for('login'))
            
#     return render_template('login.html')

# @app.route('/logout')
# def logout():
#     """Route สำหรับออกจากระบบ"""
#     session.pop('username', None)
#     flash('คุณได้ออกจากระบบเรียบร้อยแล้ว', 'info')
#     return redirect(url_for('login'))

# @app.route('/works')
# @login_required
# def works():
#     """หน้าสำหรับแสดงผลงาน (Thesis)"""
#     return render_template('works.html')

# @app.route('/new', methods=['GET', 'POST'])
# @login_required
# def new_post():
#     """หน้าสำหรับสร้างโพสต์ใหม่"""
#     if request.method == 'POST':
#         posts = load_posts()
#         new_post = {
#             'title': request.form.get('title'), 
#             'content': request.form.get('content')
#         }
#         posts.append(new_post)
#         save_posts(posts)
#         return redirect(url_for('home'))
#     return render_template('post.html', post=None)


# # --- 5. ส่วนสำหรับรันแอปพลิเคชัน ---
# if __name__ == '__main__':
#     port = int(os.environ.get('PORT', 5000))
#     app.run(debug=True, host='0.0.0.0', port=port)