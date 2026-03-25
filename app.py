import os
import smtplib
import time
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.header import Header

from flask import Flask, render_template, request, redirect, url_for, flash

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


def build_order_id() -> str:
    """
    Unikalny identyfikator zamówienia do tematu i treści wiadomości.
    """
    return datetime.now(timezone.utc).strftime("JASTEW-%Y%m%d-%H%M%S")


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
    pickup_date = (request.form.get("pickup_date") or "").strip()
    message = (request.form.get("message") or "").strip()

    products = request.form.getlist("product[]")
    quantities = request.form.getlist("quantity[]")

    order_items = []

    for product, quantity in zip(products, quantities):
        product = (product or "").strip()
        quantity = (quantity or "").strip()

        if product or quantity:
            order_items.append({
                "product": product,
                "quantity": quantity
            })

    # =========================
    # WALIDACJA
    # =========================
    errors = []

    if len(name) < 2:
        errors.append("Podaj imię i nazwisko.")

    if len(phone) < 7:
        errors.append("Podaj poprawny numer telefonu.")

    if not order_items:
        errors.append("Dodaj co najmniej jeden produkt.")

    for i, item in enumerate(order_items, start=1):
        if not item["product"]:
            errors.append(f"Pozycja {i}: wybierz produkt.")
        if not item["quantity"]:
            errors.append(f"Pozycja {i}: podaj ilość.")

    if email and "@" not in email:
        errors.append("Podaj poprawny adres e-mail.")

    if len(message) > 2000:
        errors.append("Wiadomość jest za długa.")

    if errors:
        for err in errors:
            flash(err, "error")
        return redirect(url_for("home", _anchor="kontakt"))

    # =========================
    # BUDOWANIE ZAMÓWIENIA
    # =========================
    order_id = build_order_id()
    submitted_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    order_lines = []
    for i, item in enumerate(order_items, start=1):
        order_lines.append(f"{i}. {item['product']} — {item['quantity']}")

    order_summary = "\n".join(order_lines)

    # =========================
    # TREŚĆ MAILA DO FIRMY
    # =========================
    subject = f"Nowe zamówienie {order_id} – {name}"

    body = f"""
NOWE ZAMÓWIENIE ZE STRONY

ID ZAMÓWIENIA
{order_id}

DATA WYSŁANIA
{submitted_at}

DANE KLIENTA
Imię i nazwisko: {name}
Telefon: {phone}
E-mail: {email if email else "Nie podano"}

SZCZEGÓŁY ZAMÓWIENIA
{order_summary}
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
            server.login(SMTP_USERNAME, SMTP_PASSWORD)

            # =========================
            # MAIL DO FIRMY
            # =========================
            server.sendmail(
                MAIL_FROM,
                [MAIL_TO],
                msg.as_string()
            )

            # =========================
            # MAIL DO KLIENTA
            # =========================
            if email:
                client_subject = f"Potwierdzenie zapytania {order_id} – Masarnia JASTEW"

                client_body = f"""
Dziękujemy za kontakt.

Otrzymaliśmy Twoje zapytanie dotyczące zamówienia.

ID zamówienia:
{order_id}

Szczegóły:
{order_summary}

Preferowana data odbioru: {pickup_date if pickup_date else "Nie podano"}

Skontaktujemy się z Tobą możliwie szybko,
aby potwierdzić dostępność i termin odbioru.

Masarnia JASTEW
Jastew 162
tel. 694 810 691
e-mail: kontakt@masarniajastew.pl
""".strip()

                client_msg = MIMEText(client_body, "plain", "utf-8")
                client_msg["Subject"] = Header(client_subject, "utf-8")
                client_msg["From"] = MAIL_FROM
                client_msg["To"] = email

                server.sendmail(
                    MAIL_FROM,
                    [email],
                    client_msg.as_string()
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