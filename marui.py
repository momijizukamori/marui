import json
import secrets
import os
import click
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import StringField, TextAreaField, PasswordField, SelectField, BooleanField
from wtforms.validators import DataRequired

app = Flask(__name__)
app.secret_key = b"asdljsdlafjkwef123"
try:
    app.config.from_file(read_file('config.json'), load=json.load)
except:
    print("Couldn't load config from file!")

csrf = CSRFProtect(app)
SITES = {}
DEBUG = app.config.get('DEBUG', False)


try:
    SITES = read_file('sites.json')
except:
    print("Couldn't load sites from file!")

def read_file(filename):
    with open(os.path.join('data', filename), 'r') as file:
        return json.load(file)

def write_file(filename, data):
    with open(os.path.join('data', filename), 'w') as file:
        return json.dump(data, file)

def add_to_file(filename, data):
    datalist = read_file(filename)
    datalist['sites'].append(data)
    write_file(filename, datalist)

class SiteForm(FlaskForm):
    site_url = StringField('Site URL', validators=[DataRequired()])
    site_name = StringField('Site Name')
    site_desc = TextAreaField('Site Description')
    agreement = SelectField('Do you agree to the rules?', choices=[("-", "-"), ("N", "No"), ("Y", "Yes")])
    removal = BooleanField('Remove site')

class LoginForm(FlaskForm):
    password = PasswordField('password')

@app.route('/', methods=['GET', 'POST'])
def index():
    form = SiteForm()
    if form.validate_on_submit():
        # very basic anti-spam check
        if form.agreement.data == "Y":
            handle_form(form)
    return render_template('main.html', sites=SITES, form=form)

@app.route('/json')
def sites():
    form = SiteForm()
    if form.validate_on_submit():
        # very basic anti-spam check
        if form.agreement.data == "Y":
            handle_form(form)

    return render_template('main.html', sites=SITES, form=form)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if session.get('logged_in', False) and not DEBUG:
        return redirect(url_for('login'))
    pending = read_file('pending.json')
    remove = read_file('remove.json')
    if request.method == 'POST':
        print(request.form)
        if request.form.get('remove', False):
            ids = get_ids(request.form, 'remove-')
        if request.form.get('approve', False):
            ids = get_ids(request.form, 'add-')
    return render_template('admin.html', sites=SITES, pending=pending, remove=remove)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if session.get('logged_in', False) or DEBUG:
        return redirect(url_for('admin'))
    if request.method == 'POST':
        if check_password_hash(pw_hash['password'], form.password.data):
            return redirect(url_for('admin'))
    return render_template('login.html', form=form)

def handle_form(form):
    data = {
        'url' : form.site_url.data,
        'name': form.site_name.data,
        'desc': form.site_desc.data
    }

    site_urls = [site['url'] for site in SITES]
    if form.removal.data:
        if data['url'] in site_urls:
            add_to_file('remove.json', data)
    else:
        add_to_file('pending.json', data)

def handle_webhook(form):
    pass

def get_ids(form, keyword):
    return [key for key in form.keys() if keyword in key]

@app.cli.command("update-password")
@click.password_option()
def update_password(password):
    app.config.password = generate_password_hash(password)
    write_file('config.json', app.config)

@app.cli.command("setup")
@click.password_option()
@click.option('--site-url', prompt='Site URL (this is used in generating some of the webring code)')
@click.option('--site-name', prompt='Site name (this is used in generating some of the webring code)')
@click.option('--webhook-service',
              type=click.Choice(['Discord', 'Slack', 'Zapier', 'IFTT', 'Pipedream'], case_sensitive=False), prompt=True)
@click.option('--webhook-url', prompt=True)
def setup_config(password, site_url, site_name, webhook_service, webhook_url):
    app.config.password = generate_password_hash(password)
    app.config.webhook_service = lower(webhook_service)
    app.config.webhook_url = webhook_url
    app.config.site_url = site_url
    app.config.site_name = site_name
    app.config.SECRET_KEY = secrets.token_hex()
    write_file(CONFIG_PATH, app.config)