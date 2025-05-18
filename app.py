from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_migrate import Migrate
import os
import sys
import re
from datetime import datetime, date

# Добавляем путь к директории Praktika в PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
summer_practic_dir = os.path.join(current_dir, 'Praktika')
sys.path.append(summer_practic_dir)

# Импорт app и db из config.py
from config import app, db, User, WorkType, Order, Mechanic

# Инициализация Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Инициализация Flask-Migrate
migrate = Migrate(app, db)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Создание контекста приложения
app.app_context().push()

# Создание всех таблиц в базе данных
db.create_all()

# Создание первого администратора, если его еще нет
with app.app_context():
    if not User.query.filter_by(role='admin').first():
        admin = User(
            username='admin',
            date_of_birth=date(1990, 1, 1),
            gender='male',
            role='admin',
            phone='1234567890',
            email='admin@example.com'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Первый администратор создан: username=admin, password=admin123")

# Добавление видов работ, если их еще нет
with app.app_context():
    if not WorkType.query.first():
        work_types = [
            WorkType(name="Ремонт двигателя",
                     description="Полный ремонт двигателя автомобиля, включая замену деталей и диагностику."),
            WorkType(name="Покраска кузова",
                     description="Качественная покраска кузова автомобиля с использованием современных материалов."),
            WorkType(name="Замена шин", description="Сезонная замена шин, балансировка и проверка давления."),
            WorkType(name="Диагностика электроники", description="Проверка и ремонт электронных систем автомобиля.")
        ]
        db.session.add_all(work_types)
        db.session.commit()
        print("Виды работ добавлены в базу данных")

# Добавление исполнителей, если их еще нет
with app.app_context():
    if not Mechanic.query.first():
        mechanics = [
            Mechanic(name="Иван Иванов", phone="1234567890", specialization="Ремонт двигателей"),
            Mechanic(name="Петр Петров", phone="0987654321", specialization="Покраска кузова"),
            Mechanic(name="Алексей Сидоров", phone="1112223334", specialization="Диагностика электроники")
        ]
        db.session.add_all(mechanics)
        db.session.commit()
        print("Исполнители добавлены в базу данных")


@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        date_of_birth = request.form['date_of_birth']
        gender = request.form['gender']
        phone = request.form.get('phone', '')
        email = request.form.get('email', '')

        if len(username) < 3:
            flash('Имя пользователя должно содержать минимум 3 символа!', 'error')
            return redirect(url_for('register'))
        if len(password) < 6:
            flash('Пароль должен содержать минимум 6 символов!', 'error')
            return redirect(url_for('register'))
        if User.query.filter_by(username=username).first():
            flash('Пользователь с таким именем уже существует!', 'error')
            return redirect(url_for('register'))
        if User.query.filter_by(email=email).first() and email:
            flash('Пользователь с таким email уже существует!', 'error')
            return redirect(url_for('register'))

        try:
            dob = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
            if (date.today() - dob).days < 18 * 365:
                flash('Вам должно быть не менее 18 лет!', 'error')
                return redirect(url_for('register'))
        except ValueError:
            flash('Неверный формат даты! Используйте YYYY-MM-DD.', 'error')
            return redirect(url_for('register'))

        if gender not in ['male', 'female', 'other']:
            flash('Неверное значение пола!', 'error')
            return redirect(url_for('register'))

        if phone and not re.match(r'^\d{10}$', phone):
            flash('Номер телефона должен содержать ровно 10 цифр!', 'error')
            return redirect(url_for('register'))

        if email and not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            flash('Неверный формат email!', 'error')
            return redirect(url_for('register'))

        user = User(
            username=username,
            date_of_birth=dob,
            gender=gender,
            role='user',
            phone=phone if phone else None,
            email=email if email else None
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Регистрация прошла успешно! Теперь вы можете войти.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Вы успешно вошли!', 'success')
            return redirect(url_for('profile'))
        else:
            flash('Неверное имя пользователя или пароль!', 'error')
    return render_template('login.html')


@app.route("/profile")
@login_required
def profile():
    orders = Order.query.filter_by(user_id=current_user.id).all()
    return render_template('profile.html', user=current_user, orders=orders)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash('Вы вышли из аккаунта!', 'success')
    return redirect(url_for('index'))


@app.route("/users")
@login_required
def users():
    if not current_user.is_admin():
        flash('Доступ запрещен! Только администраторы могут управлять пользователями.', 'error')
        return redirect(url_for('profile'))
    users = User.query.all()
    return render_template('users.html', users=users)


@app.route("/edit_user/<int:id>", methods=['GET', 'POST'])
@login_required
def edit_user(id):
    if not current_user.is_admin():
        flash('Доступ запрещен! Только администраторы могут редактировать пользователей.', 'error')
        return redirect(url_for('profile'))

    user = User.query.get_or_404(id)
    if request.method == 'POST':
        user.username = request.form['username']
        user.date_of_birth = datetime.strptime(request.form['date_of_birth'], '%Y-%m-%d').date()
        user.gender = request.form['gender']
        user.role = request.form['role']
        user.phone = request.form.get('phone', None)
        user.email = request.form.get('email', None)
        if 'password' in request.form and request.form['password']:
            user.set_password(request.form['password'])
        try:
            db.session.commit()
            flash('Пользователь успешно обновлен!', 'success')
            return redirect(url_for('users'))
        except:
            flash('Ошибка при обновлении пользователя!', 'error')
    return render_template('edit_user.html', user=user)


@app.route("/delete_user/<int:id>")
@login_required
def delete_user(id):
    if not current_user.is_admin():
        flash('Доступ запрещен! Только администраторы могут удалять пользователей.', 'error')
        return redirect(url_for('profile'))

    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('Нельзя удалить самого себя!', 'error')
        return redirect(url_for('users'))
    try:
        # Удаляем все заказы пользователя
        Order.query.filter_by(user_id=user.id).delete()
        db.session.delete(user)
        db.session.commit()
        flash('Пользователь и все его заказы успешно удалены!', 'success')
    except Exception as e:
        flash(f'Ошибка при удалении пользователя: {str(e)}', 'error')
    return redirect(url_for('users'))


@app.route("/work_types")
@login_required
def work_types():
    if not current_user.is_admin():
        flash('Доступ запрещен! Только администраторы могут управлять видами работ.', 'error')
        return redirect(url_for('profile'))
    work_types = WorkType.query.all()
    return render_template('work_types.html', work_types=work_types)


@app.route("/add_work_type", methods=['GET', 'POST'])
@login_required
def add_work_type():
    if not current_user.is_admin():
        flash('Доступ запрещен! Только администраторы могут добавлять виды работ.', 'error')
        return redirect(url_for('profile'))

    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')
        if not name:
            flash('Название вида работы обязательно!', 'error')
            return redirect(url_for('add_work_type'))

        work_type = WorkType(name=name, description=description)
        db.session.add(work_type)
        db.session.commit()
        flash('Вид работы успешно добавлен!', 'success')
        return redirect(url_for('work_types'))
    return render_template('add_work_type.html')


@app.route("/edit_work_type/<int:id>", methods=['GET', 'POST'])
@login_required
def edit_work_type(id):
    if not current_user.is_admin():
        flash('Доступ запрещен! Только администраторы могут редактировать виды работ.', 'error')
        return redirect(url_for('profile'))

    work_type = WorkType.query.get_or_404(id)
    if request.method == 'POST':
        work_type.name = request.form['name']
        work_type.description = request.form.get('description', '')
        if not work_type.name:
            flash('Название вида работы обязательно!', 'error')
            return redirect(url_for('edit_work_type', id=work_type.id))
        try:
            db.session.commit()
            flash('Вид работы успешно обновлен!', 'success')
            return redirect(url_for('work_types'))
        except:
            flash('Ошибка при обновлении вида работы!', 'error')
    return render_template('edit_work_type.html', work_type=work_type)


@app.route("/delete_work_type/<int:id>")
@login_required
def delete_work_type(id):
    if not current_user.is_admin():
        flash('Доступ запрещен! Только администраторы могут удалять виды работ.', 'error')
        return redirect(url_for('profile'))

    work_type = WorkType.query.get_or_404(id)
    try:
        db.session.delete(work_type)
        db.session.commit()
        flash('Вид работы успешно удален!', 'success')
    except:
        flash('Ошибка при удалении вида работы! Возможно, он используется в заказах.', 'error')
    return redirect(url_for('work_types'))


@app.route("/create_order/<int:work_type_id>", methods=['POST'])
@login_required
def create_order(work_type_id):
    work_type = WorkType.query.get_or_404(work_type_id)
    order = Order(user_id=current_user.id, work_type_id=work_type.id)
    db.session.add(order)
    db.session.commit()
    flash('Заказ успешно создан!', 'success')
    return redirect(url_for('profile'))


@app.route("/pay_order/<int:order_id>", methods=['GET', 'POST'])
@login_required
def pay_order(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash('Доступ запрещен! Это не ваш заказ.', 'error')
        return redirect(url_for('profile'))

    if request.method == 'POST':
        card_number = request.form['card_number']
        expiry_date = request.form['expiry_date']
        cvv = request.form['cvv']

        if not re.match(r'^\d{16}$', card_number):
            flash('Номер карты должен содержать 16 цифр!', 'error')
            return redirect(url_for('pay_order', order_id=order.id))
        try:
            datetime.strptime(expiry_date, '%m/%y')
        except ValueError:
            flash('Неверный формат даты истечения срока! Используйте MM/YY.', 'error')
            return redirect(url_for('pay_order', order_id=order.id))
        if not re.match(r'^\d{3}$', cvv):
            flash('CVV должен содержать 3 цифры!', 'error')
            return redirect(url_for('pay_order', order_id=order.id))

        order.is_paid = True
        db.session.commit()
        flash('Заказ успешно оплачен!', 'success')
        return redirect(url_for('profile'))

    return render_template('pay_order.html', order=order)


@app.route("/mechanics")
@login_required
def mechanics():
    if not current_user.is_admin():
        flash('Доступ запрещен! Только администраторы могут управлять исполнителями.', 'error')
        return redirect(url_for('profile'))
    mechanics = Mechanic.query.all()
    return render_template('mechanics.html', mechanics=mechanics)


@app.route("/add_mechanic", methods=['GET', 'POST'])
@login_required
def add_mechanic():
    if not current_user.is_admin():
        flash('Доступ запрещен! Только администраторы могут добавлять исполнителей.', 'error')
        return redirect(url_for('profile'))

    if request.method == 'POST':
        name = request.form['name']
        phone = request.form.get('phone', '')
        specialization = request.form.get('specialization', '')
        if not name:
            flash('Имя исполнителя обязательно!', 'error')
            return redirect(url_for('add_mechanic'))
        if phone and not re.match(r'^\d{10}$', phone):
            flash('Номер телефона должен содержать ровно 10 цифр!', 'error')
            return redirect(url_for('add_mechanic'))

        mechanic = Mechanic(name=name, phone=phone if phone else None, specialization=specialization)
        db.session.add(mechanic)
        db.session.commit()
        flash('Исполнитель успешно добавлен!', 'success')
        return redirect(url_for('mechanics'))
    return render_template('add_mechanic.html')


@app.route("/edit_mechanic/<int:id>", methods=['GET', 'POST'])
@login_required
def edit_mechanic(id):
    if not current_user.is_admin():
        flash('Доступ запрещен! Только администраторы могут редактировать исполнителей.', 'error')
        return redirect(url_for('profile'))

    mechanic = Mechanic.query.get_or_404(id)
    if request.method == 'POST':
        mechanic.name = request.form['name']
        mechanic.phone = request.form.get('phone', None)
        mechanic.specialization = request.form.get('specialization', '')
        if not mechanic.name:
            flash('Имя исполнителя обязательно!', 'error')
            return redirect(url_for('edit_mechanic', id=mechanic.id))
        if mechanic.phone and not re.match(r'^\d{10}$', mechanic.phone):
            flash('Номер телефона должен содержать ровно 10 цифр!', 'error')
            return redirect(url_for('edit_mechanic', id=mechanic.id))
        try:
            db.session.commit()
            flash('Исполнитель успешно обновлен!', 'success')
            return redirect(url_for('mechanics'))
        except:
            flash('Ошибка при обновлении исполнителя!', 'error')
    return render_template('edit_mechanic.html', mechanic=mechanic)


@app.route("/delete_mechanic/<int:id>")
@login_required
def delete_mechanic(id):
    if not current_user.is_admin():
        flash('Доступ запрещен! Только администраторы могут удалять исполнителей.', 'error')
        return redirect(url_for('profile'))

    mechanic = Mechanic.query.get_or_404(id)
    try:
        db.session.delete(mechanic)
        db.session.commit()
        flash('Исполнитель успешно удален!', 'success')
    except:
        flash('Ошибка при удалении исполнителя!', 'error')
    return redirect(url_for('mechanics'))


@app.route("/index")
@app.route("/")
def index():
    work_types = WorkType.query.all()
    mechanics = Mechanic.query.all()  # Добавляем список исполнителей
    return render_template('index.html', work_types=work_types, mechanics=mechanics)


@app.route("/about")
def about():
    return render_template('about.html')


if __name__ == '__main__':
    app.run(debug=True)