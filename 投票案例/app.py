from datetime import datetime, timedelta
from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired
from flask import Flask, request, render_template, redirect, session
from flask_sqlalchemy import SQLAlchemy
from pytz import timezone
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql
import re

pymysql.install_as_MySQLdb()

app = Flask(__name__, static_folder='static', static_url_path='/static')

class Config():
    DEBUG = True
    USER = 'root'
    PSW = "situyifeng1085"
    HOST = "localhost"
    PORT = 3306
    DB_NAME = 'vote_for_movie'
    TIMEZONE = 'Asia/Shanghai'
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{USER}:{PSW}@{HOST}:{PORT}/{DB_NAME}"
    app.config["SECRET_KEY"] = 'SNCNJSS29njn71'

app.config.from_object(Config)
db = SQLAlchemy(app)

class MSG(FlaskForm):
    content = TextAreaField(label="留言", validators=[DataRequired("不允许为空")])
    submit = SubmitField(label="提交")
    time = db.Column(db.DateTime, default=lambda: datetime.now(timezone('Asia/Shanghai')))

class Movie(db.Model):
    """电影类型表"""
    __tablename__ = "Movie"
    # id主键
    id = db.Column(db.Integer, primary_key=True)
    # 电影名称
    name = db.Column(db.String(20), unique=True)
    # 演员列表
    cast = db.Column(db.String(20))
    # 票数
    votes = db.Column(db.Integer, default=0)
    # 图片文件名
    pic = db.Column(db.String(100))  # 假设图片文件名不超过100个字符

class Message(db.Model):
    __tablename__ = 'Message'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    content = db.Column(db.String(500), nullable=False)
    time = db.Column(db.DateTime, default=lambda: datetime.now(timezone('Asia/Shanghai')))

class User(db.Model):
    """用户表"""
    __tablename__ = "user"
    # 用户账号
    root = db.Column(db.String(12), primary_key=True)
    # 用户账号密码
    psw = db.Column(db.String(12))

@app.route('/', methods=["GET", "POST"])
def index():
    form = MSG()
    m_all = Movie.query.all()
    msg = Message.query.all()#获取所有留言
    context = {
        "form": form,
        "m_all": m_all,
        "msg":msg,
    }
    if request.method == "GET":
        return render_template('vote.html', **context)
    elif request.method == "POST":
        #处理留言
        if form.validate_on_submit():
            content = form.content.data
            m = Message()
            m.content = content
            db.session.add(m)
            db.session.commit()
            return redirect("/")
        else:
            print(form.errors)
            return render_template('vote.html', **context)

@app.route('/add_vote')
def add_vote():
    if 'user' in session:
        if not session.get("vote?"):
            m_id = request.args.get("id")
            if m_id:
                try:
                    m_id = int(m_id)
                    m = Movie.query.get(m_id)
                    if m:
                        m.votes += 1
                        db.session.add(m)
                        db.session.commit()
                        session.permanent = True
                        app.permanent_session_lifetime = timedelta(seconds=10)
                        session["vote?"] = "vote"
                except ValueError:
                    pass
    else:
        return redirect('/login')
    return redirect("/")

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        root = request.form.get('root')
        psw = request.form.get('psw')
        user = User.query.filter_by(root=root, psw=psw).first()
        if user:
            session['user'] = root
            session.permanent = True
            app.permanent_session_lifetime = timedelta(days=1)
            return redirect('/')
        else:
            error = '账号或密码错误，请重新输入。'
    return render_template('login.html', error=error)


@app.route('/Register', methods=['GET', 'POST'])
def Register():
    error = None
    Tip = '长度在8~12位，且同时包含数字与字母，字母至少包含一个大写与小写字母。'

    if request.method == 'POST':
        root = request.form.get('root')
        psw = request.form.get('psw')
        check_psw = request.form.get('check_psw')

        # 检查用户名是否已存在
        user = User.query.filter_by(root=root).first()
        if user:
            error = '该用户名已被注册,换个别的吧。'
        elif not (psw == check_psw):
            error = '密码与确认密码不一致'
        elif not (8 <= len(psw) <= 12):
            error = '密码长度应在8~12之间'
        elif not re.search(r'[A-Z]', psw):
            error = '密码应包含至少一个大写字母。'
        elif not re.search(r'[a-z]', psw):
            error = '密码应包含至少一个小写字母'
        elif not re.search(r'\d', psw):
            error = '密码应包含至少一个数字'

        # 如果有任何验证失败，返回错误信息
        if error:
            return render_template('Register.html', error=error, Tip=Tip)

        # 所有验证通过，创建新用户
        try:
            new_user = User(
                root=root,
                psw=generate_password_hash(psw)  # 使用哈希存储密码
            )
            db.session.add(new_user)
            db.session.commit()
            success = '注册成功! 请登录'
            return render_template('login.html', error=success)
        except Exception as e:
            db.session.rollback()  # 回滚会话
            error = '注册失败，请重试'
            print(f"注册错误: {e}")
            return render_template('Register.html', error=error, Tip=Tip)

    # GET 请求直接显示注册页面
    return render_template('Register.html', Tip=Tip)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0')
