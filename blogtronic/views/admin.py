from blogtronic.views.base import BlogHandler
from blogtronic.models import Post, Like, blog_key


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


class ListPosts(BlogHandler):
    def get(self):
        posts = Post.all().filter("user_ref = ", self.user.key())
        self.render("edit-posts.html", posts=posts)
