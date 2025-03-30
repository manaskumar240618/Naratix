 
import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import pandas as pd
import json
from werkzeug.utils import secure_filename
from utils.data_analysis import analyze_data, generate_graphs

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}

# Create Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
app.secret_key = 'your_secret_key'  # Required for flash messages

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Store file path in session
        return redirect(url_for('analyze', filename=filename))
    
    flash('Invalid file type. Please upload a CSV file.')
    return redirect(request.url)

@app.route('/analyze/<filename>')
def analyze(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    try:
        # Load the CSV file
        df = pd.read_csv(file_path)
        
        # Basic data analysis
        analysis_results = analyze_data(df)
        
        # Generate graphs
        graphs = generate_graphs(df)
        
        return render_template('analysis.html', 
                              filename=filename,
                              data_preview=df.head(10).to_html(classes='table table-striped'),
                              analysis_results=analysis_results,
                              graphs=graphs,
                              columns=df.columns.tolist())
    
    except Exception as e:
        flash(f'Error analyzing file: {str(e)}')
        return redirect(url_for('index'))

@app.route('/api/custom_graph', methods=['POST'])
def custom_graph():
    data = request.json
    filename = data.get('filename')
    graph_type = data.get('graph_type')
    x_column = data.get('x_column')
    y_column = data.get('y_column')
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    try:
        df = pd.read_csv(file_path)
        from utils.data_analysis import generate_custom_graph
        graph = generate_custom_graph(df, graph_type, x_column, y_column)
        return jsonify(graph)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)