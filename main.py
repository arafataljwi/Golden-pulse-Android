# Golden Pulse Android - updated Kivy + SQLite app
# Client: بئر علي حسين
# Arabic shaping uses arabic-reshaper + python-bidi when available.
# Default login: admin / 112233 (change before production use).

import os
import json
import sqlite3
import uuid
from datetime import datetime

from kivy.app import App
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    def ar_text(value):
        value = str(value)
        try:
            return get_display(arabic_reshaper.reshape(value), base_dir="R")
        except Exception:
            return value
except Exception:
    def ar_text(value):
        return str(value)

NAVY = (15/255, 23/255, 42/255, 1)
PANEL = (30/255, 41/255, 59/255, 1)
GOLD = (212/255, 175/255, 55/255, 1)
WHITE = (1, 1, 1, 1)
MUTED = (0.75, 0.80, 0.87, 1)
GREEN = (0.08, 0.62, 0.30, 1)
RED = (0.78, 0.12, 0.14, 1)
BLUE = (0.10, 0.38, 0.75, 1)
PURPLE = (0.42, 0.24, 0.68, 1)
CYAN = (0.04, 0.55, 0.70, 1)

APP_FONT = "Roboto"
FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "GoldenPulseUI-Regular.ttf")
if os.path.exists(FONT_PATH):
    try:
        LabelBase.register(name="GoldenPulseArabic", fn_regular=FONT_PATH)
        APP_FONT = "GoldenPulseArabic"
    except Exception:
        pass

def now_parts():
    d = datetime.now()
    return d.strftime("%Y-%m-%d"), d.strftime("%H:%M:%S")

def money(value):
    try:
        return f"{float(value):,.2f}".rstrip("0").rstrip(".")
    except Exception:
        return str(value)

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
            if "phone" not in cols:
                c.execute("ALTER TABLE sales ADD COLUMN phone TEXT DEFAULT ''")

    def add_sale(self, d):
        # Keep customer and water-truck owner in separate columns.
        with self.connect() as c:
            c.execute("""INSERT INTO sales
            (id,no,date,time,customer,owner,phone,size,pay,currency,qty,price,discount,total)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (str(uuid.uuid4()), d["no"], d["date"], d["time"], d["customer"], d["owner"],
             d["phone"], d["size"], d["pay"], d["currency"], d["qty"], d["price"],
             d["discount"], d["total"]))

    def add_voucher(self, table, d):
        if table not in ("pay", "rec"):
            raise ValueError("Invalid voucher type")
        with self.connect() as c:
            c.execute(f"INSERT INTO {table} VALUES (?,?,?,?,?,?,?,?)",
                      (str(uuid.uuid4()), d["no"], d["date"], d["name"], d["amount"],
                       d["currency"], d["method"], d["note"]))

    def add_debt_payment(self, d):
        with self.connect() as c:
            c.execute("""INSERT INTO debt_payments
            (id,no,date,time,customer,phone,amount,currency,method,note)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (str(uuid.uuid4()), d["no"], d["date"], d["time"], d["customer"], d["phone"],
             d["amount"], d["currency"], d["method"], d["note"]))

    def rows(self, table):
        if table not in ("sales", "pay", "rec", "debt_payments"):
            raise ValueError("Invalid table")
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
            hint_text=ar_text(hint),
            multiline=False,
            size_hint_y=None,
            height=dp(46),
            padding=(dp(10), dp(10)),
            font_name=APP_FONT,
            font_size="16sp",
            halign="right",
            foreground_color=NAVY,
            **kwargs
        )

