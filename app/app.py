from flask import Flask, request, render_template_string, jsonify
import mysql.connector
import os

app = Flask(__name__)

# MySQL bağlantı bilgileri (Kubernetes environment variables)
DB_HOST = os.environ.get('DB_HOST', 'bmi-db-service')
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASSWORD = os.environ.get('MYSQL_ROOT_PASSWORD', 'bmi123')
DB_NAME = os.environ.get('MYSQL_DATABASE', 'bmidb')

def get_db_connection():
    """MySQL bağlantısı oluştur"""
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

def init_db():
    """Veritabanı tablosunu oluştur"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bmi_records (
                id INT AUTO_INCREMENT PRIMARY KEY,
                weight FLOAT NOT NULL,
                height FLOAT NOT NULL,
                bmi FLOAT NOT NULL,
                category VARCHAR(50) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ MySQL veritabanı bağlantısı başarılı")
    except Exception as e:
        print(f"❌ MySQL bağlantı hatası: {e}")

# HTML Template (Tek dosya)
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>BMI Hesaplayıcı - MySQL</title>
    <style>
        body { font-family: Arial; background: #667eea; display: flex; justify-content: center; align-items: center; height: 100vh; }
        .container { background: white; padding: 30px; border-radius: 15px; width: 400px; text-align: center; }
        input { width: 100%; padding: 10px; margin: 10px 0; }
        button { background: #667eea; color: white; padding: 10px; width: 100%; border: none; cursor: pointer; }
        .badge { background: #28a745; color: white; padding: 5px; border-radius: 10px; display: inline-block; margin-bottom: 10px; }
        .result { margin-top: 20px; display: none; }
        .history { margin-top: 20px; text-align: left; border-top: 1px solid #ccc; padding-top: 10px; }
        .history-item { padding: 5px; border-bottom: 1px solid #eee; }
    </style>
</head>
<body>
    <div class="container">
        <h1>BMI Hesaplayıcı</h1>
        <div class="badge" id="versionBadge">EnSon</div>
        <input type="number" id="weight" placeholder="Kilo (kg)">
        <input type="number" id="height" placeholder="Boy (cm)">
        <button onclick="calculateBMI()">Hesapla</button>
        <div id="result" class="result">
            <h2 id="bmiValue"></h2>
            <p id="categoryText"></p>
        </div>
        <div class="history">
            <h3>Son Hesaplamalar</h3>
            <div id="historyList"></div>
        </div>
    </div>
    <script>
        function calculateBMI() {
            fetch('/calculate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: `weight=${document.getElementById('weight').value}&height=${document.getElementById('height').value}`
            })
            .then(res => res.json())
            .then(data => {
                document.getElementById('bmiValue').innerHTML = `BMI: ${data.bmi}`;
                document.getElementById('categoryText').innerHTML = data.category;
                document.getElementById('result').style.display = 'block';
                loadHistory();
            });
        }
        function loadHistory() {
            fetch('/history').then(res => res.json()).then(data => {
                let html = '';
                data.forEach(item => {
                    html += `<div class="history-item">${item.date} - ${item.weight}kg/${item.height}cm → BMI: ${item.bmi} (${item.category})</div>`;
                });
                document.getElementById('historyList').innerHTML = html || 'Henüz hesaplama yok';
            });
        }
        loadHistory();
    </script>
</body>
</html>
'''

def calculate_bmi(weight, height):
    height_m = height / 100
    bmi = weight / (height_m ** 2)
    if bmi < 18.5:
        category = "Zayıf"
    elif bmi < 25:
        category = "Normal"
    elif bmi < 30:
        category = "Kilolu"
    else:
        category = "Obez"
    return round(bmi, 1), category

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/calculate', methods=['POST'])
def calculate():
    weight = float(request.form.get('weight'))
    height = float(request.form.get('height'))
    bmi, category = calculate_bmi(weight, height)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO bmi_records (weight, height, bmi, category) VALUES (%s, %s, %s, %s)',
                   (weight, height, bmi, category))
    conn.commit()
    cursor.close()
    conn.close()
    
    return {'bmi': bmi, 'category': category}

@app.route('/history')
def history():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT weight, height, bmi, category, created_at FROM bmi_records ORDER BY created_at DESC LIMIT 10')
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return [{'weight': r[0], 'height': r[1], 'bmi': r[2], 'category': r[3], 'date': str(r[4])[:16]} for r in rows]

@app.route('/health')
def health():
    return {'status': 'healthy'}

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
