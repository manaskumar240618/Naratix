import os
import time
import pandas as pd
import sqlite3
import re
import logging
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from openai import OpenAI
from threading import Thread

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(message)s')

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# OpenAI Client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
You are a business data analyst. Your responses must be structured:
- Provide key metrics and trends.
- Generate SQL queries only for business-related data questions.
- Offer business insights and recommendations based on available data.
If unrelated to business, respond: "I specialize in business data analysis."
"""

DB_PATH = "business_data.db"

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def load_dataframe(file_path):
    try:
        if file_path.endswith('.csv'):
            return pd.read_csv(file_path)
        elif file_path.endswith('.xlsx'):
            return pd.read_excel(file_path)
        elif file_path.endswith('.json'):
            return pd.read_json(file_path)
        else:
            raise ValueError("Unsupported file format.")
    except Exception as e:
        return f"• File Load Error: {str(e)}"

def process_data(file_path):
    df = load_dataframe(file_path)
    if isinstance(df, str):
        return df  # Error message
    return "\n".join([f"• {col}: Mean={df[col].mean():.2f}, Min={df[col].min()}, Max={df[col].max()}" for col in df.select_dtypes(include=['number']).columns])

def init_db(file_path):
    df = load_dataframe(file_path)
    if isinstance(df, str):
        return df  # Error message
    try:
        conn = get_db_connection()
        df.to_sql("business", conn, if_exists="replace", index=False)
        conn.close()
        return "• Database successfully initialized."
    except Exception as e:
        return f"• DB Error: {str(e)}"

def generate_sql_query(query):
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "Convert to SQL for SQLite 'business' table."},
            {"role": "user", "content": query}
        ],
        temperature=0.3,
        max_tokens=150
    )
    return response.choices[0].message.content.strip()

def execute_sql(query):
    try:
        if not re.match(r"^\s*SELECT\s", query, re.IGNORECASE):
            return "• Error: Only SELECT queries are allowed."
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        conn.close()
        return result
    except Exception as e:
        return str(e)

def generate_business_insights():
    try:
        conn = get_db_connection()
        df = pd.read_sql("SELECT * FROM business", conn)
        conn.close()
        insights = []
        
        # Enhanced insights generation
        for col in df.select_dtypes(include=['number']).columns:
            mean_value = df[col].mean()
            median_value = df[col].median()
            std_dev = df[col].std()
            
            if mean_value > median_value:
                insights.append(f"• {col}: Increasing trend detected. Consider leveraging for growth strategies.")
            else:
                insights.append(f"• {col}: Slight decline observed. Optimization recommended for better efficiency.")
            
            if std_dev > mean_value * 0.2:  # If standard deviation is high
                insights.append(f"• {col}: High volatility detected. Monitor fluctuations to mitigate risks.")
            
            if mean_value > df[col].quantile(0.75):
                insights.append(f"• {col}: Strong performance. Capitalize on this for further expansion.")
            elif mean_value < df[col].quantile(0.25):
                insights.append(f"• {col}: Weak performance. Investigate root causes and implement improvements.")
        
        return "\n".join(insights)
    except Exception as e:
        return f"• Insight Generation Error: {str(e)}"

def handle_file_processing(file_path):
    db_status = init_db(file_path)
    insights = generate_business_insights()
    logging.info(f"Processing Complete:\n{db_status}\n{insights}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    user_msg = request.json.get('message', '')
    
    try:
        if "sql" in user_msg.lower() or "query" in user_msg.lower():
            sql_query = generate_sql_query(user_msg)
            return jsonify({"response": f"• Query: {sql_query}\n• Result: {execute_sql(sql_query)}"})
        
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "system", "content": SYSTEM_PROMPT},
                      {"role": "user", "content": user_msg}],
            temperature=0.7,
            max_tokens=300
        )
        ai_response = response.choices[0].message.content.strip()
        return jsonify({"response": "\n".join([f"• {line.strip()}" for line in ai_response.split('. ')])})
    except OpenAI.APIConnectionError:
        return jsonify({"response": "• Error: Unable to connect to AI service. Try again later."}), 500
    except Exception as e:
        return jsonify({"response": f"• Unexpected Error: {str(e)}"}), 500

@app.route('/api/upload', methods=['POST'])
def upload_file():
    file = request.files.get('file')
    if not file or file.filename == '':
        return jsonify({"response": "• No file uploaded."}), 400
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{int(time.time())}_{file.filename}")
    try:
        file.save(file_path)
        Thread(target=handle_file_processing, args=(file_path,)).start()  # Background Processing
        logging.info(f"File uploaded: {file_path}")
        return jsonify({"response": "• File uploaded. Processing in background... Check later."})
    except Exception as e:
        logging.error(f"Upload Error: {str(e)}")
        return jsonify({"response": f"• Error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)