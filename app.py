from flask import Flask, render_template, request, redirect, url_for, send_file
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os, datetime, sqlite3

app = Flask(__name__)
os.makedirs("invoices", exist_ok=True)

def init_db():
    conn = sqlite3.connect("invoices.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_no TEXT,
        customer_name TEXT,
        customer_phone TEXT,
        total REAL,
        date TEXT,
        filename TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    customer_name = request.form["customer_name"]
    customer_phone = request.form["customer_phone"]
    business_name = request.form["business_name"]
    item_names = request.form.getlist("item_name[]")
    item_qtys = request.form.getlist("item_qty[]")
    item_prices = request.form.getlist("item_price[]")
    invoice_no = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"invoices/invoice_{invoice_no}.pdf"
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    c.setFillColorRGB(0.18, 0.8, 0.44)
    c.rect(0, height-120, width, 120, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 28)
    c.drawString(40, height-60, business_name)
    c.setFont("Helvetica", 13)
    c.drawString(40, height-85, "INVOICE")
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica", 11)
    c.drawString(40, height-150, f"Invoice No: INV-{invoice_no}")
    c.drawString(40, height-170, f"Date: {datetime.date.today()}")
    c.drawString(40, height-200, f"Customer: {customer_name}")
    c.drawString(40, height-220, f"Phone: {customer_phone}")
    c.setFillColorRGB(0.18, 0.8, 0.44)
    c.rect(40, height-270, width-80, 25, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, height-260, "Item")
    c.drawString(280, height-260, "Qty")
    c.drawString(350, height-260, "Price")
    c.drawString(450, height-260, "Total")
    y = height - 295
    grand_total = 0
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica", 11)
    for i, (name, qty, price) in enumerate(zip(item_names, item_qtys, item_prices)):
        qty = int(qty)
        price = float(price)
        total = qty * price
        grand_total += total
        if i % 2 == 0:
            c.setFillColorRGB(0.95, 0.95, 0.95)
            c.rect(40, y-5, width-80, 20, fill=1, stroke=0)
        c.setFillColorRGB(0, 0, 0)
        c.drawString(50, y, name)
        c.drawString(280, y, str(qty))
        c.drawString(350, y, f"Rs. {price:.2f}")
        c.drawString(450, y, f"Rs. {total:.2f}")
        y -= 25
    c.setFillColorRGB(0.18, 0.8, 0.44)
    c.rect(350, y-35, width-390, 30, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(360, y-20, f"Grand Total: Rs. {grand_total:.2f}")
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.setFont("Helvetica", 9)
    c.drawString(40, 40, "Thank you for your business!")
    c.save()
    conn = sqlite3.connect("invoices.db")
    cur = conn.cursor()
    cur.execute("INSERT INTO invoices (invoice_no, customer_name, customer_phone, total, date, filename) VALUES (?,?,?,?,?,?)",
                (invoice_no, customer_name, customer_phone, grand_total, str(datetime.date.today()), filename))
    conn.commit()
    conn.close()
    whatsapp_msg = f"Namaskar {customer_name} ji! Aapki invoice ready hai. Total: Rs. {grand_total:.2f}. Dhanyavaad!"
    whatsapp_url = f"https://wa.me/91{customer_phone}?text={whatsapp_msg.replace(' ', '%20')}"
    return render_template("success.html", filename=filename, invoice_no=invoice_no,
                           total=grand_total, whatsapp_url=whatsapp_url, customer_name=customer_name)

@app.route("/download/<invoice_no>")
def download(invoice_no):
    filename = f"invoices/invoice_{invoice_no}.pdf"
    return send_file(filename, as_attachment=True)

@app.route("/invoices")
def all_invoices():
    conn = sqlite3.connect("invoices.db")
    cur = conn.cursor()
    cur.execute("SELECT * FROM invoices ORDER BY id DESC")
    invoices = cur.fetchall()
    conn.close()
    return render_template("invoices.html", invoices=invoices)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)