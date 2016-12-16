import webapp2

from blogtronic.views import blog, post, admin, comments


blog_app = webapp2.WSGIApplication([
    ('/blog/?', blog.BlogFront),

    # Post CRUD
    ('/blog/([0-9]+)', post.PostPage),
    ('/blog/post/new/?', post.NewPost),
    ('/blog/post/edit/([0-9]+)', post.EditPost),
    ('/blog/post/delete/?', post.DeletePost),
    ('/blog/post/like/?', post.LikePost),

    # Blog admin
    ('/blog/admin/posts/?', admin.ListPosts),
    ('/blog/admin/likes/?', admin.ListLikes),

    # signup & login
    ('/signup/?', blog.Register),
    ('/login/?', blog.Login),
    ('/logout/?', blog.Logout),
    ('/welcome/?', blog.WelcomePage),

    ('/blog/comment/new/?', comments.NewComment),
    ('/blog/comment/edit/([0-9]+)/?', comments.EditComment),
    ('/blog/comment/delete/?', comments.DeleteComment),
], debug=True)
