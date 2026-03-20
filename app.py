print("NEW CODE RUNNING")

from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import bcrypt

from datetime import datetime   # ✅ NEW

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# ------------------ DATABASE ------------------
def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# ------------------ HOME ------------------
@app.route('/')
def home():
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    return render_template("register.html")


# ------------------ SIGNUP ------------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        query = "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)"
        cursor.execute(query, (username, hashed_password, "user"))
        db.commit()

        return redirect(url_for('login'))

    return render_template("signup.html")


# ------------------ LOGIN ------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        query = "SELECT * FROM users WHERE username=%s"
        cursor.execute(query, (username,))
        user = cursor.fetchone()

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            
            if user['role'] != 'admin':
                return "Access Denied ❌ Admin Only"

            session['user'] = username
            session['role'] = user['role']

            return redirect(url_for('home'))

        return "Invalid Credentials ❌"

    return render_template("login.html")


# ------------------ LOGOUT ------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ------------------ REGISTER PATIENT ------------------
@app.route('/register', methods=['POST'])
def register():
    try:
        name = request.form['name']
        age = request.form['age']
        gender = request.form['gender']
        phone = request.form['phone']
        email = request.form['email']

        query = """
        INSERT INTO patients (name, age, gender, phone, email)
        VALUES (%s, %s, %s, %s, %s)
        """

        cursor.execute(query, (name, age, gender, phone, email))
        db.commit()

        return redirect(url_for('view_patients'))

    except Exception as e:
        return f"Error: {e}"


# ------------------ VIEW PATIENTS ------------------
@app.route('/patients')
def view_patients():
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    cursor.execute("SELECT * FROM patients")
    data = cursor.fetchall()

    return render_template("patients.html", patients=data)


# ------------------ BOOK APPOINTMENT ------------------
@app.route('/book')
def book():
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    cursor.execute("SELECT * FROM patients")
    patients = cursor.fetchall()

    cursor.execute("SELECT * FROM doctors")
    doctors = cursor.fetchall()

    return render_template("book.html", patients=patients, doctors=doctors)


# ------------------ SAVE APPOINTMENT ------------------
@app.route('/book_appointment', methods=['POST'])
def book_appointment():
    cursor = db.cursor(dictionary=True)

    patient_id = request.form['patient_id']
    doctor_id = request.form['doctor_id']
    date = request.form['date']
    time = request.form['time']

    username = session['user']

    cursor.execute("SELECT user_id FROM users WHERE username=%s", (username,))
    user = cursor.fetchone()
    user_id = user['user_id']

    query = """
    INSERT INTO appointments (patient_id, doctor_id, date, time, status, user_id)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    values = (patient_id, doctor_id, date, time, "Pending", user_id)

    cursor.execute(query, values)
    db.commit()

    return redirect(url_for('view_appointments'))


# ------------------ VIEW APPOINTMENTS ------------------
@app.route('/appointments')
def view_appointments():
    cursor = db.cursor(dictionary=True, buffered=True)

    status = request.args.get('status')
    doctor_id = request.args.get('doctor_id')
    date = request.args.get('date')
    search = request.args.get('search')

    query = """
    SELECT a.appointment_id, p.name AS patient_name, d.name AS doctor_name,
           a.date, a.time, a.status, a.created_at
    FROM appointments a
    JOIN patients p ON a.patient_id = p.patient_id
    JOIN doctors d ON a.doctor_id = d.doctor_id
    WHERE 1=1
    """

    values = []

    if status:
        query += " AND a.status = %s"
        values.append(status)

    if doctor_id:
        query += " AND a.doctor_id = %s"
        values.append(doctor_id)

    if date:
        query += " AND a.date = %s"
        values.append(date)

    if search:
        query += " AND p.name LIKE %s"
        values.append(f"%{search}%")

    cursor.execute(query, tuple(values))
    data = cursor.fetchall()

    cursor.execute("SELECT * FROM doctors")
    doctors = cursor.fetchall()

    return render_template("appointments.html", appointments=data, doctors=doctors)


# ------------------ UPDATE STATUS ------------------
@app.route('/update_status/<int:id>/<string:status>')
def update_status(id, status):
    query = "UPDATE appointments SET status=%s WHERE appointment_id=%s"
    cursor.execute(query, (status, id))
    db.commit()

    return redirect(url_for('view_appointments'))


# ------------------ DELETE APPOINTMENT ------------------
@app.route('/delete_appointment/<int:id>')
def delete_appointment(id):
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    query = "DELETE FROM appointments WHERE appointment_id=%s"
    cursor.execute(query, (id,))
    db.commit()

    return redirect(url_for('view_appointments'))


# ------------------ ADMIN DASHBOARD ------------------
@app.route('/admin')
def admin_dashboard():
    if 'user' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    return render_template("admin.html")


# ------------------ RUN ------------------
if __name__ == '__main__':
    app.run(debug=True)