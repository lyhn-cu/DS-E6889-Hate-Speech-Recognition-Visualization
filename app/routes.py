from flask import render_template, flash, redirect, url_for, request, send_from_directory, jsonify
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from app import app, db
from app.forms import LoginForm, RegistrationForm
from app.models import User
import json
import time, datetime
from StreamProcesser import StreamProcesser
from StreamCreator import StreamCreator
import time
from threading import Thread
from DBFireBase import DBFireBase


next_port = 9001


@login_required
@app.route('/d3', methods=['GET'])
def d3():
    keyword = request.args.get('keyword')
    print(keyword)
    db = DBFireBase(keyword)
    words = db.get_word_cloud()
    while (not words):
        words = db.get_word_cloud()
    words = sorted(words.items(), key=lambda x: x[1], reverse=True)
    end = min(len(words), 200)
    words = words[0:end]
    w_c = []
    for word in words:
        w_c += [{"text":word[0], "size":2*word[1]}]
    res = {}
    res["words"] = w_c
    res["keyword"] = keyword
    res["list"] = words
    return render_template('d3.html', res=res)


@app.route('/refreshData', methods=['POST'])
def refreshData():
    keyword = request.form['keyword']
    db = DBFireBase(keyword)
    words = db.get_word_cloud()
    words = sorted(words.items(), key=lambda x: x[1], reverse=True)
    end = min(len(words), 200)
    words = words[0:end]
    # keyword_cnt = words[0]
    res = []
    res += [{"text":datetime.datetime.now(), "size":words[0][1]}]
    for word in words:
        res += [{"text":word[0], "size":2*word[1]}]
    # print(res[0][1])
    return jsonify(res)


@app.route('/assets/<path:path>')
def static_file(path):
    return send_from_directory('static/assets/', path)


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


@app.route("/introduction")
def introduction():
    return render_template('introduction.html')


@app.route("/test")
@login_required
def test():
    return render_template('test.html')


@app.route('/result', methods=['POST'])
@login_required
def result():
    global next_port
    keyword_dict = request.form
    kw = keyword_dict['keyword']

    def p1(input):
        sndr = StreamCreator()
        sndr.start(input[0], input[1])

    def p2(input):
        rcvr = StreamProcesser()
        rcvr.start(input[0], input[1])

    p1 = Thread(target=p1, args=([next_port, kw],))
    p1.start()
    time.sleep(1)
    p2 = Thread(target=p2, args=([next_port, kw],))
    p2.start()
    next_port += 1
    # time.sleep(5)
    return render_template('result.html', keyword=keyword_dict)


@app.route("/stats")
@login_required
def stats():
    keyword = request.args.get('keyword')
    db = DBFireBase(keyword)
    res = db.get_text_result(limit=200)
    return render_template('stats.html', res=res)


@app.route('/profile')
@login_required
def profile():
    return "", 204


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))
