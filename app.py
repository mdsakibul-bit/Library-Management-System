from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from pathlib import Path
from datetime import date

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "library.db"
app = Flask(__name__)
app.secret_key = "change-this-secret-key-for-real-deployment"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            category TEXT DEFAULT '',
            quantity INTEGER NOT NULL DEFAULT 1 CHECK(quantity >= 0)
        );
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            student_no TEXT NOT NULL UNIQUE,
            phone TEXT DEFAULT '',
            email TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS loans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL REFERENCES books(id),
            student_id INTEGER NOT NULL REFERENCES students(id),
            issue_date TEXT NOT NULL,
            due_date TEXT NOT NULL,
            return_date TEXT DEFAULT '',
            status TEXT NOT NULL DEFAULT 'Issued'
        );
        """)

@app.route("/")
def dashboard():
    with get_db() as db:
        stats = {
            "books": db.execute("SELECT COUNT(*) FROM books").fetchone()[0],
            "copies": db.execute("SELECT COALESCE(SUM(quantity),0) FROM books").fetchone()[0],
            "students": db.execute("SELECT COUNT(*) FROM students").fetchone()[0],
            "issued": db.execute("SELECT COUNT(*) FROM loans WHERE status='Issued'").fetchone()[0],
        }
        recent = db.execute("""
            SELECT l.id, b.title AS book_title, s.name AS student_name,
                   l.issue_date, l.due_date, l.status
            FROM loans l JOIN books b ON b.id=l.book_id
            JOIN students s ON s.id=l.student_id
            ORDER BY l.id DESC LIMIT 6
        """).fetchall()
    return render_template("index.html", stats=stats, recent=recent, today=date.today().isoformat())

@app.route("/books", methods=["GET", "POST"])
def books():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        author = request.form.get("author", "").strip()
        category = request.form.get("category", "").strip()
        try:
            quantity = int(request.form.get("quantity", "1"))
            if quantity < 0: raise ValueError
        except ValueError:
            flash("Quantity must be a non-negative whole number.", "error")
            return redirect(url_for("books"))
        if not title or not author:
            flash("Book title and author are required.", "error")
            return redirect(url_for("books"))
        with get_db() as db:
            db.execute("INSERT INTO books(title,author,category,quantity) VALUES(?,?,?,?)",
                       (title, author, category, quantity))
        flash("Book added successfully.", "success")
        return redirect(url_for("books"))
    q = request.args.get("q", "").strip()
    with get_db() as db:
        rows = db.execute("""
            SELECT b.*, (SELECT COUNT(*) FROM loans l WHERE l.book_id=b.id AND l.status='Issued') AS out_count
            FROM books b WHERE b.title LIKE ? OR b.author LIKE ? OR b.category LIKE ?
            ORDER BY b.id DESC
        """, (f"%{q}%", f"%{q}%", f"%{q}%")).fetchall()
    return render_template("books.html", books=rows, q=q)

@app.post("/books/<int:book_id>/delete")
def delete_book(book_id):
    with get_db() as db:
        active = db.execute("SELECT COUNT(*) FROM loans WHERE book_id=? AND status='Issued'", (book_id,)).fetchone()[0]
        if active:
            flash("This book has an active issue record, so it cannot be deleted yet.", "error")
        else:
            db.execute("DELETE FROM books WHERE id=?", (book_id,))
            flash("Book deleted.", "success")
    return redirect(url_for("books"))

@app.route("/students", methods=["GET", "POST"])
def students():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        student_no = request.form.get("student_no", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()
        if not name or not student_no:
            flash("Student name and student ID are required.", "error")
            return redirect(url_for("students"))
        try:
            with get_db() as db:
                db.execute("INSERT INTO students(name,student_no,phone,email) VALUES(?,?,?,?)",
                           (name, student_no, phone, email))
            flash("Student registered successfully.", "success")
        except sqlite3.IntegrityError:
            flash("That student ID already exists. Please use a unique ID.", "error")
        return redirect(url_for("students"))
    q = request.args.get("q", "").strip()
    with get_db() as db:
        rows = db.execute("""
            SELECT s.*, (SELECT COUNT(*) FROM loans l WHERE l.student_id=s.id AND l.status='Issued') AS active_loans
            FROM students s WHERE s.name LIKE ? OR s.student_no LIKE ? OR s.phone LIKE ?
            ORDER BY s.id DESC
        """, (f"%{q}%", f"%{q}%", f"%{q}%")).fetchall()
    return render_template("students.html", students=rows, q=q)

@app.post("/students/<int:student_id>/delete")
def delete_student(student_id):
    with get_db() as db:
        active = db.execute("SELECT COUNT(*) FROM loans WHERE student_id=? AND status='Issued'", (student_id,)).fetchone()[0]
        if active:
            flash("This student has an active issued book. Return it before deleting the student.", "error")
        else:
            db.execute("DELETE FROM students WHERE id=?", (student_id,))
            flash("Student deleted.", "success")
    return redirect(url_for("students"))

@app.route("/circulation", methods=["GET", "POST"])
def circulation():
    if request.method == "POST":
        book_id = request.form.get("book_id", type=int)
        student_id = request.form.get("student_id", type=int)
        due_date = request.form.get("due_date", "").strip()
        if not book_id or not student_id or not due_date:
            flash("Select a book, student, and due date.", "error")
            return redirect(url_for("circulation"))
        with get_db() as db:
            book = db.execute("SELECT quantity FROM books WHERE id=?", (book_id,)).fetchone()
            student = db.execute("SELECT id FROM students WHERE id=?", (student_id,)).fetchone()
            if not book or not student:
                flash("The selected book or student was not found.", "error")
            elif book["quantity"] < 1:
                flash("No available copies of this book.", "error")
            else:
                db.execute("INSERT INTO loans(book_id,student_id,issue_date,due_date,status) VALUES(?,?,?,?, 'Issued')",
                           (book_id, student_id, date.today().isoformat(), due_date))
                db.execute("UPDATE books SET quantity=quantity-1 WHERE id=?", (book_id,))
                flash("Book issued successfully.", "success")
        return redirect(url_for("circulation"))
    with get_db() as db:
        available_books = db.execute("SELECT id,title,author,quantity FROM books WHERE quantity>0 ORDER BY title").fetchall()
        student_rows = db.execute("SELECT id,name,student_no FROM students ORDER BY name").fetchall()
        loans = db.execute("""
            SELECT l.*, b.title AS book_title, s.name AS student_name, s.student_no
            FROM loans l JOIN books b ON b.id=l.book_id JOIN students s ON s.id=l.student_id
            ORDER BY CASE WHEN l.status='Issued' THEN 0 ELSE 1 END, l.id DESC
        """).fetchall()
    return render_template("circulation.html", books=available_books, students=student_rows, loans=loans,
                           today=date.today().isoformat())

@app.post("/loans/<int:loan_id>/return")
def return_book(loan_id):
    with get_db() as db:
        loan = db.execute("SELECT book_id,status FROM loans WHERE id=?", (loan_id,)).fetchone()
        if not loan:
            flash("Issue record not found.", "error")
        elif loan["status"] == "Returned":
            flash("This book has already been returned.", "error")
        else:
            db.execute("UPDATE loans SET status='Returned', return_date=? WHERE id=?",
                       (date.today().isoformat(), loan_id))
            db.execute("UPDATE books SET quantity=quantity+1 WHERE id=?", (loan["book_id"],))
            flash("Book returned successfully.", "success")
    return redirect(url_for("circulation"))

@app.route("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    init_db()
    app.run(debug=False, host="127.0.0.1", port=5000)
