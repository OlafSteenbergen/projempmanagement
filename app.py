from types import NoneType
from flask import Response, Flask, flash, render_template, redirect, url_for, request, session, g
from database import get_database
from werkzeug.security import generate_password_hash, check_password_hash
import io
import numpy as np
import pandas as pd
import random
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib import axes
import matplotlib.pyplot as plt
import datetime
import plotly.express as px


app = Flask(__name__)
app.config['SECRET_KEY'] = 'hello'
app.permanent_session_lifetime = datetime.timedelta(minutes=5)

def get_current_user():
    user = None
    if 'user' in session:
        user = session['user']
        db = get_database()
        user_cur = db.execute('select * from users where name = ?', [user])
        user = user_cur.fetchone()
    return user

def check_password_strength(name, password):
    if (name.upper() not in password.upper()) and (any(x.isupper() for x in password)) and (any(x.islower() for x in password)) and (len(password) > 5) and not (password.isalpha()):
        return True
    else:
        return False

@app.route("/")
def index():
    user = get_current_user()
    db = get_database()
    if user:
        allprojects = db.execute('select * from projects where empres = ?', [user['empid']]).fetchall()
        print('Output: ', allprojects)
        return render_template('home.html', user=user, allprojects=allprojects)
    else:
        return render_template('home.html', user=user, allprojects=None)

@app.route("/login", methods=["POST", "GET"])
def login():
    user = get_current_user()
    error = None
    session.permanent = True
    db = get_database()

    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']

        user_cursor = db.execute('select * from users where name = ?', [name])
        user = user_cursor.fetchone()
        
        if user:
            if check_password_hash(user['password'], password):
                session['user'] = user['name']
                return redirect(url_for('employeedashboard'))
            else:  
                error = "Username or password did not match."
        else:
            error = "Username or password did not match."

    return render_template('login.html', loginerror = error, user=user)

@app.route("/register", methods=["POST", "GET"])
def register():
    user = get_current_user()
    db = get_database()
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        empid = request.form['empid']
        hashed_password = generate_password_hash(password)

        dbuser_cur = db.execute('select * from users where name = ?', [name]).fetchone()
        dbempid_cur = db.execute('select * from users where empid = ?', [empid]).fetchone()
        dbempid_exis = db.execute('select * from emp where empid = ?', [empid]).fetchone()


        if dbuser_cur:
            flash('Username already taken, please choose a different one.')
            return render_template('register.html', name="", password=password, empid=empid)

        elif dbempid_cur:
            if empid != '':
                flash('There is already an account assigned to this employee.')
                return render_template('register.html', name=name, password=password, empid=empid)

        elif dbempid_exis == None:
            if empid != '':
                flash('Employee id provided does not exist.')
                return render_template('register.html', name=name, password=password, empid=empid)

        if check_password_strength(name, password):
            db.execute('insert into users( name, password, empid) values (?, ?, ?)', [name, hashed_password, empid])
            db.commit()
            return render_template('home.html', user=user, just_registered=True)
        else:
            flash('Password does not match requirements.')

    return render_template('register.html', user=user)

@app.route("/employeedashboard", methods=["POST", "GET"])
def employeedashboard():
    user = get_current_user()
    db = get_database()
    search = request.form.get('search', False)
    order = request.form.get('order', 'Order by')
    print(order)

#Check if user posts something and is not using the sort-function
    if request.method == 'POST' and search != False:
        allemp = db.execute('SELECT * from emp where name = ?', [search]).fetchall()
        return render_template('employeedashboard.html', allemp=allemp, order=order, user=user)
    
#Check if user posts something and uses the sort-function
    elif request.method == 'POST' and search == False:
        order = request.form.get('order', False)
        print(order)
        if order == 'name':
            allemp = db.execute('select * from emp order by name').fetchall()
        else:
            allemp = db.execute('select * from emp order by empid').fetchall()

        
        return render_template('employeedashboard.html', allemp=allemp, order=order, user=user)

#Show employee overview when GET-method is used, no search/sort
    else:
        allemp = db.execute('select * from emp').fetchall()
        return render_template('employeedashboard.html', allemp=allemp, order=order, user=user)
    

@app.route("/employeenew", methods=["POST", "GET"])
def employeenew():
    user = get_current_user()
    db = get_database()
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']

        db.execute('insert into emp(name, email, phone, address) values (?, ?, ?, ?)', [name, email, phone, address])
        db.commit()
        return redirect(url_for('employeedashboard'))

    return render_template('employeenew.html', user=user)

@app.route("/employeeprofile/<int:empid>")
def employeeprofile(empid):
    user = get_current_user()
    db = get_database()

    emp_cur = db.execute('select * from emp where empid = ?', [empid])
    single_emp = emp_cur.fetchone()

    count_proj = db.execute('select count(empres) from projects where empres = ?', [empid])
    all_proj = db.execute('select * from projects where empres = ?', [empid])

    return render_template('employeeprofile.html', user=user, single_emp=single_emp, count_proj=count_proj, all_proj=all_proj)

