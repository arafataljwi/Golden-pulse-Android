# Golden Pulse Android - starter port from the Windows Tkinter app
# Client branding: بئر علي حسين
# Built with Kivy + SQLite; no Tkinter dependencies.

import os, sqlite3, uuid
from datetime import datetime
from kivy.app import App
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.core.text import LabelBase
from kivy.resources import resource_add_path
# Golden Pulse Arabic font
FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "GoldenPulseUI-Regular.ttf")

if os.path.exists(FONT_PATH):
    LabelBase.register(
        name="GoldenPulseArabic",
        fn_regular=FONT_PATH
    )
    ARABIC_FONT = "GoldenPulseArabic"
else:
    ARABIC_FONT = "Roboto"

NAVY = (15/255, 23/255, 42/255, 1)
PANEL = (30/255, 41/255, 59/255, 1)
GOLD = (212/255, 175/255, 55/255, 1)
WHITE = (1, 1, 1, 1)
MUTED = (0.75, 0.80, 0.87, 1)

def now_parts():
    d = datetime.now()
    return d.strftime("%Y-%m-%d"), d.strftime("%H:%M:%S")

class Store:
    def __init__(self, path):
        self.path = path
        self.init_db()

    def connect(self):
        return sqlite3.connect(self.path)

    def init_db(self):
        with self.connect() as c:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS sales (
                id TEXT PRIMARY KEY, no TEXT, date TEXT, time TEXT,
                customer TEXT, owner TEXT DEFAULT '', phone TEXT, size TEXT,
                pay TEXT, currency TEXT, qty REAL, price REAL, discount REAL, total REAL
            );
            CREATE TABLE IF NOT EXISTS pay (
                id TEXT PRIMARY KEY, no TEXT, date TEXT, name TEXT,
                amount REAL, currency TEXT, method TEXT, note TEXT
            );
            CREATE TABLE IF NOT EXISTS rec (
                id TEXT PRIMARY KEY, no TEXT, date TEXT, name TEXT,
                amount REAL, currency TEXT, method TEXT, note TEXT
            );
            CREATE TABLE IF NOT EXISTS debt_payments (
                id TEXT PRIMARY KEY, no TEXT, date TEXT, time TEXT,
                customer TEXT NOT NULL, phone TEXT, amount REAL NOT NULL,
                currency TEXT NOT NULL, method TEXT, note TEXT
            );
            """)
            cols = {r[1] for r in c.execute("PRAGMA table_info(sales)").fetchall()}
            if "owner" not in cols:
                c.execute("ALTER TABLE sales ADD COLUMN owner TEXT DEFAULT ''")

    def add_sale(self, d):
        with self.connect() as c:
            c.execute("""INSERT INTO sales
            (id,no,date,time,customer,owner,phone,size,pay,currency,qty,price,discount,total)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (str(uuid.uuid4()), d["no"], d["date"], d["time"], d["customer"], d["owner"],
             d["phone"], d["size"], d["pay"], d["currency"], d["qty"], d["price"],
             d["discount"], d["total"]))

    def add_voucher(self, table, d):
        with self.connect() as c:
            c.execute(f"INSERT INTO {table} VALUES (?,?,?,?,?,?,?,?)",
                      (str(uuid.uuid4()), d["no"], d["date"], d["name"], d["amount"],
                       d["currency"], d["method"], d["note"]))

    def add_debt_payment(self, d):
        with self.connect() as c:
            c.execute("""INSERT INTO debt_payments
            (id,no,date,time,customer,phone,amount,currency,method,note)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (str(uuid.uuid4()),d["no"],d["date"],d["time"],d["customer"],d["phone"],
             d["amount"],d["currency"],d["method"],d["note"]))

    def rows(self, table):
        with self.connect() as c:
            c.row_factory = sqlite3.Row
            return [dict(r) for r in c.execute(f"SELECT * FROM {table} ORDER BY date DESC").fetchall()]

    def summary(self):
        with self.connect() as c:
            sales = c.execute("SELECT COALESCE(SUM(total),0) FROM sales").fetchone()[0]
            count = c.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
            rec = c.execute("SELECT COALESCE(SUM(amount),0) FROM rec").fetchone()[0]
            pay = c.execute("SELECT COALESCE(SUM(amount),0) FROM pay").fetchone()[0]
            debt_paid = c.execute("SELECT COALESCE(SUM(amount),0) FROM debt_payments").fetchone()[0]
            return sales, count, rec, pay, debt_paid

class Field(TextInput):
    def __init__(self, hint, **kwargs):
        super().__init__(
            hint_text=hint,
            multiline=False,
            size_hint_y=None,
            height=dp(44),
            padding=(dp(10), dp(10)),
            font_name=ARABIC_FONT,
            **kwargs
        )
class GoldenPulseApp(App):
    def build(self):
        self.title = "Golden Pulse - بئر علي حسين"
        Window.clearcolor = NAVY
        self.store = Store(os.path.join(self.user_data_dir, "golden_pulse.db"))
        self.root_box = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(10))
        self.header = Label(text="[b]بئر علي حسين[/b]\n[color=gold]GOLDEN PULSE[/color]",
                            markup=True, font_size="22sp", size_hint_y=None, height=dp(65),
                            color=WHITE)
        self.root_box.add_widget(self.header)
        self.nav = GridLayout(cols=3, spacing=dp(5), size_hint_y=None, height=dp(92))
        for label, screen in [
            ("المبيعات", "sales"), ("سند قبض", "rec"), ("سند صرف", "pay"),
            ("سداد دين", "debt"), ("التقارير", "reports"), ("السجلات", "records")
        ]:
            b = Button(text=label, background_normal="", background_color=GOLD, color=NAVY,
                       font_size="15sp")
            b.bind(on_release=lambda inst, s=screen: self.show_screen(s))
            self.nav.add_widget(b)
        self.root_box.add_widget(self.nav)
        self.content = BoxLayout(orientation="vertical", spacing=dp(8))
        self.root_box.add_widget(self.content)
        self.show_screen("sales")
        return self.root_box

    def add_label(self, parent, text, height=34, color=WHITE, size=15):
    parent.add_widget(
        Label(
            text=text,
            size_hint_y=None,
            height=dp(height),
            color=color,
            halign="right",
            valign="middle",
            text_size=(Window.width - dp(40), None),
            font_size=f"{size}sp",
            font_name=ARABIC_FONT
        )
    )

    def show_screen(self, name):
        self.content.clear_widgets()
        if name == "sales":
            self.sales_screen()
        elif name in ("rec", "pay"):
            self.voucher_screen(name)
        elif name == "debt":
            self.debt_screen()
        elif name == "reports":
            self.reports_screen()
        else:
            self.records_screen()

    def form_shell(self, title):
        self.add_label(self.content, title, height=38, color=GOLD, size=20)
        scroll = ScrollView()
        form = BoxLayout(orientation="vertical", spacing=dp(7), padding=(dp(3), dp(4)),
                         size_hint_y=None)
        form.bind(minimum_height=form.setter("height"))
        scroll.add_widget(form)
        self.content.add_widget(scroll)
        return form

    def add_field(self, form, hint, key, fields, default=""):
        widget = Field(hint, text=default)
        fields[key] = widget
        form.add_widget(widget)
        return widget

    def add_spinner(self, form, values, key, fields, default=None):
        w = Spinner(text=default or values[0], values=values, size_hint_y=None, height=dp(44),
                    background_normal="", background_color=PANEL, color=WHITE)
        fields[key] = w
        form.add_widget(w)
        return w

    def save_button(self, form, label, callback):
        b = Button(text=label, size_hint_y=None, height=dp(48),
                   background_normal="", background_color=GOLD, color=NAVY,
                   font_size="17sp")
        b.bind(on_release=callback)
        form.add_widget(b)

    def notify(self, message):
        box = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(12))
        box.add_widget(Label(text=message, color=NAVY))
        close = Button(text="حسنًا", size_hint_y=None, height=dp(42),
                       background_normal="", background_color=GOLD, color=NAVY)
        box.add_widget(close)
        pop = Popup(title="Golden Pulse", content=box, size_hint=(.85, .32))
        close.bind(on_release=pop.dismiss)
        pop.open()

    def sales_screen(self):
        form = self.form_shell("فاتورة تعبئة مياه")
        f = {}
        self.add_field(form, "اسم العميل", "customer", f)
        self.add_field(form, "اسم صاحب الوايت (اختياري)", "owner", f)
        self.add_field(form, "رقم الهاتف", "phone", f)
        self.add_spinner(form, [str(x) for x in range(2000, 20001, 2000)], "size", f, "10000")
        self.add_spinner(form, ["نقدي", "آجل"], "pay", f, "نقدي")
        self.add_spinner(form, ["ريال يمني", "دولار", "ريال سعودي"], "currency", f, "ريال يمني")
        self.add_field(form, "الكمية", "qty", f, "1")
        self.add_field(form, "سعر الوحدة / التعبئة", "price", f, "0")
        self.add_field(form, "الخصم", "discount", f, "0")
        total_label = Label(text="الإجمالي: 0", size_hint_y=None, height=dp(34), color=GOLD, font_size="18sp")
        form.add_widget(total_label)
        def calc(*_):
            try: total_label.text = "الإجمالي: " + str(max(0, float(f["qty"].text or 0)*float(f["price"].text or 0)-float(f["discount"].text or 0)))
            except ValueError: total_label.text = "الإجمالي: —"
        for k in ("qty", "price", "discount"): f[k].bind(text=calc)
        def save(_):
            try:
                customer = f["customer"].text.strip()
                if not customer: raise ValueError("أدخل اسم العميل.")
                qty, price, discount = float(f["qty"].text or 0), float(f["price"].text or 0), float(f["discount"].text or 0)
                if qty <= 0 or price < 0 or discount < 0: raise ValueError("تحقق من الكمية والسعر والخصم.")
                date, tm = now_parts()
                number = "INV-" + datetime.now().strftime("%y%m%d%H%M%S")
                total = max(0, qty*price-discount)
                self.store.add_sale(dict(no=number,date=date,time=tm,customer=customer,
                    owner=f["owner"].text.strip(),phone=f["phone"].text.strip(),size=f["size"].text,
                    pay=f["pay"].text,currency=f["currency"].text,qty=qty,price=price,
                    discount=discount,total=total))
                self.notify(f"تم حفظ الفاتورة {number}\nالإجمالي: {total:g} {f['currency'].text}")
                self.show_screen("sales")
            except (ValueError, sqlite3.Error) as e: self.notify(str(e))
        self.save_button(form, "حفظ الفاتورة", save)

    def voucher_screen(self, table):
        title = "سند قبض" if table == "rec" else "سند صرف"
        prefix = "REC-" if table == "rec" else "PAY-"
        form = self.form_shell(title)
        f = {}
        self.add_field(form, "اسم العميل / المستفيد", "name", f)
        self.add_field(form, "المبلغ", "amount", f, "0")
        self.add_spinner(form, ["ريال يمني", "دولار", "ريال سعودي"], "currency", f, "ريال يمني")
        self.add_spinner(form, ["نقدي", "تحويل", "شيك"], "method", f, "نقدي")
        self.add_field(form, "البيان / الملاحظات", "note", f)
        def save(_):
            try:
                name = f["name"].text.strip()
                amount = float(f["amount"].text or 0)
                if not name: raise ValueError("أدخل الاسم.")
                if amount <= 0: raise ValueError("يجب أن يكون المبلغ أكبر من صفر.")
                date, _ = now_parts()
                no = prefix + datetime.now().strftime("%y%m%d%H%M%S")
                self.store.add_voucher(table, dict(no=no,date=date,name=name,amount=amount,
                    currency=f["currency"].text,method=f["method"].text,note=f["note"].text.strip()))
                self.notify(f"تم حفظ {title} رقم {no}")
                self.show_screen(table)
            except (ValueError, sqlite3.Error) as e: self.notify(str(e))
        self.save_button(form, "حفظ " + title, save)

    def debt_screen(self):
        form = self.form_shell("تسجيل سداد دين عميل")
        f = {}
        self.add_field(form, "اسم العميل", "customer", f)
        self.add_field(form, "رقم الهاتف", "phone", f)
        self.add_field(form, "المبلغ المسدد", "amount", f, "0")
        self.add_spinner(form, ["ريال يمني", "دولار", "ريال سعودي"], "currency", f, "ريال يمني")
        self.add_spinner(form, ["نقدي", "تحويل", "شيك"], "method", f, "نقدي")
        self.add_field(form, "ملاحظات", "note", f)
        def save(_):
            try:
                customer = f["customer"].text.strip()
                amount = float(f["amount"].text or 0)
                if not customer: raise ValueError("أدخل اسم العميل.")
                if amount <= 0: raise ValueError("أدخل مبلغًا أكبر من صفر.")
                date, tm = now_parts()
                no = "DPM-" + datetime.now().strftime("%y%m%d%H%M%S")
                self.store.add_debt_payment(dict(no=no,date=date,time=tm,customer=customer,
                    phone=f["phone"].text.strip(),amount=amount,currency=f["currency"].text,
                    method=f["method"].text,note=f["note"].text.strip()))
                self.notify("تم تسجيل سداد الدين " + no)
                self.show_screen("debt")
            except (ValueError, sqlite3.Error) as e: self.notify(str(e))
        self.save_button(form, "حفظ سداد الدين", save)

    def reports_screen(self):
        form = self.form_shell("التقارير والملخص")
        sales, count, rec, pay, debt_paid = self.store.summary()
        self.add_label(form, f"عدد فواتير المبيعات: {count}", height=42, size=17)
        self.add_label(form, f"إجمالي المبيعات: {sales:g}", height=42, color=GOLD, size=17)
        self.add_label(form, f"إجمالي سندات القبض: {rec:g}", height=42, size=17)
        self.add_label(form, f"إجمالي سندات الصرف: {pay:g}", height=42, size=17)
        self.add_label(form, f"إجمالي سداد الديون المسجل: {debt_paid:g}", height=42, size=17)
        self.add_label(form, "تنبيه: الإجماليات هنا تجمع العملات معًا؛ لا تستخدمها كرصيد محاسبي موحد عند تعدد العملات.", height=62, color=MUTED, size=12)

    def records_screen(self):
        form = self.form_shell("آخر السجلات")
        for table, title in [("sales","المبيعات"),("rec","سندات القبض"),("pay","سندات الصرف"),("debt_payments","سداد الديون")]:
            rows = self.store.rows(table)
            self.add_label(form, f"— {title}: {len(rows)} سجل —", height=38, color=GOLD, size=17)
            for row in rows[:15]:
                name = row.get("customer") or row.get("name") or "—"
                amount = row.get("total", row.get("amount", 0))
                no = row.get("no", "")
                date = row.get("date", "")
                self.add_label(form, f"{date} | {no} | {name} | {amount}", height=42, color=WHITE, size=12)

if __name__ == "__main__":
    GoldenPulseApp().run()
