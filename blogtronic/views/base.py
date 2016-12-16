import os

import jinja2
import webapp2

from os.path import dirname
from blogtronic.models import User
from blogtronic.auth import make_secure_val, check_secure_val

package_root = dirname(dirname(dirname(__file__)))
template_dir = os.path.join(package_root, "templates")
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
    autoescape=True)


class BlogHandler(webapp2.RequestHandler):
    user = None

    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        params['user'] = self.user
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def set_secure_cookie(self, name, val):
        cookie_val = make_secure_val(str(val))
        self.response.headers.add_header('Set-Cookie',
            '%s=%s; Path=/' % (name, cookie_val))

    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and check_secure_val(cookie_val)

    def login(self, user):
        self.set_secure_cookie('user_id', user.key().id())

    def logout(self):
        self.response.headers.add_header('Set-Cookie', "user_id=; Path=/")

    def initialize(self, *args, **kwargs):
        webapp2.RequestHandler.initialize(self, *args, **kwargs)
        uid = self.read_secure_cookie("user_id")
        self.user = uid and User.by_id(int(uid))
