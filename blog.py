# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

import json
import jinja2
import webapp2

from google.appengine.ext import db

from models import Post, blog_key, User, users_key, Like
from auth import make_secure_val, check_secure_val
from validation import valid_username, valid_password, valid_email

template_dir = os.path.join(os.path.dirname(__file__), "templates")
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

class MainPage(BlogHandler):
    def get(self):
        self.redirect("/blog/")

class BlogFront(BlogHandler):
    def get(self):
        posts = Post.all().order("-created")
        if self.user:
            postsl = []
            for p in posts:
                p.like = Like.post_liked_by(p, self.user)
                p.likes_count = Like.post_liked_count(p)
                postsl.append(p)
            posts = postsl
        self.render("front.html", posts=posts, user=self.user)

class PostPage(BlogHandler):
    def get(self, post_id):
        key = db.Key.from_path("Post", int(post_id), parent=blog_key())
        post = db.get(key)
        if not post:
            self.error(404)
            return
        if self.user:
            post.like = Like.post_liked_by(post, self.user)
            post.likes_count = Like.post_liked_count(post)
        self.render("permalink.html", p=post, user=self.user)

class NewPost(BlogHandler):
    def get(self):
        self.render("newpost.html")

    def post(self):
        subject = self.request.get("subject")
        content = self.request.get("content")

        if subject and content:
            if self.user:
                p = Post(parent=blog_key(), subject=subject, content=content,
                user_ref=self.user.key())
                p.put()
                self.redirect('/blog/%s' % str(p.key().id()))
            else:
                self.redirect("/login/")
        else:
            error = "You should provide a subject, and a content for your post!"
            self.render("newpost.html", content=content, subject=subject, error=error)

class EditPost(NewPost):
    def get(self, post_id):
        post = Post.get_by_id(int(post_id), parent=blog_key())
        self.render("newpost.html", subject=post.subject, content=post.content,
            post_id=post_id)

    def post(self, post_id):
        post = Post.get_by_id(int(post_id), parent=blog_key())
        subject = self.request.get("subject")
        content = self.request.get("content")
        if subject and content:
            post.subject = subject
            post.content = content
            post.put()
            self.redirect('/blog/%s' % str(post.key().id()))
        else:
            error = "You should provide a subject, and a content for your post!"
            self.render("newpost.html", content=content, subject=subject, error=error)


class ListPosts(BlogHandler):
    def get(self):
        posts = Post.all().filter("user_ref = ", self.user.key())
        self.render("edit-posts.html", posts=posts)

class LikePost(BlogHandler):
    def post(self):
        post_id = self.request.get("post_id")
        action = self.request.get("action")

        post = Post.get_by_id(int(post_id), parent=blog_key())
        result = Like.get_post_liked_by(post, self.user)
        like = False
        if result:
            # it's a dislike
            result.delete()
        else:
            # it's a like
            like = True
            lk = Like(user_ref=self.user.key(), post_ref=post.key())
            lk.put()
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps({"success": "OK"}))

class ListLikes(BlogHandler):
    def get(self):
        like = self.request.get("like")
        like = bool(int(like)) if like else None
        post = None
        if like:
            post_id = self.request.get("post_id")
            post = Post.get_by_id(int(post_id), parent=blog_key())
        likes = Like.all().filter("user_ref = ", self.user.key())
        self.render("likes.html", post_liked=post, user=self.user, likes=likes)

class SignUp(BlogHandler):
    def get(self):
        self.render("signup-form.html")

    def post(self):
        self.username = self.request.get("username")
        self.password = self.request.get("password")
        self.verify = self.request.get("verify")
        self.email = self.request.get("email")

        have_error = False
        params = dict(username=self.username, email=self.email)
        if not valid_username(self.username):
            have_error = True
            params["error_username"] = "That's not a valid username."

        if not valid_password(self.password):
            have_error = True
            params["error_password"] = "That's not a valid password."
        elif self.password != self.verify:
            have_error = True
            params["error_verify"] = "Your passwords didn't match."

        if not valid_email(self.email):
            have_error = True
            params["error_email"] = "That's not a valid email."

        if have_error:
            self.render("signup-form.html", **params)
        else:
            self.done()

    def done(self):
        raise NotImplementedError

class Register(SignUp):
    def done(self):
        u = User.by_name(self.username)
        if u:
            msg = "That user already exist!"
            self.render("signup-form.html", error_username=msg)
        else:
            u = User.register(self.username, self.password, self.email)
            u.put()
            self.login(u)
            self.redirect("/welcome/")

class WelcomePage(BlogHandler):
    def get(self):
        if self.user:
            self.render('welcome.html', username=self.user.name)
        else:
            self.redirect('/signup')

class Login(BlogHandler):
    def get(self):
        self.render("login-form.html")

    def post(self):
        username = self.request.get("username")
        password = self.request.get("password")

        u = User.login(username, password)
        if u:
            self.login(u)
            self.redirect("/welcome/")
        else:
            msg = "invalid login"
            self.render("login-form.html", error=msg)

class Logout(BlogHandler):
    def get(self):
        self.logout()
        self.redirect("/signup/")


app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/blog/?', BlogFront),
    ('/blog/([0-9]+)', PostPage),
    ('/blog/newpost/?', NewPost),
    ('/blog/edit-posts/?', ListPosts),
    ('/blog/edit/([0-9]+)', EditPost),
    ('/blog/like-post/?', LikePost),
    ('/blog/likes/?', ListLikes),
    # signup & login
    ('/signup/?', Register),
    ('/login/?', Login),
    ('/logout/?', Logout),
    ('/welcome/?', WelcomePage)
], debug=True)
