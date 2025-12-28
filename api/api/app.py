# app.py
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, instance_relative_config=True)
app.config['SECRET_KEY'] = 'change-this-to-a-secure-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'voting.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

os.makedirs(app.instance_path, exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    major = db.Column(db.String(120), nullable=False)
    photo_url = db.Column(db.String(255), nullable=False)

class Sponsor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    logo_url = db.Column(db.String(255), nullable=False)

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Constraint: one vote per user
    __table_args__ = (db.UniqueConstraint('user_id', name='unique_user_vote'),)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Seed database if empty
# Baru (jalan di Flask 3.x)
with app.app_context():
    db.create_all()
    if not User.query.filter_by(email='admin@campus.id').first():
        admin = User(email='admin@campus.id', name='Admin',
                     password_hash=generate_password_hash('admin123'))
        db.session.add(admin)
    if Candidate.query.count() == 0:
        candidates = [
            Candidate(name='Rian Saputera', major='Teknik Informatika',
                      photo_url='/static/img/1.jpg'),
            Candidate(name='Bima Saputra', major='Manajemen',
                      photo_url='/static/img/2.jpg'),
            Candidate(name='Citra Lestari', major='Desain Komunikasi Visual',
                      photo_url='/static/img/3.jpg'),
                        Candidate(name='Alya Pratama', major='Teknik Informatika',
                      photo_url='/static/img/4.jpg'),
            Candidate(name='wahyuu huda', major='Manajemen',
                      photo_url='/static/img/5.jpg'),
            Candidate(name='Chily ', major='Desain Komunikasi Visual',
                      photo_url='/static/img/6.jpg')
        ]
        db.session.add_all(candidates)
    if Sponsor.query.count() == 0:
        sponsors = [
            Sponsor(name='TechCorp', logo_url='/static/img/s1.png'),
            Sponsor(name='EduPlus', logo_url='/static/img/s2.jpg'),
            Sponsor(name='DesignHub', logo_url='/static/img/s3.png'),
            Sponsor(name='DesignH2ub', logo_url='/static/img/s3.png')
        ]
        db.session.add_all(sponsors)
    db.session.commit()

# Routes
@app.route('/')
def index():
    candidates = Candidate.query.all()
    sponsors = Sponsor.query.all()
    return render_template('index.html', candidates=candidates, sponsors=sponsors)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Email atau password salah.', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/api/vote', methods=['POST'])
@login_required
def api_vote():
    data = request.get_json() or {}
    candidate_id = data.get('candidate_id')
    if not candidate_id:
        return jsonify({'ok': False, 'message': 'Candidate ID wajib.'}), 400

    # Check if already voted
    existing = Vote.query.filter_by(user_id=current_user.id).first()
    if existing:
        return jsonify({'ok': False, 'message': 'Anda sudah memilih.'}), 409

    candidate = Candidate.query.get(candidate_id)
    if not candidate:
        return jsonify({'ok': False, 'message': 'Kandidat tidak ditemukan.'}), 404

    vote = Vote(user_id=current_user.id, candidate_id=candidate.id)
    db.session.add(vote)
    db.session.commit()
    return jsonify({'ok': True, 'redirect': url_for('thank_you')})

@app.route('/results')
def results():
    candidates = Candidate.query.all()
    votes = db.session.query(Candidate.id, Candidate.name, db.func.count(Vote.id).label('count'))\
        .outerjoin(Vote, Candidate.id == Vote.candidate_id)\
        .group_by(Candidate.id).all()

    # Determine top candidate
    top = None
    if votes:
        # votes is list of tuples (id, name, count)
        top_id = max(votes, key=lambda v: v[2])[0]
        top = Candidate.query.get(top_id)
    return render_template('results.html', candidates=candidates, votes=votes, top=top)

@app.route('/thank-you')
@login_required
def thank_you():
    return render_template('thank_you.html')

# Optional: Register route (for testing multiple users)
@app.route('/register', methods=['POST'])
def register():
    email = request.form.get('email', '').strip().lower()
    name = request.form.get('name', '').strip()
    password = request.form.get('password', '')
    if not email or not name or not password:
        return jsonify({'ok': False, 'message': 'Lengkapi semua field.'}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({'ok': False, 'message': 'Email sudah terdaftar.'}), 409
    user = User(email=email, name=name, password_hash=generate_password_hash(password))
    db.session.add(user)
    db.session.commit()
    return jsonify({'ok': True})

if __name__ == '__main__':
    app.run(debug=True)