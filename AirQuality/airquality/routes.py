from airquality.models import User, Post
from flask import request, Flask, render_template, url_for, flash, redirect
from airquality.forms import PostForm,RegisterationForm, LoginForm, UpdateAccountForm
from airquality import app, db, bcrypt
from flask_login import login_user, current_user, logout_user, login_required
import werkzeug
import secrets
import os
from PIL import Image
from random import randint
places = [
    {
        "name":"San Ramon",
        "years_lived":"Current",
        "start_year":"2012",
        "carbon":1.1,
        "end_year":None,
        "state":"success",
        "cend":"down",
        "data":[randint(1, 10) for i in range(13)],
        "id":"aewr2",
        "county":"Contra Costa County"
    },
    {
        "name":"San Diego",
        "years_lived":"2007 - 2010",
        "start_year":"2007",
        "carbon":1.2,
        "end_year":"2010",
        "state":"warning",
        "cend":"right",
        "id":"ae2wr2",
        "data":[randint(1, 10) for i in range(13)],
        "county":"San Diego County"
    },
    {
        "name":"San Fransico",
        "years_lived":"1919 - 2007",
        "start_year":"1919",
        "carbon":3,
        "end_year":"2007",
        "state":"danger",
        "cend":"up",
        "id":"ae99wr2",
        "data":[randint(1, 10) for i in range(13)],
        "county":"Contra Costa County"

    },
]
linecolors = {
    "success":"#2ec551",
    "warning":"#ffc107",
    "danger":"#dc3545"
}
fillcolors = {
    "success":"#8cffac",
    "warning":"#ffe88c",
    "danger":"#ff8c8c",
}

@app.errorhandler(404)
def handle_bad_request(e):
    return render_template('pages/404-page.html'), 404

@app.route("/dashboard")
@login_required
def dashboard():
    print(request.environ['REMOTE_ADDR'])
    image_file = url_for('static', filename=f'profile_pics/{current_user.image_file}')
    sparkline_charts = [generate_sparkline_script(place["id"], place["data"], fillcolor=fillcolors[place["state"]], linecolor=linecolors[place["state"]]) for place in places]
    script = finalize(*sparkline_charts)
    return render_template('/dashboard/index.html', current_user=current_user, image_file=image_file, script=script, places=places)

@app.route("/register", methods=["POST", "GET"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = RegisterationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Account created for {form.username.data}!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route("/login", methods=["POST", "GET"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return  redirect(next_page) if next_page else redirect(url_for('dashboard'))
        flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)
@app.route("/")
@app.route("/home")
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('about'))
@app.route("/about")
def about():
    if current_user.is_authenticated:
        image_file = url_for('static', filename=f'profile_pics/{current_user.image_file}')
        return render_template('about.html', title='About', image_file=image_file)
    else:
        return render_template('about.html', title='About')

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)

    i.save(picture_path)
    return picture_fn

@app.route("/account", methods=["POST", "GET"])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account', image_file=image_file, form=form)


@app.route("/post/new", methods=["POST", "GET"])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post', form=form)

def generate_sparkline_script(access, data, type='line', width='99.5',
                    height='100', linecolor='#5969ff', fillcolor='#dbdeff',
                    linewidth=2, spotcolor='undefined', minspotcolor='undefined',
                    maxspotcolor='undefined', highlightspotcolor='undefined',
                    highlightlinecolor='undefined', resize='true'):
    script = """
    // Generate sparkline chart
        $('#%s').sparkline(%s, {
        type: '%s',
        width: '%s%s',
        height: '%s',
        lineColor: '%s',
        fillColor: '%s',
        lineWidth: %s,
        spotColor: %s,
        minSpotColor: %s,
        maxSpotColor: %s,
        highlightSpotColor: %s,
        highlightLineColor: %s,
        resize: %s
    });
    """ % (access, data, type, width, '%', height, linecolor, fillcolor, linewidth, spotcolor, minspotcolor, maxspotcolor,
           highlightspotcolor, highlightlinecolor, resize)
    return script

def finalize(*inline):
    concat = ''
    for s in inline:
        concat += '\n' + s
    script = '''
    $(function(){
    "use strict";
    %s
    });
    ''' % concat
    return script
