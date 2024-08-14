from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
import os
import requests
import pytz
from jira import JIRA

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///helpdesk.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Add this line
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
    jira_issue_key = db.Column(db.String(20))  # New column for JIRA issue key

    def to_dict(self):
        # Assume UTC timezone for stored dates
        utc = pytz.UTC
        # Convert to US/Pacific timezone (you can change this to any desired timezone)
        pacific = pytz.timezone('US/Pacific')
        created_at_pacific = utc.localize(self.created_at).astimezone(pacific)
        updated_at_pacific = utc.localize(self.updated_at).astimezone(pacific)
        
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'category': self.category,
            'assigned_to': self.assigned_to,
            'requester_name': self.requester_name,
            'requester_email': self.requester_email,
            'created_at': created_at_pacific.strftime('%m/%d/%Y %I:%M %p'),
            'updated_at': updated_at_pacific.strftime('%m/%d/%Y %I:%M %p'),
            'created_at_iso': self.created_at.isoformat(),
            'updated_at_iso': self.updated_at.isoformat(),
            'jira_issue_key': self.jira_issue_key
        }

class IntegrationSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    integration_name = db.Column(db.String(50), nullable=False, unique=True)
    enabled = db.Column(db.Boolean, default=False)
    webhook_url = db.Column(db.String(200))
    api_url = db.Column(db.String(200))
    username = db.Column(db.String(100))
    api_token = db.Column(db.String(100))
    project_key = db.Column(db.String(20))

def get_slack_webhook_url():
    slack_setting = IntegrationSetting.query.filter_by(integration_name='Slack').first()
    return slack_setting.webhook_url if slack_setting and slack_setting.enabled else None

def get_jira_settings():
    jira_setting = IntegrationSetting.query.filter_by(integration_name='JIRA').first()
    if jira_setting and jira_setting.enabled:
        return {
            'server': jira_setting.api_url,
            'username': jira_setting.username,
            'api_token': jira_setting.api_token,
            'project_key': jira_setting.project_key
        }
    return None

def send_slack_notification(ticket):
    with app.app_context():
        slack_webhook_url = get_slack_webhook_url()
        if not slack_webhook_url:
            print("Slack integration is not enabled or webhook URL is not set.")
            return

        ticket_url = url_for('edit_ticket', id=ticket.id, _external=True)
        message = f"""
New Ticket Created:
*<{ticket_url}|#{ticket.id}: {ticket.title}>*
*Description:* {ticket.description}
*Priority:* {ticket.priority}
*Category:* {ticket.category}
*Requester:* {ticket.requester_name} ({ticket.requester_email})
        """
        payload = {
            'text': 'New Ticket Created',
            'attachments': [
                {
                    'color': '#36a64f',
                    'text': message,
                    'actions': [
                        {
                            'type': 'button',
                            'text': 'View Ticket',
                            'url': ticket_url
                        }
                    ]
                }
            ]
        }
        try:
            response = requests.post(slack_webhook_url, json=payload)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error sending Slack notification: {e}")

def create_jira_issue(ticket):
    jira_settings = get_jira_settings()
    if not jira_settings:
        print("JIRA integration is not enabled or settings are not configured.")
        return None

    try:
        jira = JIRA(server=jira_settings['server'],
                    basic_auth=(jira_settings['username'], jira_settings['api_token']))

        issue_dict = {
            'project': {'key': jira_settings['project_key']},
            'summary': ticket.title,
            'description': ticket.description,
            'issuetype': {'name': 'Task'},
            # 'priority': {'name': ticket.priority},
        }

        new_issue = jira.create_issue(fields=issue_dict)
        return new_issue.key
    except Exception as e:
        print(f"Error creating JIRA issue: {e}")
        return None

@app.route('/')
@app.route('/tickets')
def tickets():
    tickets = Ticket.query.filter((Ticket.deleted == False) | (Ticket.deleted == None)).order_by(Ticket.created_at.desc()).all()
    return render_template('tickets.html', tickets=[ticket.to_dict() for ticket in tickets])

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
        
        # Send Slack notification
        send_slack_notification(ticket)
        
        # Create JIRA issue
        jira_issue_key = create_jira_issue(ticket)
        if jira_issue_key:
            ticket.jira_issue_key = jira_issue_key
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

@app.route('/integrations/slack', methods=['GET', 'POST'])
def slack_integration():
    slack_setting = IntegrationSetting.query.filter_by(integration_name='Slack').first()
    if not slack_setting:
        slack_setting = IntegrationSetting(integration_name='Slack')
        db.session.add(slack_setting)
        db.session.commit()

    if request.method == 'POST':
        slack_setting.enabled = 'enabled' in request.form
        slack_setting.webhook_url = request.form['webhook_url']
        db.session.commit()
        flash('Slack integration settings have been saved successfully.', 'success')
        return redirect(url_for('integrations'))

    return render_template('slack_integration.html', slack_setting=slack_setting)

@app.route('/integrations/jira', methods=['GET', 'POST'])
def jira_integration():
    jira_setting = IntegrationSetting.query.filter_by(integration_name='JIRA').first()
    if not jira_setting:
        jira_setting = IntegrationSetting(integration_name='JIRA')
        db.session.add(jira_setting)
        db.session.commit()

    if request.method == 'POST':
        jira_setting.enabled = 'enabled' in request.form
        jira_setting.api_url = request.form['api_url']
        jira_setting.username = request.form['username']
        jira_setting.api_token = request.form['api_token']
        jira_setting.project_key = request.form['project_key']
        db.session.commit()
        flash('JIRA integration settings have been saved successfully.', 'success')
        return redirect(url_for('integrations'))

    return render_template('jira_integration.html', jira_setting=jira_setting)

@app.route('/integrations/salesforce')
def salesforce_integration():
    return render_template('salesforce_integration.html')

@app.route('/integrations/webhook')
def webhook_integration():
    return render_template('webhook_integration.html')

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