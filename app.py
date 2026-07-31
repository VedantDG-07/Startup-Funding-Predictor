from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data_collection')
def data_collection():
    return render_template('data_collection.html')

@app.route('/preprocessing')
def preprocessing():
    return render_template('preprocessing.html')

@app.route('/transformation')
def transformation():
    return render_template('transformation.html')

@app.route('/eda')
def eda():
    return render_template('eda.html')

@app.route('/text_mining')
def text_mining():
    return render_template('text_mining.html')

@app.route('/data_mining')
def data_mining():
    return render_template('data_mining.html')

@app.route('/prediction')
def prediction():
    return render_template('prediction.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/insights')
def insights():
    return render_template('insights.html')

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True)
