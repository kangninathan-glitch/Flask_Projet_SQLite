from flask import Flask, render_template_string, render_template, jsonify, request, redirect, url_for, session
from flask import json
from urllib.request import urlopen
from werkzeug.utils import secure_filename
import sqlite3

app = Flask(__name__)                                                                                                                  
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'  # Clé secrète pour les sessions

def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def require_login():
    return session.get("user_id") is not None

def require_role(role):
    return session.get("role") == role

# Fonction pour créer une clé "authentifie" dans la session utilisateur
def est_authentifie():
    return session.get('authentifie')

def est_user_authentifie():
    return session.get('user_authentifie')


@app.route('/lecture')
def lecture():
    if not est_authentifie():
        # Rediriger vers la page d'authentification si l'utilisateur n'est pas authentifié
        return redirect(url_for('authentification'))

  # Si l'utilisateur est authentifié
    return "<h2>Bravo, vous êtes authentifié</h2>"

@app.route('/authentification', methods=['GET', 'POST'])
def authentification():
    if request.method == 'POST':
        # Vérifier les identifiants
        if request.form['username'] == 'admin' and request.form['password'] == 'password': # password à cacher par la suite
            session['authentifie'] = True
            # Rediriger vers la route lecture après une authentification réussie
            return redirect(url_for('lecture'))
        else:
            # Afficher un message d'erreur si les identifiants sont incorrects
            return render_template('formulaire_authentification.html', error=True)

    return render_template('formulaire_authentification.html', error=False)