@app.route("/employeeupdate/<int:empid>", methods=["POST", "GET"])
def employeeupdate(empid):
    user = get_current_user()
    db = get_database()
    emp_cur = db.execute('select * from emp where empid = ?', [empid])
    single_emp = emp_cur.fetchone()

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']
        db.execute('UPDATE emp SET name = ?, email = ?, phone = ?, address = ? where empid = ?', [name, email, phone, address, empid])
        db.commit()
        return redirect(url_for('employeedashboard'))
    
    return render_template('employeeupdate.html', user=user, single_emp=single_emp)


@app.route("/employeedelete/<int:empid>", methods=["GET", "POST"])
def employeedelete(empid):
    user = get_current_user()
    
    if request.method == "GET":
        db = get_database()
        db.execute('delete from emp where empid = ?', [empid])
        db.commit()
        return redirect(url_for('employeedashboard'))
    return render_template('employeedashboard.html', user=user)

@app.route("/logout")
def logout():
    session.pop('user', None)
    return render_template("home.html")

@app.route("/projectdashboard")
def projectdashboard():
    user = get_current_user()
    db = get_database()

    allprojects = db.execute('select * from projects').fetchall()
    allemps = db.execute('select * from emp').fetchall()

    allprojects_groupbylocation = db.execute('SELECT location, COUNT(projectid) from projects GROUP BY location').fetchall()
    allprojects_groupbyempid = db.execute('SELECT empres, COUNT(projectid) from projects GROUP BY empres').fetchall()

    return render_template("projectdashboard.html", user=user, allprojects=allprojects, locations=allprojects_groupbylocation, employees=allprojects_groupbyempid, allemps=allemps)

@app.route("/projectnew", methods=["POST", "GET"])
def projectnew():
    user = get_current_user()
    db = get_database()
    allemp = db.execute('select empid from emp').fetchall()

    if request.method == 'POST':
        name = request.form['name']
        location = request.form['location']
        empres = request.form['empres']
        description = request.form['description']
        if name != "" and location != "" and empres != "":
            db.execute('insert into projects(name, description, location, empres) values (?, ?, ?, ?)', [name, description, location, empres])
            db.commit()
            return redirect(url_for('projectdashboard'))
        else:
            flash("Make sure you fill all fields correclty.")

            return render_template('projectnew.html', user=user, allemp=allemp)


    return render_template('projectnew.html', user=user, allemp=allemp)

@app.route("/projectprofile/<int:projectid>")
def projectprofile(projectid):
    user = get_current_user()
    db = get_database()
    proj_cur = db.execute('select * from projects where projectid = ?', [projectid])
    single_proj = proj_cur.fetchone()
    single_emp = db.execute('select name from emp where empid = ?', [single_proj['empres']]).fetchone()
    
    return render_template('projectprofile.html', user=user, single_proj=single_proj, single_emp=single_emp)

@app.route("/projectupdate/<int:projectid>", methods=["POST", "GET"])
def projectupdate(projectid):
    user = get_current_user()
    db = get_database()
    allemp = db.execute('select empid, name from emp').fetchall()
    proj_cur = db.execute('select * from projects where projectid = ?', [projectid])
    single_proj = proj_cur.fetchone()

    if request.method == 'POST':
        name = request.form['name']
        location = request.form['location']
        empres = request.form['empres']
        description = request.form['description']

        if name != "" and location != "" and empres != "":
            db.execute('UPDATE projects SET name = ?, description = ?, location = ?, empres = ? where projectid = ?', [name, description, location, empres, projectid])
            db.commit()
        else:
            flash("Make sure you fill all fields correclty.")
            return render_template('projectupdate.html', user=user, single_proj=single_proj, allemp=allemp)


        return redirect(url_for('projectdashboard'))
    
    return render_template('projectupdate.html', user=user, single_proj=single_proj, allemp=allemp)


@app.route("/projectdelete/<int:projectid>", methods=["GET", "POST"])
def projectdelete(projectid):
    user = get_current_user()
    
    if request.method == "GET":
        db = get_database()
        db.execute('delete from projects where projectid = ?', [projectid])
        db.commit()
        return redirect(url_for('projectdashboard'))
    return render_template('projectdashboard.html', user=user)

@app.route("/userprofile")
def userprofile():
    user = get_current_user()
    db = get_database()

    if 'user' in session and type('user') != NoneType:
        user_cur = db.execute('select * from users where id = ?', [user['id']]).fetchone()
        return render_template('userprofile.html', user_cur=user_cur)
    else:
        return render_template('userprofile.html', user_cur='')

if __name__ == "__main__":
    app.run(debug=True)