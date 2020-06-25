from datetime import datetime
import hashlib
from flask import request
from flask_login import UserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from markdown import markdown
import bleach
from markdown import markdown
from coreyblog import db, app, login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username=db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True ,nullable=False)
    password=db.Column(db.String(60), nullable=False)
    image_file=db.Column(db.String(20), nullable=False, default='default.jpg')
    posts = db.relationship('Post', backref='author', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy='dynamic')

    def get_reset_token(self, expires_sec=1800):
        s=Serializer(app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    def gravatar(self, size=100, default='identicon', rating='g'):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        hash_ = hashlib.md5(self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash_}?s={size}&d={default}&r={rating}'.format(
                                                            url=url, 
                                                            hash_=hash_, 
                                                            size=size, 
                                                            default=default, 
                                                            rating=rating)
    
    @staticmethod 
    def verify_reset_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id=s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title=db.Column(db.String(100), nullable=False)
    date_posted=db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content=db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    body_html = db.Column(db.Text)
    comments = db.relationship('Comment', backref='post', lazy=True)

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p']
        target.body_html = bleach.linkify(bleach.clean(
                                    markdown(value, 
                                            output_format='html'),
                                    tags=allowed_tags, 
                                    strip=True))


    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"

db.event.listen(Post.content, 'set', Post.on_changed_body)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_posted=db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content=db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id=db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    body_html = db.Column(db.Text)

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p']
        target.body_html = bleach.linkify(bleach.clean(
                                    markdown(value, 
                                            output_format='html'),
                                    tags=allowed_tags, 
                                    strip=True))


    def __repr__(self):
        return f"Comment('{self.author.username}', {self.post.title}, '{self.date_posted}')"
db.event.listen(Comment.content, 'set', Comment.on_changed_body)
