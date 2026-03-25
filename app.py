from flask import Flask, render_template, request, redirect, url_for, session
import json
import os

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

DATA_FILE = "students.json"


# -------------------------
# Utility Functions
# -------------------------

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


def assign_grade(avg):
    if avg >= 70:
        return "A"
    elif avg >= 60:
        return "B"
    elif avg >= 50:
        return "C"
    elif avg >= 45:
        return "D"
    elif avg >= 40:
        return "E"
    else:
        return "F"


# -------------------------
# Authentication
# -------------------------

@app.route("/", methods=["GET"])
def login():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def do_login():
    username = request.form.get("username")
    password = request.form.get("password")

    ADMIN_USER = "Admin"
    ADMIN_PASS = "Muslim Pride Schools"

    if username == ADMIN_USER and password == ADMIN_PASS:
        session["logged_in"] = True
        return redirect(url_for("dashboard"))
    else:
        return render_template("login.html", error="Invalid login")


@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("login"))


# -------------------------
# Dashboard
# -------------------------

@app.route("/dashboard")
def dashboard():
    if "logged_in" not in session:
        return redirect(url_for("login"))

    data = load_data()

    all_scores = []
    for stu in data:
        for s in stu["subjects"]:
            all_scores.append(s["total"])

    class_avg = round(sum(all_scores) / len(all_scores), 2) if all_scores else 0
    return render_template("dashboard.html", class_average=class_avg)


# -------------------------
# Add Student
# -------------------------

@app.route("/add", methods=["GET"])
def add_form():
    if "logged_in" not in session:
        return redirect(url_for("login"))
    return render_template("add_student.html")


@app.route("/add", methods=["POST"])
def add_student():
    if "logged_in" not in session:
        return redirect(url_for("login"))

    name = request.form.get("name")

    subjects = request.form.getlist("subject")
    test1_list = request.form.getlist("test1")
    test2_list = request.form.getlist("test2")
    exam_list = request.form.getlist("exam")

    data = load_data()

    # Check if student already exists
    existing_student = None
    for stu in data:
        if stu["name"].lower() == name.lower():
            existing_student = stu
            break

    new_subject_items = []
    for i in range(len(subjects)):
        t1 = float(test1_list[i])
        t2 = float(test2_list[i])
        ex = float(exam_list[i])
        total = t1 + t2 + ex

        new_subject_items.append({
            "name": subjects[i],
            "test1": t1,
            "test2": t2,
            "exam": ex,
            "total": round(total, 2)
        })

    if existing_student:
        # Append new subjects
        existing_student["subjects"].extend(new_subject_items)

        totals = [s["total"] for s in existing_student["subjects"]]
        existing_student["average"] = round(sum(totals) / len(totals), 2)
        existing_student["grade"] = assign_grade(existing_student["average"])

    else:
        totals = [s["total"] for s in new_subject_items]
        avg = sum(totals) / len(totals)

        new_student = {
            "name": name,
            "subjects": new_subject_items,
            "average": round(avg, 2),
            "grade": assign_grade(avg)
        }

        data.append(new_student)

    save_data(data)
    return redirect(url_for("students_list"))


# -------------------------
# View Students
# -------------------------

@app.route("/students")
def students_list():
    if "logged_in" not in session:
        return redirect(url_for("login"))
    data = load_data()
    return render_template("students.html", students=data)


@app.route("/student/<int:index>")
def view_student(index):
    data = load_data()
    if index >= len(data):
        return "Student not found"
    student = data[index]
    return render_template("student_detail.html", student=student, index=index)


# -------------------------
# Delete Student
# -------------------------

@app.route("/delete/<int:index>")
def delete_student(index):
    if "logged_in" not in session:
        return redirect(url_for("login"))

    data = load_data()
    if index < len(data):
        data.pop(index)
        save_data(data)

    return redirect(url_for("students_list"))


# -------------------------
# Edit Student
# -------------------------

@app.route("/edit/<int:index>", methods=["GET"])
def edit_student_form(index):
    if "logged_in" not in session:
        return redirect(url_for("login"))

    data = load_data()

    if index >= len(data):
        return "Student not found"

    student = data[index]
    return render_template("edit_student.html", student=student, index=index)


@app.route("/edit/<int:index>", methods=["POST"])
def edit_student(index):
    if "logged_in" not in session:
        return redirect(url_for("login"))

    data = load_data()

    if index >= len(data):
        return "Student not found"

    new_name = request.form.get("name")

    subjects = request.form.getlist("subject")
    test1_list = request.form.getlist("test1")
    test2_list = request.form.getlist("test2")
    exam_list = request.form.getlist("exam")

    updated_subjects = []
    for i in range(len(subjects)):
        t1 = float(test1_list[i])
        t2 = float(test2_list[i])
        ex = float(exam_list[i])
        total = t1 + t2 + ex

        updated_subjects.append({
            "name": subjects[i],
            "test1": t1,
            "test2": t2,
            "exam": ex,
            "total": round(total, 2)
        })

    # Update the student
    student = data[index]
    student["name"] = new_name
    student["subjects"] = updated_subjects

    totals = [s["total"] for s in updated_subjects]
    student["average"] = round(sum(totals) / len(totals), 2)
    student["grade"] = assign_grade(student["average"])

    save_data(data)
    return redirect(url_for("students_list"))


# -------------------------
# Run App
# -------------------------

if __name__ == "__main__":
    app.run(debug=True)