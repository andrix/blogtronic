from blogtronic.views.base import BlogHandler

from blogtronic.models import Post, User, post_extend
from blogtronic.validation import valid_username, valid_password, valid_email


class BlogFront(BlogHandler):
    def get(self):
        posts = Post.all().order("-created")
        postsl = []
        for p in posts:
            p = post_extend(p, self.user)
            postsl.append(p)
        posts = postsl
        self.render("front.html", posts=posts, user=self.user)


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