class GoldenPulseApp(App):
    def build(self):
        self.title = "Golden Pulse - بئر علي حسين"
        Window.clearcolor = NAVY
        self.store = Store(os.path.join(self.user_data_dir, "golden_pulse.db"))
        self.root_box = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(10))
        self.show_login()
        return self.root_box

    def make_label(self, text, height=38, color=WHITE, size=15, markup=False):
        return Label(
            text=ar_text(text), markup=markup, size_hint_y=None, height=dp(height),
            color=color, halign="right", valign="middle",
            text_size=(Window.width-dp(40), None), font_size=f"{size}sp",
            font_name=APP_FONT
        )

    def make_button(self, text, callback, height=48, font_size=16, color=GOLD, text_color=NAVY):
        b = Button(text=ar_text(text), size_hint_y=None, height=dp(height),
                   background_normal="", background_color=color, color=text_color,
                   font_size=f"{font_size}sp", font_name=APP_FONT)
        b.bind(on_release=callback)
        return b

    def show_login(self):
        self.root_box.clear_widgets()
        self.root_box.add_widget(self.make_label("GOLDEN PULSE", 58, GOLD, 29))
        self.root_box.add_widget(self.make_label("بئر علي حسين", 42, WHITE, 22))
        self.root_box.add_widget(self.make_label("النظام المحاسبي المتكامل", 40, MUTED, 17))
        self.root_box.add_widget(self.make_label("تسجيل الدخول إلى النظام", 42, GOLD, 19))
        form = BoxLayout(orientation="vertical", spacing=dp(12), padding=(dp(12), dp(12)))
        self.login_user = Field("اسم المستخدم")
        self.login_pass = Field("كلمة المرور", password=True)
        form.add_widget(self.login_user)
        form.add_widget(self.login_pass)
        form.add_widget(self.make_button("الدخول إلى النظام", self.login, 52, 18, color=GREEN, text_color=WHITE))
        self.root_box.add_widget(form)
        self.root_box.add_widget(self.make_label("للدخول الأول: admin / 112233", 32, MUTED, 12))

    def login(self, *_):
        # Initial prototype credentials. Replace with managed credentials before production.
        if self.login_user.text.strip() == "admin" and self.login_pass.text == "112233":
            self.show_dashboard()
        else:
            self.notify("اسم المستخدم أو كلمة المرور غير صحيحة")

    def show_dashboard(self):
        self.root_box.clear_widgets()
        self.root_box.add_widget(self.make_label("GOLDEN PULSE", 42, GOLD, 25))
        self.root_box.add_widget(self.make_label("بئر علي حسين | النظام المحاسبي المتكامل", 38, WHITE, 17))
        self.nav = GridLayout(cols=2, spacing=dp(8), size_hint_y=None, height=dp(222))
        sections = [
            ("المبيعات", "sales", GOLD), ("سند قبض", "rec", GREEN),
            ("سند صرف", "pay", BLUE), ("الديون / سداد دين", "debt", RED),
            ("التقارير", "reports", PURPLE), ("النسخة الاحتياطية", "backup", CYAN),
        ]
        for label, screen, color in sections:
            self.nav.add_widget(self.make_button(label, lambda inst, s=screen: self.show_screen(s), 64, 15,
                                                 color=color, text_color=WHITE))
        self.root_box.add_widget(self.nav)
        self.content = BoxLayout(orientation="vertical", spacing=dp(8))
        self.root_box.add_widget(self.content)
        self.footer = self.make_button("خروج", self.footer_action, 44, 16, color=RED, text_color=WHITE)
        self.root_box.add_widget(self.footer)
        self.current_screen = "dashboard"
        self.show_screen("sales")

    def footer_action(self, *_):
        # The red footer button exits the current session and returns to login.
        self.show_login()

    def logout(self, *_):
        self.show_login()

    def add_label(self, parent, text, height=34, color=WHITE, size=15):
        parent.add_widget(self.make_label(text, height, color, size))

    def show_screen(self, name):
        self.current_screen = name
        self.content.clear_widgets()
        if name == "sales":
            self.sales_screen()
        elif name in ("rec", "pay"):
            self.voucher_screen(name)
        elif name == "debt":
            self.debt_screen()
        elif name == "reports":
            self.reports_screen()
        elif name == "backup":
            self.backup_screen()
        else:
            self.records_screen()

    def form_shell(self, title):
        self.add_label(self.content, title, height=40, color=GOLD, size=20)
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
        vals = [ar_text(v) for v in values]
        w = Spinner(text=ar_text(default or values[0]), values=vals, size_hint_y=None, height=dp(46),
                    background_normal="", background_color=PANEL, color=WHITE,
                    font_name=APP_FONT, font_size="16sp")
        fields[key] = w
        form.add_widget(w)
        return w

    def save_button(self, form, label, callback):
        form.add_widget(self.make_button(label, callback, 50, 17))

    def notify(self, message):
        box = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(12))
        box.add_widget(self.make_label(message, 70, NAVY, 15))
        close = self.make_button("حسنًا", lambda *_: pop.dismiss(), 42)
        box.add_widget(close)
        pop = Popup(title="Golden Pulse", content=box, size_hint=(.88, .42))
        close.bind(on_release=pop.dismiss)
        pop.open()

    def sales_screen(self):
        form = self.form_shell("فاتورة تعبئة مياه")
        f = {}

        # Top row: invoice number and phone side by side.
        top = GridLayout(cols=2, spacing=dp(6), size_hint_y=None, height=dp(46))
        no_widget = Field("رقم الفاتورة", text="INV-" + datetime.now().strftime("%y%m%d%H%M%S%f"))
        no_widget.readonly = True
        phone_widget = Field("رقم الهاتف", input_filter=None)
        f["no"] = no_widget
        f["phone"] = phone_widget
        top.add_widget(no_widget)
        top.add_widget(phone_widget)
        form.add_widget(top)

        self.add_field(form, "اسم العميل", "customer", f)
        self.add_field(form, "اسم صاحب الوايت", "owner", f)
        self.add_spinner(form, [str(x) for x in range(2000, 20001, 2000)], "size", f, "10000")
        self.add_spinner(form, ["نقدي", "آجل"], "pay", f, "نقدي")
        self.add_spinner(form, ["ريال يمني", "دولار", "ريال سعودي"], "currency", f, "ريال يمني")
        self.add_field(form, "الكمية", "qty", f, "1")
        self.add_field(form, "سعر الوحدة / التعبئة", "price", f, "0")
        self.add_field(form, "الخصم", "discount", f, "0")
        total_label = self.make_label("الإجمالي: 0", 42, GOLD, 19)
        form.add_widget(total_label)

        def calc(*_):
            try:
                total = max(0, float(f["qty"].text or 0) * float(f["price"].text or 0) - float(f["discount"].text or 0))
                total_label.text = ar_text("الإجمالي: " + money(total) + " " + f["currency"].text)
            except (ValueError, TypeError):
                total_label.text = ar_text("الإجمالي: —")
        for k in ("qty", "price", "discount"):
            f[k].bind(text=calc)
        f["currency"].bind(text=calc)

        def save(_):
            try:
                customer = f["customer"].text.strip()
                owner = f["owner"].text.strip()
                if not customer:
                    raise ValueError("أدخل اسم العميل.")
                if not owner:
                    raise ValueError("أدخل اسم صاحب الوايت.")
                qty = float(f["qty"].text or 0)
                price = float(f["price"].text or 0)
                discount = float(f["discount"].text or 0)
                if qty <= 0 or price < 0 or discount < 0 or discount > qty * price:
                    raise ValueError("تحقق من الكمية والسعر والخصم؛ لا يجوز أن يتجاوز الخصم الإجمالي.")
                date, tm = now_parts()
                number = f["no"].text.strip() or ("INV-" + datetime.now().strftime("%y%m%d%H%M%S%f"))
                total = max(0, qty * price - discount)
                data = dict(no=number, date=date, time=tm, customer=customer, owner=owner,
                            phone=f["phone"].text.strip(), size=f["size"].text,
                            pay=f["pay"].text, currency=f["currency"].text,
                            qty=qty, price=price, discount=discount, total=total)
                self.store.add_sale(data)
                self.show_invoice(data)
                # prepare a fresh unique invoice number for the next sale
                f["no"].text = "INV-" + datetime.now().strftime("%y%m%d%H%M%S%f")
            except (ValueError, sqlite3.Error) as e:
                self.notify(str(e))
        self.save_button(form, "حفظ الفاتورة وعرض فاتورة العميل", save)

    def invoice_text(self, d):
        return (
            "بئر علي حسين\n"
            "GOLDEN PULSE\n"
            "فاتورة تعبئة مياه\n"
            "--------------------------------\n"
            f"رقم الفاتورة: {d['no']}\n"
            f"التاريخ: {d['date']}  {d['time']}\n"
            f"اسم العميل: {d.get('customer', '-')}\n"
            f"اسم صاحب الوايت: {d['owner']}\n"
            f"رقم الهاتف: {d['phone'] or '-'}\n"
            f"حجم الوايت: {d['size']} لتر\n"
            f"نوع الدفع: {d['pay']}\n"
            f"الكمية: {d['qty']:g}\n"
            f"سعر الوحدة: {money(d['price'])}\n"
            f"الخصم: {money(d['discount'])}\n"
            "--------------------------------\n"
            f"الإجمالي: {money(d['total'])} {d['currency']}\n"
            "شكرًا لتعاملكم معنا"
        )

    def show_invoice(self, d):
        box = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(10))
        inv = Label(text=ar_text(self.invoice_text(d)), color=NAVY, font_name=APP_FONT,
                    font_size="15sp", halign="right", valign="middle",
                    text_size=(Window.width*0.76, None))
        box.add_widget(inv)
        actions = GridLayout(cols=2, spacing=dp(6), size_hint_y=None, height=dp(48))
        pop = Popup(title="فاتورة بئر علي حسين", content=box, size_hint=(.95, .85))
        print_btn = self.make_button("طباعة / مشاركة", lambda *_: self.share_invoice(d), 46, 13)
        close_btn = self.make_button("إغلاق", lambda *_: pop.dismiss(), 46, 13)
        actions.add_widget(print_btn)
        actions.add_widget(close_btn)
        box.add_widget(actions)
        pop.open()

    def share_invoice(self, d):
        text = self.invoice_text(d)
        try:
            from jnius import autoclass
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Intent = autoclass("android.content.Intent")
            String = autoclass("java.lang.String")
            activity = PythonActivity.mActivity
            intent = Intent()
            intent.setAction(Intent.ACTION_SEND)
            intent.setType("text/plain")
            intent.putExtra(Intent.EXTRA_TEXT, String(text))
            chooser = Intent.createChooser(intent, String("طباعة أو مشاركة الفاتورة"))
            activity.startActivity(chooser)
            self.notify("اختر تطبيق الطباعة أو المشاركة من القائمة التي ظهرت.")
        except Exception:
            self.notify("تعذّر فتح قائمة الطباعة تلقائيًا. يمكنك استخدام مشاركة الفاتورة من نظام أندرويد بعد تفعيل تطبيق الطابعة.")

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
                if not name:
                    raise ValueError("أدخل الاسم.")
                if amount <= 0:
                    raise ValueError("يجب أن يكون المبلغ أكبر من صفر.")
                date, _ = now_parts()
                no = prefix + datetime.now().strftime("%y%m%d%H%M%S")
                self.store.add_voucher(table, dict(no=no, date=date, name=name, amount=amount,
                    currency=f["currency"].text, method=f["method"].text, note=f["note"].text.strip()))
                self.notify(f"تم حفظ {title} رقم {no}")
                self.show_screen(table)
            except (ValueError, sqlite3.Error) as e:
                self.notify(str(e))
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
                if not customer:
                    raise ValueError("أدخل الاسم.")
                if amount <= 0:
                    raise ValueError("أدخل مبلغًا أكبر من صفر.")
                date, tm = now_parts()
                no = "DPM-" + datetime.now().strftime("%y%m%d%H%M%S")
                self.store.add_debt_payment(dict(no=no, date=date, time=tm, customer=customer,
                    phone=f["phone"].text.strip(), amount=amount, currency=f["currency"].text,
                    method=f["method"].text, note=f["note"].text.strip()))
                self.notify("تم تسجيل سداد الدين " + no)
                self.show_screen("debt")
            except (ValueError, sqlite3.Error) as e:
                self.notify(str(e))
        self.save_button(form, "حفظ سداد الدين", save)

    def reports_screen(self):
        form = self.form_shell("التقارير والملخص")
        sales, count, rec, pay, debt_paid = self.store.summary()
        self.add_label(form, f"عدد فواتير المبيعات: {count}", height=42, size=17)
        self.add_label(form, f"إجمالي المبيعات: {money(sales)}", height=42, color=GOLD, size=17)
        self.add_label(form, f"إجمالي سندات القبض: {money(rec)}", height=42, size=17)
        self.add_label(form, f"إجمالي سندات الصرف: {money(pay)}", height=42, size=17)
        self.add_label(form, f"إجمالي سداد الديون المسجل: {money(debt_paid)}", height=42, size=17)
        self.add_label(form, "تنبيه: الإجماليات تجمع العملات معًا؛ لا تستخدمها كرصيد موحد عند تعدد العملات.",
                       height=68, color=MUTED, size=12)

    def backup_screen(self):
        form = self.form_shell("النسخة الاحتياطية والتخزين المحلي")
        self.add_label(form, "يحفظ التطبيق البيانات تلقائيًا داخل قاعدة SQLite على الهاتف.",
                       height=60, color=WHITE, size=14)
        self.add_label(form, "أنشئ نسخة احتياطية دورية واحتفظ بها خارج الهاتف.",
                       height=52, color=MUTED, size=13)
        form.add_widget(self.make_button("إنشاء نسخة احتياطية ومشاركتها", self.export_backup, 52, 15,
                                         color=CYAN, text_color=WHITE))
        form.add_widget(self.make_button("استعادة نسخة احتياطية من ملف", self.choose_backup, 52, 15,
                                         color=BLUE, text_color=WHITE))
        form.add_widget(self.make_button("عرض آخر السجلات", lambda *_: self.show_screen("records"), 48, 14,
                                         color=PURPLE, text_color=WHITE))

    def export_backup(self, *_):
        try:
            payload = {"app": "Golden Pulse", "client": "بئر علي حسين",
                       "created_at": datetime.now().isoformat(timespec="seconds"), "tables": {}}
            for table in ("sales", "pay", "rec", "debt_payments"):
                payload["tables"][table] = self.store.rows(table)
            filename = "GoldenPulse_Backup_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".json"
            path = os.path.join(self.user_data_dir, filename)
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, ensure_ascii=False, indent=2)
            # Open Android share sheet so the user can save/send the backup outside app storage.
            try:
                from jnius import autoclass
                PythonActivity = autoclass("org.kivy.android.PythonActivity")
                Intent = autoclass("android.content.Intent")
                String = autoclass("java.lang.String")
                activity = PythonActivity.mActivity
                intent = Intent()
                intent.setAction(Intent.ACTION_SEND)
                intent.setType("text/plain")
                intent.putExtra(Intent.EXTRA_TEXT, String(json.dumps(payload, ensure_ascii=False, indent=2)))
                chooser = Intent.createChooser(intent, String("نسخة Golden Pulse الاحتياطية"))
                activity.startActivity(chooser)
                self.notify("تم إنشاء النسخة محليًا. استخدم قائمة المشاركة لحفظ نسخة خارج الهاتف أيضًا.")
            except Exception:
                self.notify("تم إنشاء النسخة الاحتياطية داخل مجلد التطبيق:\n" + path)
        except Exception as e:
            self.notify("تعذر إنشاء النسخة الاحتياطية: " + str(e))

    def choose_backup(self, *_):
        box = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(8))
        chooser = FileChooserListView(path=self.user_data_dir, filters=["*.json"],
                                      size_hint=(1, 1))
        box.add_widget(chooser)
        actions = GridLayout(cols=2, spacing=dp(6), size_hint_y=None, height=dp(46))
        popup = Popup(title="اختيار ملف النسخة الاحتياطية", content=box, size_hint=(.96, .88))
        def cancel(*_):
            popup.dismiss()
        def restore(*_):
            if not chooser.selection:
                self.notify("اختر ملف JSON أولًا.")
                return
            path = chooser.selection[0]
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    payload = json.load(fh)
                tables = payload.get("tables", {})
                if not isinstance(tables, dict):
                    raise ValueError("تنسيق النسخة الاحتياطية غير صحيح.")
                # Import as additional records; original data is not deleted.
                with self.store.connect() as c:
                    for table in ("sales", "pay", "rec", "debt_payments"):
                        rows = tables.get(table, [])
                        if not isinstance(rows, list):
                            continue
                        cols = {r[1] for r in c.execute(f"PRAGMA table_info({table})").fetchall()}
                        for row in rows:
                            if not isinstance(row, dict):
                                continue
                            clean = {k: v for k, v in row.items() if k in cols}
                            if "id" not in clean:
                                clean["id"] = str(uuid.uuid4())
                            # Avoid replacing existing entries with the same ID.
                            keys = list(clean.keys())
                            sql = f"INSERT OR IGNORE INTO {table} ({','.join(keys)}) VALUES ({','.join(['?']*len(keys))})"
                            c.execute(sql, [clean[k] for k in keys])
                popup.dismiss()
                self.notify("تمت استعادة البيانات. السجلات الموجودة لم تُحذف.")
                self.show_screen("records")
            except Exception as e:
                self.notify("فشلت الاستعادة: " + str(e))
        actions.add_widget(self.make_button("استعادة", restore, 44, 14, color=GREEN, text_color=WHITE))
        actions.add_widget(self.make_button("إلغاء", cancel, 44, 14, color=RED, text_color=WHITE))
        box.add_widget(actions)
        popup.open()

    def records_screen(self):
        form = self.form_shell("آخر السجلات")
        for table, title in [("sales", "المبيعات"), ("rec", "سندات القبض"),
                             ("pay", "سندات الصرف"), ("debt_payments", "سداد الديون")]:
            rows = self.store.rows(table)
            self.add_label(form, f"— {title}: {len(rows)} سجل —", height=38, color=GOLD, size=17)
            for row in rows[:15]:
                name = row.get("customer") or row.get("owner") or row.get("name") or "—"
                amount = row.get("total", row.get("amount", 0))
                no = row.get("no", "")
                date = row.get("date", "")
                self.add_label(form, f"{date} | {no} | {name} | {money(amount)}", height=44, color=WHITE, size=12)

if __name__ == "__main__":
    GoldenPulseApp().run()
