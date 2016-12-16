import json

from blogtronic.views.base import BlogHandler
from blogtronic.models import Post, Like, blog_key, post_extend, Comment


class PostPage(BlogHandler):
    def get(self, post_id):
        post = Post.get_by_id(int(post_id), parent=blog_key())
        if not post:
            self.error(404)
            return
        post = post_extend(post, self.user)
        post_comments = Comment.comments_for_post(post)
        self.render("permalink.html", p=post, user=self.user,
            post_comments=post_comments)


class CRUDPost(BlogHandler):
    def _update(self, op, subject=None, content=None, post_id=None):
        if self.user:
            if op == "new" or op == "update":
                if subject and content:
                    post = Post(parent=blog_key(), subject=subject,
                        content=content, user_ref=self.user.key())
                    if op == "update":
                        post = Post.get_by_id(int(post_id), parent=blog_key())
                        post.subject = subject
                        post.content = content
                    post.put()
                    self.redirect('/blog/%s' % str(post.key().id()))
                else:
                    error = "You should provide a subject, and "\
                            "a content for your post!"
                    self.render("newpost.html", content=content,
                        subject=subject, error=error)
            elif op == "delete":
                post = Post.get_by_id(int(post_id), parent=blog_key())
                Like.delete_likes_from(post=post)
                #TODO: Comment.delete_comments(post=post)
                post.delete()
                self.redirect('/blog/')
            else:
                error = "Invalid operation on post."
                self.render("newpost.html", content=content,
                    subject=subject, error=error)
        else:
            self.redirect("/login/")


class NewPost(CRUDPost):
    def get(self):
        self.render("newpost.html")

    def post(self):
        subject = self.request.get("subject")
        content = self.request.get("content")
        self._update("new", subject=subject, content=content)


class EditPost(CRUDPost):
    def get(self, post_id):
        post = Post.get_by_id(int(post_id), parent=blog_key())
        self.render("newpost.html", subject=post.subject, content=post.content,
            post_id=post_id)

    def post(self, post_id):
        subject = self.request.get("subject")
        content = self.request.get("content")
        self._update("update", subject=subject, content=content,
            post_id=post_id)


class DeletePost(CRUDPost):
    def post(self):
        post_id = self.request.get("post_id")
        self._update("delete", post_id=post_id)

        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps({"success": "OK"}))


class LikePost(BlogHandler):

    def post(self):
        if self.user:
            post_id = self.request.get("post_id")

            post = Post.get_by_id(int(post_id), parent=blog_key())
            result = Like.get_post_liked_by(post, self.user)
            if result:
                # it's a dislike
                result.delete()
            else:
                # it's a like
                lk = Like(user_ref=self.user.key(), post_ref=post.key())
                lk.put()
            self.response.headers['Content-Type'] = 'application/json'
            self.response.out.write(json.dumps({"success": "OK"}))
        else:
            self.redirect("/login/")

