from flask import Flask, request, redirect, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
import re

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mappings.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define the model for URL mapping
class URLMapping(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    short_code = db.Column(db.String(80), unique=True, nullable=False)
    long_url = db.Column(db.String(2083), nullable=False)  # 2083 is max URL length in IE

# Create the database and tables
with app.app_context():
    db.create_all()

# URL validation function (basic example)
def is_valid_url(url):
    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'\S+$', re.IGNORECASE)
    return re.match(regex, url) is not None

# API endpoint to create a mapping
@app.route('/api/mappings', methods=['POST'])
def create_mapping():
    data = request.get_json()
    if not data or 'short_code' not in data or 'long_url' not in data:
        return jsonify({'error': 'Invalid payload'}), 400

    short_code = data['short_code']
    long_url = data['long_url']

    if not is_valid_url(long_url):
        return jsonify({'error': 'Invalid URL format'}), 400

    # Check for duplicate short_code
    if URLMapping.query.filter_by(short_code=short_code).first():
        return jsonify({'error': 'Short code already exists'}), 400

    new_mapping = URLMapping(short_code=short_code, long_url=long_url)
    db.session.add(new_mapping)
    db.session.commit()
    return jsonify({'message': 'Mapping created', 'short_code': short_code, 'long_url': long_url}), 201

# Endpoint to redirect based on short_code
@app.route('/<short_code>', methods=['GET'])
def redirect_short_url(short_code):
    mapping = URLMapping.query.filter_by(short_code=short_code).first()
    if mapping:
        return redirect(mapping.long_url, code=302)
    else:
        abort(404)

if __name__ == '__main__':
    app.run(debug=True)
