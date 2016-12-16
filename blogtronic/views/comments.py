import json

from blogtronic.views.base import BlogHandler
from blogtronic.models import Comment, Post, blog_key


class CRUDComment(BlogHandler):

    def _update(self, op, comment=None, post_id=None, comment_id=None):
        if self.user:
            if op == "new" or op == "update":
                if comment:
                    if op == "new":
                        post = Post.get_by_id(int(post_id), parent=blog_key())
                        cm = Comment(comment=comment, user_ref=self.user.key(),
                            post_ref=post.key())
                    else:
                        cm = Comment.get_by_id(int(comment_id))
                        post = cm.post_ref
                        cm.comment = comment
                    cm.put()
                self.redirect("/blog/%s" % post.key().id())
            elif op == "delete":
                comment = Comment.get_by_id(int(comment_id))
                comment.delete()
                self.response.headers['Content-Type'] = 'application/json'
                self.response.out.write(json.dumps({"status": "OK"}))
            else:
                self.response.headers['Content-Type'] = 'application/json'
                self.response.out.write(json.dumps({"status": "error"}))
        else:
            self.redirect("/login/")


class NewComment(CRUDComment):
    def get(self):
        self.render("comment.html")

    def post(self):
        post_id = self.request.get("post_id")
        comment = self.request.get("comment")
        self._update("new", comment=comment, post_id=post_id)


class EditComment(CRUDComment):
    def get(self, comment_id):
        comment = Comment.get_by_id(int(comment_id))
        self.render("comment.html", comment=comment.comment,
            comment_id=comment_id)

    def post(self, comment_id):
        comment = self.request.get("comment")
        comment_id = comment_id or self.request.get("comment_id")
        self._update("update", comment=comment, comment_id=comment_id)


class DeleteComment(CRUDComment):
    def post(self):
        comment_id = self.request.get("comment_id")
        self._update("delete", comment_id=comment_id)
