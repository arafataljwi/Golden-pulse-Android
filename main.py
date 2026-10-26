# Golden Pulse Android - Professional Edition
# Client: بئر علي حسين
# Arabic shaping uses arabic-reshaper + python-bidi when available.

import os
import sqlite3
import uuid
import shutil
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

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    def ar_text(value):
        value = str(value)
        try:
            return get_display(arabic_reshaper.reshape(value))
        except Exception:
            return value
except Exception:
    def ar_text(value):
        return str(value)

# الألوان والتصميم الأنيق
NAVY = (15/255, 23/255, 42/255, 1)          # خلفية داكنة فخمة
PANEL = (30/255, 41/255, 59/255, 1)         # لوحة فرعية
GOLD = (212/255, 175/255, 55/255, 1)        # ذهبي أنيق
GREEN = (46/255, 204/255, 113/255, 1)       # أخضر للدخول والحفظ
RED = (231/255, 76/255, 60/255, 1)          # أحمر للخروج والرجوع
WHITE = (1, 1, 1, 1)
MUTED = (0.75, 0.80, 0.87, 1)

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
        with self.connect() as c:
            c.execute("""INSERT INTO sales
            (id,no,date,time,customer,owner,phone,size,pay,currency,qty,price,discount,total)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (str(uuid.uuid4()), d["no"], d["date"], d["time"], d["owner"], d["owner"],
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
            background_color=(0.95, 0.95, 0.95, 1),
            cursor_color=GOLD,
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

    def make_button(self, text, callback, height=48, font_size=16, bg_color=GOLD, fg_color=NAVY):
        b = Button(text=ar_text(text), size_hint_y=None, height=dp(height),
                   background_normal="", background_color=bg_color, color=fg_color,
                   font_size=f"{font_size}sp", font_name=APP_FONT, bold=True)
        b.bind(on_release=callback)
        return b

    def show_login(self):
        self.root_box.clear_widgets()
        self.root_box.add_widget(self.make_label("بئر علي حسين", 54, GOLD, 27, markup=True))
        self.root_box.add_widget(self.make_label("GOLDEN PULSE", 36, WHITE, 22))
        self.root_box.add_widget(self.make_label("تسجيل الدخول", 48, GOLD, 20))
        
        form = BoxLayout(orientation="vertical", spacing=dp(12), padding=(dp(12), dp(12)))
        self.login_user = Field("اسم المستخدم")
        self.login_pass = Field("كلمة المرور", password=True)
        form.add_widget(self.login_user)
        form.add_widget(self.login_pass)
        
        # زر الدخول باللون الأخضر المميز
        form.add_widget(self.make_button("دخول النظام", self.login, 50, 18, bg_color=GREEN, fg_color=NAVY))
        self.root_box.add_widget(form)
        self.root_box.add_widget(self.make_label("للدخول الافتراضي: admin / 112233", 36, MUTED, 12))

    def login(self, *_):
        if self.login_user.text.strip() == "admin" and self.login_pass.text == "112233":
            self.show_dashboard()
        else:
            self.notify("اسم المستخدم أو كلمة المرور غير صحيحة")

    def show_dashboard(self):
        self.root_box.clear_widgets()
        self.header = self.make_label("بئر علي حسين  |  لوحة التحكم الذهبية", 52, GOLD, 21)
        self.root_box.add_widget(self.header)
        
        # القائمة الرئيسية المكونة من الشاشات السبع المطلوبة بألوان جذابة
        self.nav = GridLayout(cols=2, spacing=dp(8), size_hint_y=None, height=dp(260))
        for label, screen in [
            ("المبيعات", "sales"), 
            ("سند قبض", "rec"), 
            ("سند صرف", "pay"),
            ("الديون وسدادها", "debt"), 
            ("التقارير المالية", "reports"), 
            ("السجلات", "records"),
            ("النسخة الاحتياطية", "backup")
        ]:
            b = self.make_button(label, lambda inst, s=screen: self.show_screen(s), 48, 15, bg_color=PANEL, fg_color=GOLD)
            self.nav.add_widget(b)
        self.root_box.add_widget(self.nav)
        
        # زر خروج أحمر للعودة لتسجيل الدخول أو القفل
        exit_btn = self.make_button("قفل النظام / تسجيل الخروج", lambda *_: self.show_login(), 48, 15, bg_color=RED, fg_color=WHITE)
        self.root_box.add_widget(exit_btn)
        
        self.content = BoxLayout(orientation="vertical", spacing=dp(8))
        self.root_box.add_widget(self.content)
        self.show_screen("sales")

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
        elif name == "records":
            self.records_screen()
        elif name == "backup":
            self.backup_screen()

    def form_shell(self, title):
        self.add_label(self.content, title, height=40, color=GOLD, size=20)
        scroll = ScrollView()
        form = BoxLayout(orientation="vertical", spacing=dp(7), padding=(dp(3), dp(4)),
                         size_hint_y=None)
        form.bind(minimum_height=form.setter("height"))
        scroll.add_widget(form)
        self.content.add_widget(scroll)
        return form

    def add_back_button(self, form_layout):
        """زر أحمر للرجوع للوحة التحكم الرئيسية في نهاية كل صفحة"""
        b = self.make_button("العودة إلى لوحة التحكم الرئيسية", lambda *_: self.show_dashboard(), 48, 15, bg_color=RED, fg_color=WHITE)
        form_layout.add_widget(b)

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
        # زر الحفظ باللون الأخضر الجذاب
        form.add_widget(self.make_button(label, callback, 50, 17, bg_color=GREEN, fg_color=NAVY))

    def notify(self, message):
        box = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(12))
        box.add_widget(self.make_label(message, 70, NAVY, 15))
        close = self.make_button("حسنًا", lambda *_: pop.dismiss(), 42, bg_color=GOLD, fg_color=NAVY)
        box.add_widget(close)
        pop = Popup(title="Golden Pulse", content=box, size_hint=(.88, .42))
        close.bind(on_release=pop.dismiss)
        pop.open()

    def sales_screen(self):
        form = self.form_shell("فاتورة تعبئة مياه (وايت)")
        f = {}
        self.add_field(form, "اسم صاحب الوايت", "owner", f)
        self.add_field(form, "رقم الهاتف", "phone", f)
        self.add_spinner(form, [str(x) for x in range(2000, 20001, 2000)], "size", f, "10000")
        self.add_spinner(form, ["نقدي", "آجل"], "pay", f, "نقدي")
        self.add_spinner(form, ["ريال يمني", "دولار", "ريال سعودي"], "currency", f, "ريال يمني")
        self.add_field(form, "الكمية (لتر)", "qty", f, "5000")  # الكمية الافتراضية 5000 لتر
        self.add_field(form, "سعر الوايت", "price", f, "0")
        self.add_field(form, "الخصم", "discount", f, "0")
        
        # الإجمالي بخط كبير ولون ذهبي جذاب
        total_label = self.make_label("الإجمالي: 0", 44, GOLD, 22)
        form.add_widget(total_label)

        def calc(*_):
            try:
                total = max(0, float(f["qty"].text or 0) * float(f["price"].text or 0) - float(f["discount"].text or 0))
                total_label.text = ar_text("الإجمالي: " + money(total))
            except ValueError:
                total_label.text = ar_text("الإجمالي: —")
        for k in ("qty", "price", "discount"):
            f[k].bind(text=calc)

        def save(_):
            try:
                owner = f["owner"].text.strip()
                if not owner:
                    raise ValueError("أدخل اسم صاحب الوايت.")
                qty = float(f["qty"].text or 0)
                price = float(f["price"].text or 0)
                discount = float(f["discount"].text or 0)
                if qty <= 0 or price < 0 or discount < 0:
                    raise ValueError("تحقق من الكمية والسعر والخصم.")
                date, tm = now_parts()
                number = "INV-" + datetime.now().strftime("%y%m%d%H%M%S")
                total = max(0, qty * price - discount)
                data = dict(no=number, date=date, time=tm, owner=owner,
                            phone=f["phone"].text.strip(), size=f["size"].text,
                            pay=f["pay"].text, currency=f["currency"].text,
                            qty=qty, price=price, discount=discount, total=total)
                self.store.add_sale(data)
                self.show_invoice(data)
            except (ValueError, sqlite3.Error) as e:
                self.notify(str(e))
                
        self.save_button(form, "حفظ الفاتورة وعرضها", save)
        self.add_back_button(form)

    def invoice_text(self, d):
        return (
            "بئر علي حسين\n"
            "GOLDEN PULSE\n"
            "فاتورة تعبئة مياه\n"
            "--------------------------------\n"
            f"رقم الفاتورة: {d['no']}\n"
            f"التاريخ: {d['date']}  {d['time']}\n"
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
        print_btn = self.make_button("طباعة / مشاركة", lambda *_: self.share_invoice(d), 46, 13, bg_color=GREEN, fg_color=NAVY)
        close_btn = self.make_button("إغلاق", lambda *_: pop.dismiss(), 46, 13, bg_color=RED, fg_color=WHITE)
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
            self.notify("اختر تطبيق الطابعة الحرارية أو البلوتوث من القائمة.")
        except Exception:
            self.notify("تعذّر فتح قائمة المشاركة تلقائيًا.")

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
                self.show_dashboard()
            except (ValueError, sqlite3.Error) as e:
                self.notify(str(e))
        self.save_button(form, "حفظ " + title, save)
        self.add_back_button(form)

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
                self.show_dashboard()
            except (ValueError, sqlite3.Error) as e:
                self.notify(str(e))
        self.save_button(form, "حفظ سداد الدين", save)
        self.add_back_button(form)

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
        self.add_back_button(form)

    def records_screen(self):
        form = self.form_shell("آخر السجلات")
        for table, title in [("sales", "المبيعات"), ("rec", "سندات القبض"),
                             ("pay", "سندات الصرف"), ("debt_payments", "سداد الديون")]:
            rows = self.store.rows(table)
            self.add_label(form, f"— {title}: {len(rows)} سجل —", height=38, color=GOLD, size=17)
            for row in rows[:15]:
                name = row.get("owner") or row.get("customer") or row.get("name") or "—"
                amount = row.get("total", row.get("amount", 0))
                no = row.get("no", "")
                date = row.get("date", "")
                self.add_label(form, f"{date} | {no} | {name} | {money(amount)}", height=44, color=WHITE, size=12)
        self.add_back_button(form)

    def backup_screen(self):
        form = self.form_shell("النسخة الاحتياطية المحلية")
        self.add_label(form, "يمكنك أخذ نسخة احتياطية لقاعدة البيانات المحلية وحفظها على جهازك.", height=50, color=MUTED, size=13)
        
        def do_backup(_):
            try:
                src = os.path.join(self.user_data_dir, "golden_pulse.db")
                dst_dir = os.path.join(self.user_data_dir, "backup")
                os.makedirs(dst_dir, exist_ok=True)
                dst = os.path.join(dst_dir, f"golden_pulse_bk_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
                if os.path.exists(src):
                    shutil.copy(src, dst)
                    self.notify(f"تم إنشاء نسخة احتياطية بنجاح في:\n{dst}")
                else:
                    self.notify("لا توجد بيانات حالية لعمل نسخة احتياطية.")
            except Exception as e:
                self.notify(f"خطأ في النسخ: {str(e)}")

        bk_btn = self.make_button("إنشاء نسخة احتياطية الآن", do_backup, 48, 16, bg_color=GREEN, fg_color=NAVY)
        form.add_widget(bk_btn)
        self.add_back_button(form)

if __name__ == "__main__":
    GoldenPulseApp().run()
