from flask import Flask,flash,redirect,render_template,url_for,request,jsonify,session,abort
from flask_session import Session
from flask_mysqldb import MySQL
from datetime import date
from datetime import datetime
import stripe
from itsdangerous import URLSafeTimedSerializer

stripe.api_key = "sk_test_51MMsHhSGj898WTbYXSx509gD14lhhXs8Hx8ipwegdytPB1Bkw0lJykMB0yGpCux95bdw1Gk9Gb9nJIWzPEEDxSqf00GEtCqZ8Y"
app=Flask(__name__)
app.secret_key='hello'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['MYSQL_HOST'] ='localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD']='admin'
app.config['MYSQL_DB']='food'
mysql=MySQL(app)
Session(app)
@app.route('/')
def welcome():
    return render_template('welcome.html')
@app.route('/welcome',methods=['GET','POST'])
def login():
    if session.get('name'):
        return redirect(url_for('home',id1=session['name']))
    if request.method=="POST":
        print(request.form)
        user=request.form['user']
        cursor=mysql.connection.cursor()
        cursor.execute('SELECT number from signup')
        users=cursor.fetchall()
        password=request.form['password']
        cursor.execute('select password from signup where number=%s',[user])
        data=cursor.fetchone()
        cursor.close()
        if (int(user),) in users:
            if password==data[0]:
                session['name']=user
                session['cart']={}
                return redirect(url_for('home'))
            else:
                flash('Invalid Password')
                return render_template('loginpage.html')
        else:
            flash('Invalid user id')
            return render_template('loginpage.html')      
    return render_template('loginpage.html')
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        number = request.form['number']
        gender = request.form['gender']
        password = request.form['password']
        email = request.form['email']
        cursor = mysql.connection.cursor()
        cursor.execute('select count(*) from signup where name=%s', [name])
        count = cursor.fetchone()[0]
        cursor.execute('select count(*) from signup where email=%s', [email])
        count1 = cursor.fetchone()[0]
        if count == 1:
            flash('username already in use')
            return render_template('signuppage.html')
        elif count1 == 1:
            flash('Email already in use')
            return render_template('signuppage.html')
        else:
            cursor.execute('INSERT INTO signup (name, number, gender, password, email) VALUES (%s, %s, %s, %s, %s)', 
                           (name, number, gender, password, email))
            mysql.connection.commit()
            cursor.close()
            flash('Registration successful')
            return render_template('welcome.html')  # or redirect to a welcome page
    return render_template('signuppage.html')




@app.route('/homepage')
def home():
    if session.get('name'):
        return render_template('mainPage.html')
    return redirect(url_for('login'))
@app.route('/nonveg')
def nonveg():
    if session.get('name'):
        return render_template('nonVegBiryaniPage.html')
    return redirect(url_for('login'))
@app.route('/veg')
def veg():
    if session.get('name'):
        return render_template('vegPage.html')
    return redirect(url_for('login'))
@app.route('/desserts')
def desserts():
    if session.get('name'):
        return render_template('dessertsPage.html')
    return redirect(url_for('login'))
@app.route('/mainpage')
def homepagemain():
    if session.get('name'):
        return render_template('menuPage.html')
    return redirect(url_for('login'))
@app.post('/pay/<item>/<int:price>')
def pay(item,price):
    id1=session.get('name')
    qty=request.form['quantity']
    checkout_session=stripe.checkout.Session.create(
        success_url=request.host_url+url_for('success_pay',id1=id1,item=item,qty=qty,price=int(qty)*price),
        line_items=[
            {
                'price_data': {
                    'product_data': {
                        'name': item,
                    },
                    'unit_amount': price*100,
                    'currency': 'inr',
                },
                'quantity': qty,
            },
            ],
        mode="payment",)
    return redirect(checkout_session.url)
@app.route('/successpay/<id1>/<item>/<price>/<qty>')
def success_pay(id1,item,price,qty):
    today=date.today()
    day=today.day
    month=today.month
    year=today.year
    today_date=datetime.strptime(f'{year}-{month}-{day}','%Y-%m-%d')
    date_today=datetime.strftime(today_date,'%Y-%m-%d')
    cursor=mysql.connection.cursor()
    cursor.execute('insert into orders(mobile_no,item,qty,total_price,date) values(%s,%s,%s,%s,%s)',[id1,item,price,qty,date_today])
    mysql.connection.commit()
    cursor.close()
    return 'Your Order Placed Successfully'
@app.route('/cart/<string:name>/<int:price>/<path:imgurl>')
def cart(name,price,imgurl):
    if name not in session['cart'].keys():
        session['cart'][name]=[price,imgurl]
        session.modify=True
        flash('Your item is added to cart')
        return redirect(url_for('homepagemain'))
    else:
        flash('Your item is already added to cart')
        return redirect(url_for('homepagemain'))
@app.route('/cartview')
def view():
    data=session['cart']
    return render_template('cart.html',data=data)
@app.route('/logout')
def logout():
    session.pop('name')
    session.pop('cart')
    return redirect(url_for('welcome'))
@app.route('/orders')
def orders():
    if session.get('name'):
        cursor=mysql.connection.cursor()
        cursor.execute('SELECT * from orders where mobile_no=%s',[session.get('name')])
        data=cursor.fetchall()
        return render_template('orders.html',orders=data)
    return redirect(url_for('welcome'))
app.run(debug=True, use_reloader= True)