@app.route('/fiche_client/<int:post_id>')
def Readfiche(post_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM clients WHERE id = ?', (post_id,))
    data = cursor.fetchall()
    conn.close()
    # Rendre le template HTML et transmettre les données
    return render_template('read_data.html', data=data)

@app.route('/consultation/')
def ReadBDD():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM clients;')
    data = cursor.fetchall()
    conn.close()
    return render_template('read_data.html', data=data)

@app.route('/enregistrer_client', methods=['GET'])
def formulaire_client():
    return render_template('formulaire.html')  # afficher le formulaire

@app.route('/enregistrer_client', methods=['POST'])
def enregistrer_client():
    nom = request.form['nom']
    prenom = request.form['prenom']

    # Connexion à la base de données
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Exécution de la requête SQL pour insérer un nouveau client
    cursor.execute('INSERT INTO clients (created, nom, prenom, adresse) VALUES (?, ?, ?, ?)', (1002938, nom, prenom, "ICI"))
    conn.commit()
    conn.close()
    return redirect('/consultation/')  # Rediriger vers la page d'accueil après l'enregistrement

@app.route('/auth_user', methods=['GET', 'POST'])
def auth_user():
    if request.method == 'POST':
        if request.form.get('username') == 'user' and request.form.get('password') == '12345':
            session['user_authentifie'] = True
            return redirect(url_for('fiche_nom'))
        else:
            return render_template('formulaire_auth_user.html', error=True)

    return render_template('formulaire_auth_user.html', error=False)

@app.route('/fiche_nom/', methods=['GET', 'POST'])
def fiche_nom():
    # Protection USER
    if not est_user_authentifie():
        return redirect(url_for('auth_user'))

    data = []
    nom_recherche = ""

    # On accepte soit POST (form), soit GET (?nom=...)
    if request.method == 'POST':
        nom_recherche = request.form.get('nom', '').strip()
    else:
        nom_recherche = request.args.get('nom', '').strip()

    if nom_recherche:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        # Recherche partielle (plus pratique) : DUPONT, du, etc.
        cursor.execute("SELECT * FROM clients WHERE nom LIKE ?", (f"%{nom_recherche}%",))
        data = cursor.fetchall()
        conn.close()

    return render_template('fiche_nom.html', data=data, nom=nom_recherche)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        conn = get_db()
        user = conn.execute(
            "SELECT id, username, role FROM users WHERE username=? AND password=?",
            (username, password)
        ).fetchone()
        conn.close()

        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            return redirect(url_for("home"))

        return render_template("login.html", error=True)

    return render_template("login.html", error=False)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
def home():
    if not require_login():
        return redirect(url_for("login"))
    return render_template("home.html", username=session.get("username"), role=session.get("role"))

@app.route("/api/books", methods=["GET"])
def api_books_list():
    if not require_login():
        return jsonify({"error": "unauthorized"}), 401

    q = request.args.get("q", "").strip()
    only_available = request.args.get("available", "0") == "1"

    conn = get_db()
    sql = """
      SELECT b.id, b.isbn, b.title, b.author, s.total, s.available
      FROM books b
      JOIN book_stock s ON s.book_id = b.id
      WHERE 1=1
    """
    params = []
    if q:
        sql += " AND (b.title LIKE ? OR b.author LIKE ? OR b.isbn LIKE ?)"
        like = f"%{q}%"
        params += [like, like, like]
    if only_available:
        sql += " AND s.available > 0"

    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/books", methods=["POST"])
def api_books_create():
    if not require_login() or not require_role("admin"):
        return jsonify({"error": "forbidden"}), 403

    payload = request.get_json(force=True)
    title = payload.get("title", "").strip()
    author = payload.get("author", "").strip()
    isbn = payload.get("isbn", "").strip()
    total = int(payload.get("total", 1))

    if not title or not author or total < 0:
        return jsonify({"error": "bad_request"}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO books (isbn, title, author) VALUES (?, ?, ?)", (isbn, title, author))
    book_id = cur.lastrowid
    cur.execute("INSERT INTO book_stock (book_id, total, available) VALUES (?, ?, ?)", (book_id, total, total))
    conn.commit()
    conn.close()
    return jsonify({"id": book_id}), 201

@app.route("/api/books/<int:book_id>", methods=["DELETE"])
def api_books_delete(book_id):
    if not require_login() or not require_role("admin"):
        return jsonify({"error": "forbidden"}), 403

    conn = get_db()
    conn.execute("DELETE FROM books WHERE id=?", (book_id,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@app.route("/api/loans/borrow", methods=["POST"])
def api_borrow():
    if not require_login():
        return jsonify({"error": "unauthorized"}), 401

    payload = request.get_json(force=True)
    book_id = int(payload.get("book_id"))

    conn = get_db()
    cur = conn.cursor()

    stock = cur.execute("SELECT available FROM book_stock WHERE book_id=?", (book_id,)).fetchone()
    if not stock or stock["available"] <= 0:
        conn.close()
        return jsonify({"error": "not_available"}), 409

    cur.execute("UPDATE book_stock SET available = available - 1 WHERE book_id=?", (book_id,))
    cur.execute("INSERT INTO loans (book_id, user_id) VALUES (?, ?)", (book_id, session["user_id"]))
    conn.commit()
    conn.close()
    return jsonify({"ok": True}), 201

@app.route("/api/loans/return", methods=["POST"])
def api_return():
    if not require_login():
        return jsonify({"error": "unauthorized"}), 401

    payload = request.get_json(force=True)
    loan_id = int(payload.get("loan_id"))

    conn = get_db()
    cur = conn.cursor()

    loan = cur.execute(
        "SELECT book_id FROM loans WHERE id=? AND user_id=? AND returned_at IS NULL",
        (loan_id, session["user_id"])
    ).fetchone()
    if not loan:
        conn.close()
        return jsonify({"error": "not_found"}), 404

    cur.execute("UPDATE loans SET returned_at=datetime('now') WHERE id=?", (loan_id,))
    cur.execute("UPDATE book_stock SET available = available + 1 WHERE book_id=?", (loan["book_id"],))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@app.route("/clients")
def clients_home():
    return redirect(url_for("formulaire_client"))

@app.route("/api/users", methods=["GET"])
def api_users_list():
    if not require_login() or not require_role("admin"):
        return jsonify({"error": "forbidden"}), 403

    conn = get_db()
    rows = conn.execute("SELECT id, username, role FROM users ORDER BY id").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/users", methods=["POST"])
def api_users_create():
    if not require_login() or not require_role("admin"):
        return jsonify({"error": "forbidden"}), 403

    payload = request.get_json(force=True)
    username = (payload.get("username") or "").strip()
    password = (payload.get("password") or "").strip()
    role = (payload.get("role") or "user").strip()

    if not username or not password or role not in ("admin", "user"):
        return jsonify({"error": "bad_request"}), 400

    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, password, role)
        )
        conn.commit()
        user_id = cur.lastrowid
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error": "username_already_exists"}), 409

    conn.close()
    return jsonify({"id": user_id, "username": username, "role": role}), 201


@app.route("/api/users/<int:user_id>", methods=["DELETE"])
def api_users_delete(user_id):
    if not require_login() or not require_role("admin"):
        return jsonify({"error": "forbidden"}), 403

    # Sécurité: empêcher de supprimer son propre compte
    if session.get("user_id") == user_id:
        return jsonify({"error": "cannot_delete_self"}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    deleted = cur.rowcount
    conn.close()

    if deleted == 0:
        return jsonify({"error": "not_found"}), 404

    return jsonify({"ok": True})

@app.route("/api/users/<int:user_id>", methods=["PATCH"])
def api_users_update(user_id):
    if not require_login() or not require_role("admin"):
        return jsonify({"error": "forbidden"}), 403

    payload = request.get_json(force=True)
    new_password = payload.get("password")
    new_role = payload.get("role")

    if new_role is not None and new_role not in ("admin", "user"):
        return jsonify({"error": "bad_request"}), 400

    fields = []
    params = []

    if new_password is not None:
        new_password = str(new_password).strip()
        if not new_password:
            return jsonify({"error": "bad_request"}), 400
        fields.append("password=?")
        params.append(new_password)

    if new_role is not None:
        fields.append("role=?")
        params.append(new_role)

    if not fields:
        return jsonify({"error": "bad_request"}), 400

    params.append(user_id)

    conn = get_db()
    cur = conn.cursor()
    cur.execute(f"UPDATE users SET {', '.join(fields)} WHERE id=?", params)
    conn.commit()
    updated = cur.rowcount
    conn.close()

    if updated == 0:
        return jsonify({"error": "not_found"}), 404

    return jsonify({"ok": True})


                                                                                                                                       
if __name__ == "__main__":
  app.run(debug=True)
