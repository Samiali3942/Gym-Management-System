import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, flash

# Database Configuration
MYSQL_HOST = 'localhost'
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'SM03@apss' # enter your password

MYSQL_DB = 'gymmanagement'

# Connect to MySQL
db = mysql.connector.connect(
    host=MYSQL_HOST,
    user=MYSQL_USER,
    password=MYSQL_PASSWORD,
    database=MYSQL_DB
)
cursor = db.cursor()

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Required for flash messages

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/members')
def members():
    # Get search and filter parameters
    search = request.args.get('search', '')
    membership_type = request.args.get('membership_type', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    # Build the query with filters
    query = "SELECT * FROM Members WHERE 1=1"
    params = []
    
    if search:
        query += " AND (name LIKE %s OR email LIKE %s OR contact_number LIKE %s)"
        search_param = f"%{search}%"
        params.extend([search_param, search_param, search_param])
    
    if membership_type:
        query += " AND membership_type = %s"
        params.append(membership_type)
    
    if start_date:
        query += " AND start_date >= %s"
        params.append(start_date)
    
    if end_date:
        query += " AND start_date <= %s"
        params.append(end_date)
    
    query += " ORDER BY name"
    
    cursor.execute(query, params)
    members_data = cursor.fetchall()
    
    # Get related record counts for each member
    members_with_counts = []
    for member in members_data:
        cursor.execute("SELECT COUNT(*) FROM Payments WHERE member_id = %s", (member[0],))
        payment_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM attendance WHERE member_id = %s", (member[0],))
        attendance_count = cursor.fetchone()[0]
        
        members_with_counts.append({
            'member': member,
            'payment_count': payment_count,
            'attendance_count': attendance_count
        })
    
    # Get unique membership types for filter dropdown
    cursor.execute("SELECT DISTINCT membership_type FROM Members WHERE membership_type IS NOT NULL AND membership_type != '' ORDER BY membership_type")
    membership_types = [row[0] for row in cursor.fetchall()]
    
    print(members_data)
    return render_template('members.html', 
                         members_data=members_with_counts, 
                         membership_types=membership_types,
                         search=search,
                         membership_type_filter=membership_type,
                         start_date=start_date,
                         end_date=end_date)

@app.route('/insert_member', methods=['POST'])
def insert_member():
    if request.method == 'POST':
        name = request.form['name']
        contact_number = request.form['phone']
        email = request.form['email']
        membership_type = request.form['membership_type']
        start_date = request.form['join_date']

        sql = "INSERT INTO Members (name, contact_number, email, membership_type, start_date) VALUES (%s, %s, %s, %s, %s)"
        values = (name, contact_number, email, membership_type, start_date)

        cursor.execute(sql, values)
        db.commit()
        flash('Member added successfully!', 'success')
        return redirect(url_for('members'))

@app.route('/update_member/<int:member_id>', methods=['GET', 'POST'])
def update_member(member_id):
    if request.method == 'GET':
        cursor.execute("SELECT * FROM Members WHERE id = %s", (member_id,))
        member = cursor.fetchone()
        return render_template('update_member.html', member=member)
    
    elif request.method == 'POST':
        name = request.form['name']
        contact_number = request.form['phone']
        email = request.form['email']
        membership_type = request.form['membership_type']
        start_date = request.form['join_date']

        sql = "UPDATE Members SET name = %s, contact_number = %s, email = %s, membership_type = %s, start_date = %s WHERE id = %s"
        values = (name, contact_number, email, membership_type, start_date, member_id)

        cursor.execute(sql, values)
        db.commit()
        flash('Member updated successfully!', 'success')
        return redirect(url_for('members'))

@app.route('/delete_member/<int:member_id>')
def delete_member(member_id):
    try:
        # Check if member has related records
        cursor.execute("SELECT COUNT(*) FROM Payments WHERE member_id = %s", (member_id,))
        payment_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM attendance WHERE member_id = %s", (member_id,))
        attendance_count = cursor.fetchone()[0]
        
        if payment_count > 0 or attendance_count > 0:
            flash(f'Cannot delete member. This member has {payment_count} payment(s) and {attendance_count} attendance record(s). Please delete related records first.', 'error')
        else:
            cursor.execute("DELETE FROM Members WHERE id = %s", (member_id,))
            db.commit()
            flash('Member deleted successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f'Error deleting member: {err}', 'error')
    return redirect(url_for('members'))

@app.route('/trainers')
def trainers():
    # Get search and filter parameters
    search = request.args.get('search', '')
    speciality = request.args.get('speciality', '')
    
    # Build the query with filters
    query = "SELECT * FROM Trainers WHERE 1=1"
    params = []
    
    if search:
        query += " AND (name LIKE %s OR Contact_number LIKE %s)"
        search_param = f"%{search}%"
        params.extend([search_param, search_param])
    
    if speciality:
        query += " AND speciality = %s"
        params.append(speciality)
    
    query += " ORDER BY name"
    
    cursor.execute(query, params)
    trainers_data = cursor.fetchall()
    
    # Get related record counts for each trainer
    trainers_with_counts = []
    for trainer in trainers_data:
        cursor.execute("SELECT COUNT(*) FROM Classes WHERE trainer_id = %s", (trainer[0],))
        class_count = cursor.fetchone()[0]
        
        trainers_with_counts.append({
            'trainer': trainer,
            'class_count': class_count
        })
    
    # Get unique specialities for filter dropdown
    cursor.execute("SELECT DISTINCT speciality FROM Trainers WHERE speciality IS NOT NULL AND speciality != '' ORDER BY speciality")
    specialities = [row[0] for row in cursor.fetchall()]
    
    return render_template('trainers.html', 
                         trainers_data=trainers_with_counts,
                         specialities=specialities,
                         search=search,
                         speciality_filter=speciality)

@app.route('/insert_trainer', methods=['POST'])
def insert_trainer():
    if request.method == 'POST':
        name = request.form['name']
        speciality = request.form['speciality']
        phone = request.form['Phone']

        sql = "INSERT INTO Trainers (name, speciality,Contact_number) VALUES (%s, %s, %s)"
        values = (name, speciality,phone)

        cursor.execute(sql, values)
        db.commit()
        flash('Trainer added successfully!', 'success')
        return redirect(url_for('trainers'))

@app.route('/update_trainer/<int:trainer_id>', methods=['GET', 'POST'])
def update_trainer(trainer_id):
    if request.method == 'GET':
        cursor.execute("SELECT * FROM Trainers WHERE id = %s", (trainer_id,))
        trainer = cursor.fetchone()
        return render_template('update_trainer.html', trainer=trainer)
    
    elif request.method == 'POST':
        name = request.form['name']
        speciality = request.form['speciality']
        phone = request.form['Phone']

        sql = "UPDATE Trainers SET name = %s, speciality = %s, Contact_number = %s WHERE id = %s"
        values = (name, speciality, phone, trainer_id)

        cursor.execute(sql, values)
        db.commit()
        flash('Trainer updated successfully!', 'success')
        return redirect(url_for('trainers'))

@app.route('/delete_trainer/<int:trainer_id>')
def delete_trainer(trainer_id):
    try:
        # Check if trainer has related classes
        cursor.execute("SELECT COUNT(*) FROM Classes WHERE trainer_id = %s", (trainer_id,))
        class_count = cursor.fetchone()[0]
        
        if class_count > 0:
            flash(f'Cannot delete trainer. This trainer is assigned to {class_count} class(es). Please reassign or delete the classes first.', 'error')
        else:
            cursor.execute("DELETE FROM Trainers WHERE id = %s", (trainer_id,))
            db.commit()
            flash('Trainer deleted successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f'Error deleting trainer: {err}', 'error')
    return redirect(url_for('trainers'))

@app.route('/classes')
def classes():
    # Get search and filter parameters
    search = request.args.get('search', '')
    trainer_id = request.args.get('trainer_id', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    # Build the query with filters
    query = "SELECT c.*, t.name as trainer_name FROM Classes c LEFT JOIN Trainers t ON c.trainer_id = t.id WHERE 1=1"
    params = []
    
    if search:
        query += " AND c.class_name LIKE %s"
        search_param = f"%{search}%"
        params.append(search_param)
    
    if trainer_id:
        query += " AND c.trainer_id = %s"
        params.append(trainer_id)
    
    if start_date:
        query += " AND DATE(c.time) >= %s"
        params.append(start_date)
    
    if end_date:
        query += " AND DATE(c.time) <= %s"
        params.append(end_date)
    
    query += " ORDER BY c.time"
    
    cursor.execute(query, params)
    classes_data = cursor.fetchall()
    
    # Get related record counts for each class
    classes_with_counts = []
    for class_data in classes_data:
        cursor.execute("SELECT COUNT(*) FROM attendance WHERE class_id = %s", (class_data[0],))
        attendance_count = cursor.fetchone()[0]
        
        classes_with_counts.append({
            'class': class_data,
            'attendance_count': attendance_count
        })
    
    # Get all trainers for dropdown
    cursor.execute("SELECT id, name, speciality FROM Trainers")
    trainers = cursor.fetchall()
    
    return render_template('classes.html', 
                         classes_data=classes_with_counts, 
                         trainers=trainers,
                         search=search,
                         trainer_id_filter=trainer_id,
                         start_date=start_date,
                         end_date=end_date)

@app.route('/insert_class', methods=['POST'])
def insert_class():
    if request.method == 'POST':
        class_name = request.form['class_name']
        trainer_id = request.form['trainer_id']
        time = request.form['time']

        # Check if trainer exists
        cursor.execute("SELECT id FROM Trainers WHERE id = %s", (trainer_id,))
        trainer = cursor.fetchone()
        
        if not trainer:
            flash(f'Error: Trainer with ID {trainer_id} does not exist. Please enter a valid trainer ID.', 'error')
            return redirect(url_for('classes'))

        try:
            sql = "INSERT INTO Classes (class_name, trainer_id, time) VALUES (%s, %s, %s)"
            values = (class_name, trainer_id, time)

            cursor.execute(sql, values)
            db.commit()
            flash('Class added successfully!', 'success')
        except mysql.connector.Error as err:
            flash(f'Error adding class: {err}', 'error')
        
        return redirect(url_for('classes'))

@app.route('/update_class/<int:class_id>', methods=['GET', 'POST'])
def update_class(class_id):
    if request.method == 'GET':
        cursor.execute("SELECT * FROM Classes WHERE id = %s", (class_id,))
        class_data = cursor.fetchone()
        cursor.execute("SELECT * FROM Trainers")
        trainers = cursor.fetchall()
        return render_template('update_class.html', class_data=class_data, trainers=trainers)
    
    elif request.method == 'POST':
        class_name = request.form['class_name']
        trainer_id = request.form['trainer_id']
        time = request.form['time']

        sql = "UPDATE Classes SET class_name = %s, trainer_id = %s, time = %s WHERE id = %s"
        values = (class_name, trainer_id, time, class_id)

        cursor.execute(sql, values)
        db.commit()
        flash('Class updated successfully!', 'success')
        return redirect(url_for('classes'))

@app.route('/delete_class/<int:class_id>')
def delete_class(class_id):
    try:
        # Check if class has related attendance records
        cursor.execute("SELECT COUNT(*) FROM attendance WHERE class_id = %s", (class_id,))
        attendance_count = cursor.fetchone()[0]
        
        if attendance_count > 0:
            flash(f'Cannot delete class. This class has {attendance_count} attendance record(s). Please delete attendance records first.', 'error')
        else:
            cursor.execute("DELETE FROM Classes WHERE id = %s", (class_id,))
            db.commit()
            flash('Class deleted successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f'Error deleting class: {err}', 'error')
    return redirect(url_for('classes'))

@app.route('/payments')
def payments():
    # Get search and filter parameters
    member_id = request.args.get('member_id', '')
    min_amount = request.args.get('min_amount', '')
    max_amount = request.args.get('max_amount', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    # Build the query with filters
    query = "SELECT p.*, m.name as member_name FROM Payments p LEFT JOIN Members m ON p.member_id = m.id WHERE 1=1"
    params = []
    
    if member_id:
        query += " AND p.member_id = %s"
        params.append(member_id)
    
    if min_amount:
        query += " AND p.amount >= %s"
        params.append(min_amount)
    
    if max_amount:
        query += " AND p.amount <= %s"
        params.append(max_amount)
    
    if start_date:
        query += " AND p.payment_date >= %s"
        params.append(start_date)
    
    if end_date:
        query += " AND p.payment_date <= %s"
        params.append(end_date)
    
    query += " ORDER BY p.payment_date DESC"
    
    cursor.execute(query, params)
    payments_data = cursor.fetchall()
    
    # Get all members for dropdown
    cursor.execute("SELECT id, name, email FROM Members")
    members = cursor.fetchall()
    
    return render_template('payments.html', 
                         payments_data=payments_data, 
                         members=members,
                         member_id_filter=member_id,
                         min_amount=min_amount,
                         max_amount=max_amount,
                         start_date=start_date,
                         end_date=end_date)

@app.route('/insert_payment', methods=['POST'])
def insert_payment():
    if request.method == 'POST':
        member_id = request.form['member_id']
        amount = request.form['amount']
        payment_date = request.form['payment_date']

        # Check if member exists
        cursor.execute("SELECT id FROM Members WHERE id = %s", (member_id,))
        member = cursor.fetchone()
        
        if not member:
            flash(f'Error: Member with ID {member_id} does not exist. Please enter a valid member ID.', 'error')
            return redirect(url_for('payments'))

        try:
            sql = "INSERT INTO Payments (member_id, amount, payment_date) VALUES (%s, %s, %s)"
            values = (member_id, amount, payment_date)

            cursor.execute(sql, values)
            db.commit()
            flash('Payment added successfully!', 'success')
        except mysql.connector.Error as err:
            flash(f'Error adding payment: {err}', 'error')
        
        return redirect(url_for('payments'))

@app.route('/update_payment/<int:payment_id>', methods=['GET', 'POST'])
def update_payment(payment_id):
    if request.method == 'GET':
        cursor.execute("SELECT * FROM Payments WHERE id = %s", (payment_id,))
        payment = cursor.fetchone()
        cursor.execute("SELECT * FROM Members")
        members = cursor.fetchall()
        return render_template('update_payment.html', payment=payment, members=members)
    
    elif request.method == 'POST':
        member_id = request.form['member_id']
        amount = request.form['amount']
        payment_date = request.form['payment_date']

        sql = "UPDATE Payments SET member_id = %s, amount = %s, payment_date = %s WHERE id = %s"
        values = (member_id, amount, payment_date, payment_id)

        cursor.execute(sql, values)
        db.commit()
        flash('Payment updated successfully!', 'success')
        return redirect(url_for('payments'))

@app.route('/delete_payment/<int:payment_id>')
def delete_payment(payment_id):
    try:
        cursor.execute("DELETE FROM Payments WHERE id = %s", (payment_id,))
        db.commit()
        flash('Payment deleted successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f'Error deleting payment: {err}', 'error')
    return redirect(url_for('payments'))

@app.route('/attendance')
def attendance():
    # Get search and filter parameters
    member_id = request.args.get('member_id', '')
    class_id = request.args.get('class_id', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    # Build the query with filters
    query = "SELECT a.*, m.name as member_name, c.class_name FROM attendance a LEFT JOIN Members m ON a.member_id = m.id LEFT JOIN Classes c ON a.class_id = c.id WHERE 1=1"
    params = []
    
    if member_id:
        query += " AND a.member_id = %s"
        params.append(member_id)
    
    if class_id:
        query += " AND a.class_id = %s"
        params.append(class_id)
    
    if start_date:
        query += " AND a.date >= %s"
        params.append(start_date)
    
    if end_date:
        query += " AND a.date <= %s"
        params.append(end_date)
    
    query += " ORDER BY a.date DESC"
    
    cursor.execute(query, params)
    attendance_data = cursor.fetchall()
    
    # Get all members and classes for dropdowns
    cursor.execute("SELECT id, name, email FROM Members")
    members = cursor.fetchall()
    
    cursor.execute("SELECT id, class_name FROM Classes")
    classes = cursor.fetchall()
    
    return render_template('attendance.html', 
                         attendance_data=attendance_data, 
                         members=members, 
                         classes=classes,
                         member_id_filter=member_id,
                         class_id_filter=class_id,
                         start_date=start_date,
                         end_date=end_date)

@app.route('/insert_attendance', methods=['POST'])
def insert_attendance():
    if request.method == 'POST':
        member_id = request.form['member_id']
        class_id = request.form['class_id']
        date = request.form['payment_date']

        # Check if member exists
        cursor.execute("SELECT id FROM Members WHERE id = %s", (member_id,))
        member = cursor.fetchone()
        
        if not member:
            flash(f'Error: Member with ID {member_id} does not exist. Please enter a valid member ID.', 'error')
            return redirect(url_for('attendance'))

        # Check if class exists
        cursor.execute("SELECT id FROM Classes WHERE id = %s", (class_id,))
        class_data = cursor.fetchone()
        
        if not class_data:
            flash(f'Error: Class with ID {class_id} does not exist. Please enter a valid class ID.', 'error')
            return redirect(url_for('attendance'))

        try:
            sql = "INSERT INTO attendance ( member_id, class_id,date) VALUES (%s, %s, %s)"
            values = (member_id, class_id,date)

            cursor.execute(sql, values)
            db.commit()
            flash('Attendance added successfully!', 'success')
        except mysql.connector.Error as err:
            flash(f'Error adding attendance: {err}', 'error')
        
        return redirect(url_for('attendance'))

@app.route('/update_attendance/<int:attendance_id>', methods=['GET', 'POST'])
def update_attendance(attendance_id):
    if request.method == 'GET':
        cursor.execute("SELECT * FROM attendance WHERE id = %s", (attendance_id,))
        attendance = cursor.fetchone()
        cursor.execute("SELECT * FROM Members")
        members = cursor.fetchall()
        cursor.execute("SELECT * FROM Classes")
        classes = cursor.fetchall()
        return render_template('update_attendance.html', attendance=attendance, members=members, classes=classes)
    
    elif request.method == 'POST':
        member_id = request.form['member_id']
        class_id = request.form['class_id']
        date = request.form['date']

        sql = "UPDATE attendance SET member_id = %s, class_id = %s, date = %s WHERE id = %s"
        values = (member_id, class_id, date, attendance_id)

        cursor.execute(sql, values)
        db.commit()
        flash('Attendance updated successfully!', 'success')
        return redirect(url_for('attendance'))

@app.route('/delete_attendance/<int:attendance_id>')
def delete_attendance(attendance_id):
    try:
        cursor.execute("DELETE FROM attendance WHERE id = %s", (attendance_id,))
        db.commit()
        flash('Attendance deleted successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f'Error deleting attendance: {err}', 'error')
    return redirect(url_for('attendance'))

if __name__ == '__main__':
    app.run(debug=True)

# Close the database connection
db.close()