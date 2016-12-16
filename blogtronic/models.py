from google.appengine.ext import db
from blogtronic.auth import make_pw_hash, valid_pw

def users_key(group='default'):
    return db.Key.from_path("users", group)

class User(db.Model):
    name = db.StringProperty(required=True)
    pw_hash = db.StringProperty(required=True)
    email = db.StringProperty()

    @classmethod
    def by_id(cls, uid):
        return User.get_by_id(uid, parent=users_key())

    @classmethod
    def by_name(cls, name):
        return User.all().filter("name = ", name).get()

    @classmethod
    def register(cls, name, pw, email=None):
        pw_hash = make_pw_hash(name, pw)
        u = User(parent=users_key(), name=name, pw_hash=pw_hash,
            email=email)
        return u

    @classmethod
    def login(cls, name, pw):
        u = cls.by_name(name)
        if u and valid_pw(name, pw, u.pw_hash):
            return u

def blog_key(name="default"):
    return db.Key.from_path("blogs", name)

class Post(db.Model):
    subject = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    last_modified = db.DateTimeProperty(auto_now=True)

    user_ref = db.ReferenceProperty(User)

    def user(self):
        return self.user_ref

class Like(db.Model):
    user_ref = db.ReferenceProperty(User)
    post_ref = db.ReferenceProperty(Post)

    @classmethod
    def get_post_liked_by(cls, post, user):
        q = cls.all()
        q.filter("user_ref =", user.key())
        q.filter("post_ref =", post.key())
        result = q.get()
        return result

    @classmethod
    def post_liked_by(cls, post, user):
        return (cls.get_post_liked_by(post, user) is not None)

    @classmethod
    def post_liked_count(cls, post):
        q = cls.all()
        q.filter("post_ref =", post.key())
        return q.count()

    @classmethod
    def delete_likes_from(cls, post=None, user=None):
        if not post and not user:
            return
        q = cls.all()
        likes = q.filter("post_ref=", post.key())
        db.delete(likes)


class Comment(db.Model):
    comment = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    last_modified = db.DateTimeProperty(auto_now=True)

    user_ref = db.ReferenceProperty(User)
    post_ref = db.ReferenceProperty(Post)

    @classmethod
    def count_for_post(cls, post):
        q = cls.all()
        q.filter("post_ref =", post.key())
        return q.count()

    @classmethod
    def comments_for_post(cls, post):
        q = cls.all()
        q.filter("post_ref =", post.key())
        q.order("-created")
        return [c for c in q.run()]


def post_extend(post, user):
    """
    Return an updated post with a few attributes added:
    - like: if the post is liked by the user logged in or not
    - likes_count: the number of like this post has (global)
    - comments_count - the number of commenst this post has (global)
    """

    if user:
        post.like = Like.post_liked_by(post, user)
    post.likes_count = Like.post_liked_count(post)
    post.comments_count = Comment.count_for_post(post)
    return post