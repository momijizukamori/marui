import json
import secrets
import click
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import CSRFProtect

from utils import SiteData, SiteForm, LoginForm, read_file, write_file

CONFIG_PATH = 'config.json'
DATA_PATH = 'sites.json'

app = Flask(__name__)
app.secret_key = b"asdljsdlafjkwef123"
try:
    app.config.from_file(read_file(CONFIG_PATH), load=json.load)
except:
    print("Couldn't load config from file!")


csrf = CSRFProtect(app)
DATA = SiteData(DATA_PATH)
DEBUG = app.config.get('DEBUG', False)

@app.route('/', methods=['GET', 'POST'])
def index():
    form = SiteForm()
    if form.validate_on_submit():
        # very basic anti-spam check
        if form.agreement.data == "Y":
            DATA.handle_form(form)
    return render_template('main.html', sites=DATA.sites, form=form)

@app.route('/sites')
def sites():
    return DATA.data()

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if session.get('logged_in', False) and not DEBUG:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        clear = request.form.get('clear', False)
        ids = [int(request.form[key]) for key in request.form.keys() if 'check-' in key]

        if clear:
            DATA.remove_from_list(ids, clear)

        if request.form.get('remove', False):
            DATA.handle_removals(ids)

        if request.form.get('approve', False):
            DATA.handle_additions(ids)
      
        DATA.sort_and_save()
    return render_template('admin.html', data=DATA)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if session.get('logged_in', False) or DEBUG:
        return redirect(url_for('admin'))
    if request.method == 'POST':
        if check_password_hash(pw_hash['password'], form.password.data):
            return redirect(url_for('admin'))
    return render_template('login.html', form=form)

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
    app.config.webhook_service = webhook_service.lower()
    app.config.webhook_url = webhook_url
    app.config.site_url = site_url
    app.config.site_name = site_name
    app.config.SECRET_KEY = secrets.token_hex()
    write_file(CONFIG_PATH, app.config)