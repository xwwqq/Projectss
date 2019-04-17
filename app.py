from flask import Flask,render_template,request,redirect,url_for,session
import config
from models import User,Question,Answer
from exts import db
from decorators import login_required
from sqlalchemy import or_
from werkzeug.utils import secure_filename
from flask import Flask,render_template,jsonify,request,send_from_directory
import time
import os
import base64
app = Flask(__name__)
app.config.from_object(config)
db.init_app(app)

UPLOAD_FOLDER='upload'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
basedir = os.path.abspath(os.path.dirname(__file__))
ALLOWED_EXTENSIONS = set(['pdf','jpg','png'])

@app.route('/')
def index():
    context = {
        'questions': Question.query.order_by('-create_time').all()
    }
    return render_template('index.html',**context)

@app.route('/login/',methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        email = request.form.get('email')
        password = request.form.get('password')


        user = User.query.filter(User.email == email,User.password==password).first()
        if user:
            session['user_id'] =user.id
            session.permanent =True
            return redirect(url_for('index'))
        else:
            return '邮箱或者密码输入错误，请确认后再输入'

@app.route('/regist/',methods=['GET','POST'])
def regist():
    if request.method == 'GET':
        return render_template('regist.html')
    else:
        email = request.form.get('email')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user =User.query.filter(User.email ==email).first()
        if user:
            return '邮箱已被注册，请更换邮箱号！'
        else:
            if password1 !=password2:
                return '两次密码不相等，请核对后在填写'
            else:
                user =User(email=email,password=password1)
                db.session.add(user)
                db.session.commit()
                return redirect(url_for('login'))
@app.route('/logout/')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/question/',methods=['GET','POST'])
@login_required
def question():
    if request.method =='GET':
        return render_template('question.html')
    else:
        title =request.form.get('title')
        content =request.form.get('content')
        question=Question(title=title,content=content)
        user_id =session.get('user_id')
        user =User.query.filter(User.id==user_id).first()
        question.author=user
        db.session.add(question)
        db.session.commit()
        return redirect(url_for('index'))

@app.route('/detail/<question_id>/')
def detail(question_id):
    question_model=Question.query.filter(Question.id==question_id).first()
    return render_template('detail.html',question=question_model)

@app.route('/add_answer/',methods=['POST'])
@login_required
def add_answer():
    content=request.form.get('answer_content')
    question_id =request.form.get('question_id')

    answer =Answer(content=content)
    user_id =session['user_id']
    user=User.query.filter(User.id==user_id).first()
    answer.author=user
    question=Question.query.filter(Question.id==question_id).first()
    answer.question=question
    db.session.add(answer)
    db.session.commit()
    return redirect(url_for('detail',question_id=question_id))


@app.route('/search/')
def searach():
    q=request.args.get('q')
    questions= Question.query.filter(or_(Question.title.contains(q),Question.content.contains(q))).order_by('-create_time')
    return render_template('index.html',questions=questions)
@app.context_processor
def my_context_processor():
    user_id =session.get('user_id')
    if user_id:
        user = User.query.filter(User.id == user_id).first()
        if user:
            return {'user':user}
    return {}

@app.route('/money/')
def money():
    return render_template('money.html')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1] in ALLOWED_EXTENSIONS

# 用于测试上传，稍后用到
@app.route('/wq/',methods=['GET'],strict_slashes=False)
def wq():
    return render_template('wq.html')

# 上传文件
@app.route('/wq/',methods=['POST'],strict_slashes=False)
def api_upload():
    file_dir = os.path.join(basedir, app.config['UPLOAD_FOLDER'])
    if not os.path.exists(file_dir):
        os.makedirs(file_dir)
    f = request.files['file']  # 从表单的file字段获取文件，file为该表单的name值

    if f and allowed_file(f.filename):  # 判断是否是允许上传的文件类型
        fname = secure_filename(f.filename)
        print(fname)
        ext = fname.rsplit('.',1)[1]  # 获取文件后缀
        unix_time = int(time.time())
        new_filename = str(unix_time)+'.'+ext  # 修改了上传的文件名
        #new_filename = '1'+'.'+ext  # 修改了上传的文件名
        f.save(os.path.join(file_dir,new_filename))  #保存文件到upload目录
        token = base64.b64encode(new_filename)
        print(token)

        return jsonify({"errno":0, "msg":"succeed ","token":token})
    else:
        return jsonify({"errno":1001, "errmsg":u"failed"})





if __name__ == '__main__':
    app.run()
