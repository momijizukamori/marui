import json
import os
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, PasswordField, SelectField, BooleanField
from wtforms.validators import DataRequired

def read_file(filename):
    try:
        with open(os.path.join('data', filename), 'r') as file:
            return json.load(file)
    except FileNotFoundError as e:
        print(f"Could not find {filename}")

    except json.decoder.JSONDecodeError as e:
        print(f"{filename} was invaid JSON")
    return {}
    
def write_file(filename, data):
    with open(os.path.join('data', filename), 'w') as file:
        return json.dump(data, file)

def handle_webhook(form):
    pass

class SiteData:
    def __init__(self, filepath='sites.json'):
        data = read_file(filepath)
        self.filename = filepath
        self.pending = data.get('pending', [])
        self.remove = data.get('remove', [])
        self.sites = data.get('sites', [])

    def data(self):
        return {'sites': self.sites, 'pending': self.pending, 'remove': self.remove}
    
    def handle_form(self, form):
        url = form.site_url.data
        data = {
            'url' : url,
            'name': form.site_name.data,
            'desc': form.site_desc.data
        }

        if form.removal.data:
            if url in [site['url'] for site in self.sites]:
                self.remove.append(data)
        else:
            self.pending.append(data)

        self.sort_and_save

    def handle_removals(self, ids):
            removals = self.remove_from_list(ids, 'remove')
            for site in removals:
                site_index = self.get_index(self.sites, site['url'])
                if site_index > -1:
                    self.sites.pop(site_index)
    
    def handle_additions(self, ids):
        additions = self.remove_from_list(ids, 'pending')
        for site in additions:
            site_index = self.get_index(self.sites, site['url'])
            if site_index > -1:
                self.sites[site_index] = site
            else:
                self.sites.append(site)
    
    @staticmethod
    def get_index(sitelist, url):
        for index, site in enumerate(sitelist):
            if url in site['url']:
                return index
        return -1

    def remove_from_list(self, indices, listname):
        indices.sort(reverse=True)
        if indices[0] <= len(getattr(self, listname)):
            return [getattr(self, listname).pop(i) for i in indices]
        else:
            return []
        
    def sort_and_save(self):
        for sitelist in [self.sites, self.pending, self.remove]:
            sitelist.sort(key=lambda site: site['name'])
        write_file('sites.json', self.data())


class SiteForm(FlaskForm):
    site_url = StringField('Site URL', validators=[DataRequired()])
    site_name = StringField('Site Name')
    site_desc = TextAreaField('Site Description')
    agreement = SelectField('Do you agree to the rules?', choices=[("-", "-"), ("N", "No"), ("Y", "Yes")])
    removal = BooleanField('Remove site')

class LoginForm(FlaskForm):
    password = PasswordField('password')