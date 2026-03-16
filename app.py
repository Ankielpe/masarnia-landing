import os
import smtplib
import time
from email.mime.text import MIMEText
from email.header import Header

from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash

# wczytaj zmienne z pliku .env
load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "zmien-to-na-wlasny-sekret")


# =========================
# KONFIGURACJA MAILA
# =========================
SMTP_HOST = os.environ.get("SMTP_HOST", "ssl0.ovh.net")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))

SMTP_USERNAME = os.environ.get("SMTP_USERNAME")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")

MAIL_TO = os.environ.get("MAIL_TO", "kontakt@masarniajastew.pl")
MAIL_FROM = os.environ.get("MAIL_FROM", SMTP_USERNAME)

# ile ms musi minąć od załadowania formularza do wysłania
MIN_FORM_TIME_MS = 3000


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/kontakt", methods=["POST"])
def kontakt():

    # =========================
    # ANTY-SPAM (honeypot)
    # =========================
    website = (request.form.get("website") or "").strip()
    if website:
        return redirect(url_for("home", _anchor="kontakt"))

    # =========================
    # ANTY-SPAM (czas wysłania)
    # =========================
    form_time_raw = (request.form.get("form_time") or "").strip()

    try:
        form_time = int(form_time_raw)
    except ValueError:
        flash("Nie udało się zweryfikować formularza.", "error")
        return redirect(url_for("home", _anchor="kontakt"))

    now_ms = int(time.time() * 1000)

    if now_ms - form_time < MIN_FORM_TIME_MS:
        flash("Formularz wysłany zbyt szybko. Spróbuj ponownie.", "error")
        return redirect(url_for("home", _anchor="kontakt"))

    # =========================
    # DANE Z FORMULARZA
    # =========================
    name = (request.form.get("name") or "").strip()
    phone = (request.form.get("phone") or "").strip()
    email = (request.form.get("email") or "").strip()
    product = (request.form.get("product") or "").strip()
    quantity = (request.form.get("quantity") or "").strip()
    pickup_date = (request.form.get("pickup_date") or "").strip()
    message = (request.form.get("message") or "").strip()

    # =========================
    # WALIDACJA
    # =========================
    errors = []

    if len(name) < 2:
        errors.append("Podaj imię i nazwisko.")

    if len(phone) < 7:
        errors.append("Podaj poprawny numer telefonu.")

    if not product:
        errors.append("Wybierz produkt.")

    if not quantity:
        errors.append("Podaj ilość.")

    if email and "@" not in email:
        errors.append("Podaj poprawny adres e-mail.")

    if len(message) > 2000:
        errors.append("Wiadomość jest za długa.")

    if errors:
        for err in errors:
            flash(err, "error")
        return redirect(url_for("home", _anchor="kontakt"))

    # =========================
    # TREŚĆ MAILA
    # =========================
    subject = f"Nowe zamówienie ze strony – {name}"

    body = f"""
NOWE ZAMÓWIENIE ZE STRONY

DANE KLIENTA
Imię i nazwisko: {name}
Telefon: {phone}
E-mail: {email if email else "Nie podano"}

SZCZEGÓŁY ZAMÓWIENIA
Produkt: {product}
Ilość: {quantity}
Preferowana data odbioru: {pickup_date if pickup_date else "Nie podano"}

DODATKOWE INFORMACJE
{message if message else "Brak"}

---
Formularz masarniajastew.pl
""".strip()

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = MAIL_FROM
    msg["To"] = MAIL_TO

    if email:
        msg["Reply-To"] = email

    # =========================
    # WYSYŁKA MAILA
    # =========================
    try:

        if not SMTP_USERNAME or not SMTP_PASSWORD:
            raise ValueError("Brak SMTP w .env")

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:

            server.starttls()

            server.login(
                SMTP_USERNAME,
                SMTP_PASSWORD
            )

            server.sendmail(
                MAIL_FROM,
                [MAIL_TO],
                msg.as_string()
            )

        flash("Formularz wysłany. Skontaktujemy się z Tobą w sprawie zamówienia.", "success")

    except Exception as e:

        print(f"[FORM ERROR] {e}")

        flash(
            "Nie udało się wysłać formularza. Spróbuj później lub zadzwoń.",
            "error"
        )

    return redirect(url_for("home", _anchor="kontakt"))


if __name__ == "__main__":
    app.run(debug=True)