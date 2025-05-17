from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
import sys
import os

# Добавляем путь к директории Praktika в PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
summer_practic_dir = os.path.join(current_dir, 'Praktika')
sys.path.append(summer_practic_dir)

# Импорт app и db из config.py
from config import app, db

# Также импортируем класс Post
from config import Post

# Создание контекста приложения
app.app_context().push()

# Создание всех таблиц в базе данных
db.create_all()

@app.route("/index")  # получаем доступ к главной странице
@app.route("/")
def index():
    return render_template('index.html')

@app.route("/posts")
def posts():
    posts = Post.query.all()
    return render_template('posts.html', posts=posts)

@app.route("/create", methods=['POST', 'GET'])
def create():
    if request.method == 'POST':
        title = request.form['title']
        text = request.form['text']

        post = Post(title=title, text=text)

        try:
            db.session.add(post)
            db.session.commit()
            return redirect('/')
        except:
            return 'При добавлении статьи произошла ошибка!'
        return redirect('/')
    else:
        return render_template('create.html')

@app.route("/about")
def about():
    return render_template('about.html')

if __name__ == '__main__':
    app.run(debug=True)