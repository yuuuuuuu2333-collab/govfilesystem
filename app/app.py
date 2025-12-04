from flask import Flask, render_template, request, redirect, url_for, session, flash
from .database import init_db, get_db

app = Flask(__name__)
app.secret_key = 'your_secret_key' # Replace with a strong secret key

with app.app_context():
    init_db()

@app.route('/')
def index():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    return render_template('home.html')

@app.route('/crawl', methods=['POST'])
def crawl():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    keyword = request.form['keyword']
    # Here we will integrate the crawler later
    flash(f'您提交的关键字是: {keyword}', 'info')
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        db.close()

        if user:
            session['logged_in'] = True
            session['username'] = user['username']
            flash('登录成功！', 'success')
            return redirect(url_for('index'))
        else:
            flash('用户名或密码错误！', 'error')
            return render_template('login.html', error='用户名或密码错误！')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    flash('您已退出登录。', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)