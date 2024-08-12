from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///helpdesk.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Open')
    priority = db.Column(db.String(20), default='Medium')
    category = db.Column(db.String(50))
    assigned_to = db.Column(db.String(100))
    requester_name = db.Column(db.String(100), nullable=False)
    requester_email = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted = db.Column(db.Boolean, default=False)  # New column for soft delete

@app.route('/')
@app.route('/tickets')
def tickets():
    tickets = Ticket.query.filter((Ticket.deleted == False) | (Ticket.deleted == None)).all()  # Show non-deleted tickets and tickets without the 'deleted' attribute
    return render_template('tickets.html', tickets=tickets)

@app.route('/tickets/new', methods=['GET', 'POST'])
def new_ticket():
    if request.method == 'POST':
        ticket = Ticket(
            title=request.form['title'],
            description=request.form['description'],
            status=request.form['status'],
            priority=request.form['priority'],
            category=request.form['category'],
            assigned_to=request.form['assigned_to'],
            requester_name=request.form['requester_name'],
            requester_email=request.form['requester_email']
        )
        db.session.add(ticket)
        db.session.commit()
        return redirect(url_for('tickets'))
    return render_template('new_ticket.html')

@app.route('/tickets/<int:id>/edit', methods=['GET', 'POST'])
def edit_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    if request.method == 'POST':
        ticket.title = request.form['title']
        ticket.description = request.form['description']
        ticket.status = request.form['status']
        ticket.priority = request.form['priority']
        ticket.category = request.form['category']
        ticket.assigned_to = request.form['assigned_to']
        ticket.requester_name = request.form['requester_name']
        ticket.requester_email = request.form['requester_email']
        db.session.commit()
        return redirect(url_for('tickets'))
    return render_template('edit_ticket.html', ticket=ticket)

@app.route('/tickets/<int:id>/delete', methods=['POST'])
def delete_ticket(id):
    ticket = Ticket.query.get_or_404(id)
    ticket.deleted = True
    db.session.commit()
    return redirect(url_for('tickets'))

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
    app.run(debug=True)