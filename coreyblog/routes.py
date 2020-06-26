import secrets, os, datetime
from flask import (
    render_template, url_for, 
    flash, redirect, request, abort)
from werkzeug.security import (
    generate_password_hash, check_password_hash)
from coreyblog import app, db, mail
from coreyblog.models import User, Post, Comment
from coreyblog.forms import (LoginForm,
    RegistrationForm, ResetPasswordForm,
    UpdateAccountForm, PostForm, 
    UpdatePostForm, RequestResetForm,
    CommentForm)
from flask_login import (
    login_user, logout_user, 
    current_user, login_required)
from flask_mail import Message

@app.route('/')
@app.route('/home/')
def home():
    page = request.args.get('page', 1, type=int)
    all_posts = Post.query.order_by(Post.date_posted.desc()).\
                                    paginate(page=page, per_page=2)
    return render_template('home.html', 
                            all_posts=all_posts)

@app.route('/about/')
def about():
    return render_template('about.html', 
                            title='About')

@app.errorhandler(403)
def internal_server_error(error):
    return render_template('error.html', 
                            title='Server error',
                            error1="Forbidden (403)",
                            error2="You don't have the permission to access the requested resource. It is either read-protected or not readable by the server."), 403

@app.errorhandler(404)
def page_not_found(error):
    return render_template('error.html', 
                            title='Page not found',
                            error1="Page not found (404)",
                            error2="The requested URL was not found on our server. If you entered the URL manually please check your spelling and try again.", error=404), 404

@app.errorhandler(500)
def internal_server_error2(error):
    return render_template('error.html', 
                            title='Error',
                            error1="Something went wrong(500)",
                            error2="We're experiencing  some trouble on our end, please try again"), 500

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password=generate_password_hash(form.password.data)
        user = User(username=form.username.data, 
                    email=form.email.data, 
                    password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Account has been created! You can now login', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', 
                            form=form, 
                            title='Register')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page=request.args.get('next')
            flash('Login was successful', 'success')
            return redirect(next_page) if next_page else  redirect(url_for('home'))
        flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', 
                            form=form, 
                            title='Login')
 

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

def save_pic(picture):
    from PIL import Image
    file_name = secrets.token_hex(8) +os.path.splitext(picture.filename)[1]
    file_path = os.path.join(app.root_path, 'static/img', file_name)
    picture = Image.open(picture)
    picture.thumbnail((150, 150))
    picture.save(file_path)
    return file_name

@app.route('/profile/', methods=['GET', 'POST'])
@login_required
def account():
    page = request.args.get('page', 1, type=int)
    all_posts = Post.query.filter_by(author=current_user).\
                                    order_by(Post.date_posted.desc()).\
                                        paginate(page=page, per_page=2)
    return render_template('account.html', 
                            title='Profile',  
                            all_posts=all_posts)

@app.route('/profile/update', methods=['GET', 'POST'])
@login_required
def updateaccount():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            pic_file = save_pic(form.picture.data)
            current_user.image_file = pic_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    else:
        pass
    return render_template('updateaccount.html', 
                            title='Update Account',
                            form=form)
    

@app.route('/post/new', methods=['GET', 'POST'])
@login_required
def newpost():
    form=PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, 
                    content=form.content.data, 
                    user_id=current_user.id)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created', 'success')
        return redirect(url_for('home'))
    return render_template('newpost.html', 
                            form=form, 
                            title='Create Post')

@app.route('/post/delete/<int:id>', methods=['DELETE', 'GET'])
@login_required
def delete(id):
    if current_user.id==Post.query.get_or_404(id).author.id:
        db.session.delete(Post.query.get_or_404(id))
        db.session.commit()
        flash('Your post has been successfully deleted', 'success')
        return redirect(url_for('home'))
    abort(403)

@app.route('/comment/delete/<int:id>', methods=['DELETE', 'GET'])
@login_required
def delete_comment(id):
    if current_user.id==Comment.query.get_or_404(id).author.id:
        db.session.delete(Comment.query.get_or_404(id))
        db.session.commit()
        flash('Your comment has been successfully deleted', 'success')
        return redirect(url_for('home'))
    abort(403)

@app.route('/post/update/<int:id>', methods=['GET', 'POST'])
@login_required
def updatepost(id):
    form = UpdatePostForm()
    post = Post.query.get_or_404(id)
    if current_user != post.author:
        return  abort(403)
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        post.date_posted=datetime.datetime.utcnow()
        db.session.commit()
        flash('Your post has been updated', 'success')
        return redirect(url_for('viewblog', 
                                id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    else:
        pass
    return render_template('updatepost.html', 
                            title='Update Post', 
                            form=form)

@app.route('/post/best/')
def best_post():
    best = Post.query.first_or_404()
    for post in Post.query.all():
        if len(post.comments) > len(best.comments):
            best=post
    return redirect(url_for('viewblog', id=best.id))

@app.route('/profile/best')
def best_author():
    win = User.query.first()
    for user in User.query.all():
        if len(user.posts) > len(win.posts): 
                win = user
    return redirect(url_for('profile', user=win.username))


@app.route('/profile/<user>')
def profile(user):
    user_=User.query.filter_by(username=user).first_or_404()
    if user_ == current_user: 
        return redirect(url_for('account')) 
    page = request.args.get('page', 1, type=int)
    all_posts = Post.query.filter_by(author=user_).\
                                    order_by(Post.date_posted.desc()).\
                                    paginate(page=page, per_page=2)
    return render_template('profile.html', 
                            user_=user_, 
                            all_posts=all_posts, 
                            title=f'Profile {user}')

@app.route('/post/view/<int:id>', methods=['GET', 'POST'])
def viewblog(id):
    blog=Post.query.get_or_404(id)
    form=CommentForm()
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash('You need to be logged in to comment')
            next_page=request.args.get('next') or f'post/view/{title}'
            return redirect(url_for('login', next=next_page))
        else:
            comment = Comment(content=form.body.data,
                                post=blog,
                                user_id=current_user.id)
            db.session.add(comment)
            db.session.commit()
            flash('You comment has been successfully added')
            return redirect(url_for('viewblog', id=blog.id))
    page = request.args.get('page', 1, type=int)
    per_page=3
    if page == -1:
        page = (blog.comments.count() - 1) / per_page+ 1
    blog_comments=Comment.query.filter_by(post=blog)
    pagination = blog_comments.paginate(
                                        page, per_page=per_page,
                                        error_out=False)
    count=blog_comments.count()
    comments = pagination.items
    return render_template('viewblog.html', 
                            blog=blog,
                            count=count,
                            form=form,
                            pagination=pagination,
                            comments=comments)

def send_reset_email(user):
    token = user.get_reset_token()
    body = f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}

If you did not make this request then simply ignore this email.
Do not reply this mail.
'''
    msg = Message(subject='Password Reset Request', 
                sender='admin@demo.com',
                body=body,
                recipients=[user.email])
    mail.send(msg)


@app.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        token=user.get_reset_token()
        send_reset_email(user)
        flash('An email has been sent to you with instructions to resetting your password', 'info')
    return render_template('reset_request.html', 
                            title='Reset Password',
                            form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('Token is invalid or has expired', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password=generate_password_hash(form.password.data)
        user.password=hashed_password
        db.session.commit()
        flash(f'Password has been updated! You can now login', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', 
                            title='Reset Password',
                            form=form)

