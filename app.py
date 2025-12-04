from flask import Flask, render_template, request, redirect, url_for, session, send_file, jsonify
import sqlite3
from crawler import crawl_baidu
from weasyprint import HTML
import io
import os
from bs4 import BeautifulSoup
from openai import OpenAI
import requests

def remove_html_tags(text):
    if not text: return ""
    soup = BeautifulSoup(text, 'html.parser')
    return soup.get_text(separator=' ', strip=True)

def fetch_and_extract_main_content(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Remove script and style elements
        for script_or_style in soup(['script', 'style']):
            script_or_style.decompose()

        # Get text, stripping whitespace
        text = soup.get_text(separator=' ', strip=True)
        return text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching content from {url}: {e}")
        return ""
    except Exception as e:
        print(f"Error extracting content from {url}: {e}")
        return ""

app = Flask(__name__)
app.secret_key = 'super_secret_key_for_govfilesystem_app_12345' # Replace with a strong secret key

DATABASE = 'database.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            session['logged_in'] = True
            session['username'] = user['username']
            return redirect(url_for('dashboard')) # Redirect to dashboard after successful login
        else:
            return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('login'))
    return render_template('dashboard.html', session=session)

@app.route('/collect_data', methods=['POST'])
def collect_data():
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('login'))
    
    keyword = request.form['keyword']
    try:
        results = crawl_baidu(keyword, output_format="json")
        return render_template('search_results.html', query=keyword, results=results)
    except Exception as e:
        return render_template('dashboard.html', session=session, error=f"爬取数据失败: {e}")

@app.route('/save_data', methods=['POST'])
def save_data():
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('login'))
    
    keyword = request.form['keyword']
    selected_indices = request.form.getlist('selected_results')
    
    conn = get_db()
    cursor = conn.cursor()
    
    saved_count = 0
    for index_str in selected_indices:
        index = int(index_str)
        title = request.form.get(f'title_{index}', '')
        url = request.form.get(f'url_{index}', '')
        snippet = request.form.get(f'snippet_{index}', '')
        
        if title and url:
            cursor.execute("INSERT INTO crawled_data (keyword, title, url, snippet) VALUES (?, ?, ?, ?)",
                           (keyword, title, url, snippet))
            saved_count += 1
            
    conn.commit()
    conn.close()
    
    return redirect(url_for('dashboard', message=f'成功保存 {saved_count} 条数据！'))

@app.route('/data_warehouse', methods=['GET'])
def data_warehouse():
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('login'))
    
    search_keyword = request.args.get('search_keyword', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    conn = get_db()
    cursor = conn.cursor()

    query = "SELECT * FROM crawled_data WHERE 1=1"
    params = []

    if search_keyword:
        query += " AND (keyword LIKE ? OR title LIKE ? OR snippet LIKE ?)"
        params.extend([f'%{search_keyword}%', f'%{search_keyword}%', f'%{search_keyword}%'])
    
    if start_date:
        query += " AND timestamp >= ?"
        params.append(start_date + " 00:00:00") # Assuming timestamp includes time, so append start of day
    
    if end_date:
        query += " AND timestamp <= ?"
        params.append(end_date + " 23:59:59") # Assuming timestamp includes time, so append end of day

    query += " ORDER BY timestamp DESC"
    
    cursor.execute(query, params)
    data = cursor.fetchall()
    conn.close()
    
    return render_template('data_warehouse.html', data=data, search_keyword=search_keyword, start_date=start_date, end_date=end_date)

@app.route('/process_with_ai', methods=['POST'])
def process_with_ai():
    if 'logged_in' not in session or not session['logged_in']:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    selected_ids = data.get('selected_ids', [])
    
    if not selected_ids:
        return jsonify({"error": "请选择至少一条数据进行处理。"}), 400

    conn = get_db()
    cursor = conn.cursor()
    
    # Fetch the selected data from the database
    placeholders = ', '.join(['?' for _ in selected_ids])
    query = f"SELECT * FROM crawled_data WHERE id IN ({placeholders})"
    cursor.execute(query, selected_ids)
    selected_data = cursor.fetchall()
    conn.close()

    # Get Qwen API Key from environment variable
    QWEN_API_KEY = "sk-mkxlqmxarjfxxejptlrzyxhuiahzeghjgtkkyppruvjqtnxb"

    # Construct the prompt for Qwen model
    prompt_content = "请根据以下信息，总结并提炼出核心要点，形成一份简洁的报告，不要输出md格式：\n"
    for item in selected_data:
        cleaned_keyword = remove_html_tags(item['keyword'])
        cleaned_title = remove_html_tags(item['title'])
        url = item['url']
        full_content = fetch_and_extract_main_content(url)
        
        if full_content:
            prompt_content += f"- 关键词: {cleaned_keyword}, 标题: {cleaned_title}, 来源URL: {url}, 网页内容: {full_content}\n"
        else:
            # Fallback to snippet if full content cannot be fetched
            cleaned_snippet = remove_html_tags(item['snippet'])
            prompt_content += f"- 关键词: {cleaned_keyword}, 标题: {cleaned_title}, 来源URL: {url}, 摘要: {cleaned_snippet}\n"

    # Siliconflow API configuration
    client = OpenAI(base_url="https://api.siliconflow.cn/v1/", api_key=QWEN_API_KEY)
    SILICONFLOW_MODEL_NAME = "deepseek-ai/DeepSeek-R1"

    refined_content = "AI模型处理失败。" # Default error message

    try:
        response = client.chat.completions.create(
            model=SILICONFLOW_MODEL_NAME,
            messages=[{"role": "user", "content": prompt_content}],
            stream=False, # Set to True if you want to handle streaming responses
            max_tokens=4096
        )
        
        if response.choices and response.choices[0].message:
            refined_content = response.choices[0].message.content
        else:
            refined_content = f"AI模型返回了无效的响应: {response}"
            
    except Exception as e:
        refined_content = f"调用Siliconflow API时发生错误: {e}"
    
    # Save the refined content to the ai_reports table
    original_data_ids_str = ', '.join(map(str, selected_ids))
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO ai_reports (original_data_ids, refined_content) VALUES (?, ?)",
                   (original_data_ids_str, refined_content))
    conn.commit()
    conn.close()
    
    return jsonify({"message": f"已选择 {len(selected_data)} 条数据提交给AI模型处理，并生成了报告。", "report_content": refined_content}), 200

@app.route('/ai_reports')
def ai_reports():
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('login'))
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ai_reports ORDER BY timestamp DESC")
    reports = cursor.fetchall()
    conn.close()
    
    return render_template('ai_reports.html', reports=reports)

@app.route('/report/pdf/<int:report_id>')
def generate_report_pdf(report_id):
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ai_reports WHERE id = ?", (report_id,))
    report = cursor.fetchone()
    conn.close()

    if report is None:
        return "Report not found", 404

    # Construct HTML for the PDF
    html_content = render_template('report_template.html', report=report, title=f"AI Report - {report_id}")

    # Generate PDF
    pdf = HTML(string=html_content).write_pdf()

    # Return PDF as a downloadable file
    return send_file(
        io.BytesIO(pdf),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'ai_report_{report_id}.pdf'
    )

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5001)
