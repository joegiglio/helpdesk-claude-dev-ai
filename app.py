from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///helpdesk.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Open')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/')
@app.route('/tickets')
def tickets():
    tickets = Ticket.query.all()
    return render_template('tickets.html', tickets=tickets)

@app.route('/tickets/new', methods=['GET', 'POST'])
def new_ticket():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        new_ticket = Ticket(title=title, description=description)
        db.session.add(new_ticket)
        db.session.commit()
        return redirect(url_for('tickets'))
    return render_template('new_ticket.html')

@app.route('/integrations')
def integrations():
    return render_template('integrations.html')

@app.route('/workflows')
def workflows():
    return render_template('workflows.html')

@app.route('/team')
def team():
    return render_template('team.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)