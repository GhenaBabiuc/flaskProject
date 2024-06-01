from flask import render_template, url_for, flash, redirect, request
from app import app, db, bcrypt
from app.forms import RegistrationForm, LoginForm, PostForm, CommentForm, WeatherForm, SurveyForm, VoteForm
from app.models import User, Post, Comment, Survey, Option
from flask_login import login_user, current_user, logout_user, login_required
import requests


@app.route("/")
@app.route("/home")
def home():
    posts = Post.query.all()
    return render_template('home.html', posts=posts)


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post', form=form, legend='New Post')


@app.route("/post/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id)
    form = CommentForm()
    return render_template('post.html', title=post.title, post=post, form=form)


@app.route("/post/<int:post_id>/comment", methods=['POST'])
@login_required
def comment_post(post_id):
    post = Post.query.get_or_404(post_id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(content=form.content.data, author=current_user, post=post)
        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been added!', 'success')
    return redirect(url_for('post', post_id=post.id))


@app.route("/weather", methods=['GET', 'POST'])
def weather():
    form = WeatherForm()
    weather_data = None
    if form.validate_on_submit():
        city = form.city.data
        api_key = 'XW9QXP69NNUQGKUFMY6CFV4W8'
        weather_url = f'https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{city}?unitGroup=metric&key={api_key}&contentType=json'
        response = requests.get(weather_url).json()

        if 'days' in response:
            weather_data = {
                'city': city,
                'temperature': response['days'][0]['temp'],  # Example data
                'description': response['days'][0]['description'],  # Example data
            }
        else:
            flash('City not found or API error!', 'danger')
    return render_template('weather.html', title='Weather', form=form, weather_data=weather_data)


@app.route("/survey/new", methods=['GET', 'POST'])
@login_required
def new_survey():
    form = SurveyForm()
    if form.validate_on_submit():
        options = [opt.strip() for opt in form.options.data.split('\n') if opt.strip()]
        survey = Survey(question=form.question.data)
        db.session.add(survey)
        db.session.commit()
        for opt in options:
            option = Option(option_text=opt, survey=survey)
            db.session.add(option)
        db.session.commit()
        flash('Your survey has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('survey.html', title='New Survey', form=form, legend='New Survey')


@app.route("/surveys")
def surveys():
    surveys = Survey.query.all()
    return render_template('surveys.html', surveys=surveys)


@app.route("/survey/<int:survey_id>", methods=['GET', 'POST'])
def survey(survey_id):
    survey = Survey.query.get_or_404(survey_id)
    form = VoteForm()
    form.option.choices = [(opt.id, opt.option_text) for opt in survey.options]
    if form.validate_on_submit():
        option = Option.query.get(form.option.data)
        option.votes += 1
        db.session.commit()
        flash('Your vote has been counted!', 'success')
        return redirect(url_for('survey', survey_id=survey.id))
    return render_template('survey_vote.html', title=survey.question, survey=survey, form=form)
