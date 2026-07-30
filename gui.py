"""
Desktop GUI for the bank system, built with CustomTkinter.

Every action here calls straight into the already tested functions in
DBsys.py and ai.py this file is UI only.
"""

import threading
from datetime import date, timedelta

import customtkinter as ctk
from tkinter import messagebox

import DBsys
import ai

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

WINDOW_SIZE = "1000x680"


# ============================================================================
# Small reusable widgets
# ============================================================================

class LabeledEntry(ctk.CTkFrame):
    """A label + entry pair stacked vertically, used all over the forms below."""
    def __init__(self, parent, label, show=None, width=280):
        super().__init__(parent, fg_color="transparent")
        ctk.CTkLabel(self, text=label, anchor="w").pack(fill="x")
        self.entry = ctk.CTkEntry(self, width=width, show=show)
        self.entry.pack(fill="x", pady=(2, 0))

    def get(self):
        return self.entry.get().strip()

    def set(self, value):
        self.entry.delete(0, "end")
        self.entry.insert(0, str(value))


def status_label(parent):
    """A small label for showing success/error messages under a form."""
    lbl = ctk.CTkLabel(parent, text="", anchor="w")
    return lbl


def show_status(label, message, ok=True):
    label.configure(text=message, text_color="lightgreen" if ok else "tomato")


# ============================================================================
# Main application / page router
# ============================================================================

class BankApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Bank System")
        self.geometry(WINDOW_SIZE)

        self.current_user = None  # dict: user_id, full_name, session_id, token
        self.dashboard = None

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)

        self.frames = {}
        for PageClass in (WelcomePage, LoginPage, RegisterPage, ContactPage):
            frame = PageClass(self.container, self)
            self.frames[PageClass.__name__] = frame
            frame.place(relwidth=1, relheight=1)

        self.show_frame("WelcomePage")

    def show_frame(self, name):
        self.frames[name].tkraise()

    def login_success(self, user_id, full_name, session_id, token):
        self.current_user = {
            "user_id": user_id,
            "full_name": full_name,
            "session_id": session_id,
            "token": token,
        }
        if self.dashboard is not None:
            self.dashboard.destroy()
        self.dashboard = Dashboard(self.container, self)
        self.dashboard.place(relwidth=1, relheight=1)
        self.dashboard.tkraise()

    def logout(self):
        if self.current_user:
            DBsys.revoke_session(self.current_user["session_id"])
        self.current_user = None
        if self.dashboard is not None:
            self.dashboard.destroy()
            self.dashboard = None
        self.show_frame("WelcomePage")


# ============================================================================
# Welcome / Login / Register / Contact
# ============================================================================

class WelcomePage(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        ctk.CTkLabel(self, text="Welcome", font=ctk.CTkFont(size=30, weight="bold")).pack(pady=(100, 40))

        ctk.CTkButton(self, text="Log In", width=260, height=45,
                      command=lambda: app.show_frame("LoginPage")).pack(pady=8)
        ctk.CTkButton(self, text="I'm new here -->> Create an Account", width=260, height=45,
                      command=lambda: app.show_frame("RegisterPage")).pack(pady=8)
        ctk.CTkButton(self, text="Contact the Bank", width=260, height=45,
                      fg_color="gray30", hover_color="gray20",
                      command=lambda: app.show_frame("ContactPage")).pack(pady=8)


class LoginPage(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        ctk.CTkLabel(self, text="Log In", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(70, 25))

        self.name_field = LabeledEntry(self, "Full name")
        self.name_field.pack(pady=6)
        self.id_field = LabeledEntry(self, "User ID")
        self.id_field.pack(pady=6)
        self.pw_field = LabeledEntry(self, "Password", show="*")
        self.pw_field.pack(pady=6)

        self.status = status_label(self)
        self.status.pack(pady=10)

        ctk.CTkButton(self, text="Log In", width=220, command=self.attempt_login).pack(pady=6)
        ctk.CTkButton(self, text="Back", width=220, fg_color="gray30", hover_color="gray20",
                      command=lambda: app.show_frame("WelcomePage")).pack(pady=6)

    def attempt_login(self):
        name = self.name_field.get()
        user_id_str = self.id_field.get()
        password = self.pw_field.get()

        if not name or not user_id_str or not password:
            show_status(self.status, "Please fill in every field.", ok=False)
            return

        try:
            user_id = int(user_id_str)
        except ValueError:
            show_status(self.status, "User ID must be a number.", ok=False)
            return

        success, result = DBsys.authenticate_user(user_id, name, password)
        if not success:
            show_status(self.status, result, ok=False)
            return

        self.pw_field.set("")
        show_status(self.status, "")
        self.app.login_success(result["user_id"], name, result["session_id"], result["token"])


class RegisterPage(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        ctk.CTkLabel(self, text="Create a New Account", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(25, 15))

        form = ctk.CTkFrame(self, fg_color="transparent")
        form.pack()

        self.full_name = LabeledEntry(form, "Full name")
        self.full_name.grid(row=0, column=0, padx=8, pady=6)
        self.email = LabeledEntry(form, "Email")
        self.email.grid(row=0, column=1, padx=8, pady=6)

        self.phone = LabeledEntry(form, "Phone number")
        self.phone.grid(row=1, column=0, padx=8, pady=6)
        self.national_id = LabeledEntry(form, "National ID")
        self.national_id.grid(row=1, column=1, padx=8, pady=6)

        self.dob = LabeledEntry(form, "Date of birth (YYYY-MM-DD)")
        self.dob.grid(row=2, column=0, padx=8, pady=6)
        self.address = LabeledEntry(form, "Address")
        self.address.grid(row=2, column=1, padx=8, pady=6)

        self.password = LabeledEntry(form, "Password", show="*")
        self.password.grid(row=3, column=0, padx=8, pady=6)
        self.confirm = LabeledEntry(form, "Confirm password", show="*")
        self.confirm.grid(row=3, column=1, padx=8, pady=6)

        self.status = status_label(self)
        self.status.pack(pady=10)

        ctk.CTkButton(self, text="Register", width=220, command=self.attempt_register).pack(pady=6)
        ctk.CTkButton(self, text="Back", width=220, fg_color="gray30", hover_color="gray20",
                      command=lambda: app.show_frame("WelcomePage")).pack(pady=6)

    def attempt_register(self):
        values = {
            "full_name": self.full_name.get(),
            "email": self.email.get(),
            "phone_number": self.phone.get(),
            "national_id": self.national_id.get(),
            "date_of_birth": self.dob.get(),
            "address": self.address.get(),
        }
        password = self.password.get()
        confirm = self.confirm.get()

        if not all(values.values()) or not password:
            show_status(self.status, "Please fill in every field.", ok=False)
            return
        if password != confirm:
            show_status(self.status, "Passwords don't match.", ok=False)
            return
        if len(password) < 8:
            show_status(self.status, "Password must be at least 8 characters.", ok=False)
            return

        ok, result = DBsys.register_user(**values, password=password)
        if not ok:
            show_status(self.status, result, ok=False)
            return

        messagebox.showinfo(
            "Welcome!",
            f"Account created. Your User ID is {result} write it down, "
            "you'll need it (along with your name and password) to log in."
        )
        self.app.show_frame("LoginPage")


class ContactPage(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        ctk.CTkLabel(self, text="Contact the Bank", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(40, 6))
        ctk.CTkLabel(self, text="Support line: +351 000 111 000   |   support@fakeBank.pt").pack(pady=(0, 20))
        ctk.CTkLabel(self, text="Can't log in, or running into a problem? Send us a message:").pack(pady=(0, 10))

        self.name_field = LabeledEntry(self, "Your name", width=320)
        self.name_field.pack(pady=4)
        self.email_field = LabeledEntry(self, "Your email", width=320)
        self.email_field.pack(pady=4)

        ctk.CTkLabel(self, text="Message", anchor="w").pack(fill="x", padx=(340, 0))
        self.message_box = ctk.CTkTextbox(self, width=320, height=110)
        self.message_box.pack(pady=(2, 8))

        self.status = status_label(self)
        self.status.pack(pady=6)

        ctk.CTkButton(self, text="Send", width=220, command=self.send_message).pack(pady=6)
        ctk.CTkButton(self, text="Back", width=220, fg_color="gray30", hover_color="gray20",
                      command=lambda: app.show_frame("WelcomePage")).pack(pady=6)

    def send_message(self):
        name = self.name_field.get()
        email = self.email_field.get()
        message = self.message_box.get("1.0", "end").strip()

        if not name or not email or not message:
            show_status(self.status, "Please fill in every field.", ok=False)
            return

        # There's no dedicated support ticket table yet, so this is logged to
        # the audit log for now (user_id is None if nobody's logged in e.g.
        # exactly the "I can't log in" case this form exists for). Worth a
        # real support_requests table if this app grows.
        user_id = self.app.current_user["user_id"] if self.app.current_user else None
        DBsys.log_audit_event(
            user_id, "SUPPORT_REQUEST",
            details={"name": name, "email": email, "message": message}
        )

        show_status(self.status, "Message sent - we'll get back to you.")
        self.name_field.set("")
        self.email_field.set("")
        self.message_box.delete("1.0", "end")


# ============================================================================
# Dashboard (post-login hub)
# ============================================================================

class Dashboard(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.user_id = app.current_user["user_id"]
        self.full_name = app.current_user["full_name"]

        self.accounts_cache = []  # refreshed by refresh_accounts()

        # ---- layout: sidebar + content area ----
        sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.pack(side="left", fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(sidebar, text=f"Hi, {self.full_name.split(' ')[0]}",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20, 15), padx=15)

        nav_items = [
            ("Overview", self.show_overview),
            ("Transactions", self.show_transactions),
            ("New Account", self.show_new_account),
            ("Cards", self.show_cards),
            ("MBWay", self.show_mbway),
            ("Transfer / Withdraw / Deposit", self.show_move_money),
            ("Payment Codes", self.show_payment_codes),
            ("Scheduled Payments", self.show_scheduled_payments),
            ("AI Assistant", self.show_ai_assistant),
        ]
        for label, command in nav_items:
            ctk.CTkButton(sidebar, text=label, anchor="w", command=command).pack(
                fill="x", padx=15, pady=4
            )

        ctk.CTkButton(sidebar, text="Log Out", fg_color="firebrick", hover_color="darkred",
                      command=app.logout).pack(side="bottom", fill="x", padx=15, pady=20)

        self.refresh_accounts()
        self.show_overview()

    # ---- shared helpers ----

    def clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    def refresh_accounts(self):
        self.accounts_cache = DBsys.get_account_overview(self.user_id)

    def account_options(self):
        """Returns {display_string: account_id} for populating dropdowns."""
        return {
            f"#{a[3]} - {a[4]} ({a[5]} {a[6]})": a[3]
            for a in self.accounts_cache
        }

    # ---- Overview ----

    def show_overview(self):
        self.refresh_accounts()
        self.clear_content()
        ctk.CTkLabel(self.content, text="Account Overview", font=ctk.CTkFont(size=20, weight="bold")).pack(
            anchor="w", pady=(0, 15)
        )

        if not self.accounts_cache:
            ctk.CTkLabel(self.content, text="You don't have any accounts yet - create one from the sidebar.").pack(anchor="w")
            return

        for a in self.accounts_cache:
            row = ctk.CTkFrame(self.content)
            row.pack(fill="x", pady=4)
            ctk.CTkLabel(row, text=f"Account #{a[3]}", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10, pady=8)
            ctk.CTkLabel(row, text=f"IBAN: {a[4]}").pack(side="left", padx=10)
            ctk.CTkLabel(row, text=f"Balance: {a[5]} {a[6]}").pack(side="left", padx=10)
            ctk.CTkLabel(row, text=f"Status: {a[7]}").pack(side="left", padx=10)

        upcoming = DBsys.get_upcoming_payments_for_user(self.user_id)
        ctk.CTkLabel(self.content, text="Payments due in the next 7 days",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(20, 8))
        if not upcoming:
            ctk.CTkLabel(self.content, text="Nothing due soon.").pack(anchor="w")
        for u in upcoming:
            ctk.CTkLabel(self.content, text=f"- {u[4]} to {u[3]} due {u[5]} (account #{u[2]})").pack(anchor="w")

    # ---- New account ----

    def show_new_account(self):
        self.clear_content()
        ctk.CTkLabel(self.content, text="Open a New Account", font=ctk.CTkFont(size=20, weight="bold")).pack(
            anchor="w", pady=(0, 15)
        )
        ctk.CTkLabel(self.content, text="An IBAN will be generated automatically.").pack(anchor="w", pady=(0, 10))

        status = status_label(self.content)

        def create():
            ok, result = DBsys.creat_new_account(self.user_id)
            if ok:
                show_status(status, f"Account #{result} created.")
                self.refresh_accounts()
            else:
                show_status(status, result, ok=False)

        ctk.CTkButton(self.content, text="Create Checking Account", command=create).pack(anchor="w", pady=6)
        status.pack(anchor="w", pady=8)

    # ---- Transactions ----

    def show_transactions(self):
        self.clear_content()
        ctk.CTkLabel(self.content, text="Transaction History", font=ctk.CTkFont(size=20, weight="bold")).pack(
            anchor="w", pady=(0, 15)
        )

        options = self.account_options()
        if not options:
            ctk.CTkLabel(self.content, text="You don't have any accounts yet.").pack(anchor="w")
            return

        picker = ctk.CTkOptionMenu(self.content, values=list(options.keys()))
        picker.pack(anchor="w", pady=6)

        results_box = ctk.CTkTextbox(self.content, width=700, height=380)

        def load():
            account_id = options[picker.get()]
            rows = DBsys.get_transaction_history(account_id, limit=50)
            results_box.delete("1.0", "end")
            if not rows:
                results_box.insert("end", "No transactions yet.")
                return
            for r in rows:
                tx_id, frm, to, amount, currency, tx_type, status_, ref, desc, created = r
                results_box.insert(
                    "end",
                    f"[{created}] {tx_type} - {amount} {currency} - {status_}"
                    f"{' - ' + desc if desc else ''}\n"
                )

        ctk.CTkButton(self.content, text="Load History", command=load).pack(anchor="w", pady=6)
        results_box.pack(pady=10)

    # ---- Cards ----

    def show_cards(self):
        self.clear_content()
        ctk.CTkLabel(self.content, text="Cards", font=ctk.CTkFont(size=20, weight="bold")).pack(
            anchor="w", pady=(0, 15)
        )

        options = self.account_options()
        if not options:
            ctk.CTkLabel(self.content, text="You don't have any accounts yet.").pack(anchor="w")
            return

        form = ctk.CTkFrame(self.content, fg_color="transparent")
        form.pack(anchor="w")

        ctk.CTkLabel(form, text="Account").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        account_picker = ctk.CTkOptionMenu(form, values=list(options.keys()))
        account_picker.grid(row=0, column=1, padx=4, pady=4)

        ctk.CTkLabel(form, text="Card type").grid(row=1, column=0, sticky="w", padx=4, pady=4)
        type_picker = ctk.CTkOptionMenu(form, values=["debit", "credit"])
        type_picker.grid(row=1, column=1, padx=4, pady=4)

        limit_field = LabeledEntry(form, "Daily limit", width=200)
        limit_field.grid(row=2, column=0, columnspan=2, pady=4)

        status = status_label(self.content)

        def create_card():
            account_id = options[account_picker.get()]
            card_type = type_picker.get()
            try:
                daily_limit = float(limit_field.get() or "400")
            except ValueError:
                show_status(status, "Daily limit must be a number.", ok=False)
                return
            expiry = (date.today() + timedelta(days=365 * 4)).isoformat()
            ok, result = DBsys.add_card_to_account(account_id, card_type, expiry, daily_limit)
            if ok:
                show_status(status, f"Card created: ...{result[-4:]}" if isinstance(result, str) else "Card created.")
                refresh_list()
            else:
                show_status(status, str(result), ok=False)

        ctk.CTkButton(form, text="Issue Card", command=create_card).grid(row=3, column=0, columnspan=2, pady=8)
        status.pack(anchor="w", pady=6)

        list_box = ctk.CTkTextbox(self.content, width=700, height=260)
        list_box.pack(pady=10)

        def refresh_list():
            list_box.delete("1.0", "end")
            cards = DBsys.get_cards_for_user(self.user_id)
            if not cards:
                list_box.insert("end", "No cards yet.")
                return
            for c in cards:
                card_id, account_id, last_four, card_type, expiry, daily_limit, status_ = c
                list_box.insert(
                    "end",
                    f"Card #{card_id} (acct #{account_id}) - {card_type} ending {last_four} - "
                    f"limit {daily_limit}/day - expires {expiry} - {status_}\n"
                )

        refresh_list()

    # ---- MBWay ----

    def show_mbway(self):
        self.clear_content()
        ctk.CTkLabel(self.content, text="MBWay", font=ctk.CTkFont(size=20, weight="bold")).pack(
            anchor="w", pady=(0, 15)
        )

        options = self.account_options()
        if not options:
            ctk.CTkLabel(self.content, text="You don't have any accounts yet.").pack(anchor="w")
            return

        form = ctk.CTkFrame(self.content, fg_color="transparent")
        form.pack(anchor="w")

        ctk.CTkLabel(form, text="Account").grid(row=0, column=0, sticky="w", padx=4, pady=4)
        account_picker = ctk.CTkOptionMenu(form, values=list(options.keys()))
        account_picker.grid(row=0, column=1, padx=4, pady=4)

        phone_field = LabeledEntry(form, "Phone number", width=200)
        phone_field.grid(row=1, column=0, columnspan=2, pady=4)

        status = status_label(self.content)

        list_box = ctk.CTkTextbox(self.content, width=700, height=200)

        def refresh_list():
            list_box.delete("1.0", "end")
            account_id = options[account_picker.get()]
            links = DBsys.get_mbway_links(account_id)
            if not links:
                list_box.insert("end", "No MBWay links for this account.")
                return
            for mbway_id, phone, status_ in links:
                list_box.insert("end", f"#{mbway_id} - {phone} - {status_}\n")

        def link_phone():
            account_id = options[account_picker.get()]
            phone = phone_field.get()
            if not phone:
                show_status(status, "Enter a phone number.", ok=False)
                return
            ok, result = DBsys.add_mbway_link(account_id, phone)
            show_status(status, "Linked." if ok else result, ok=ok)
            refresh_list()

        ctk.CTkButton(form, text="Link Phone Number", command=link_phone).grid(
            row=2, column=0, columnspan=2, pady=8
        )
        status.pack(anchor="w", pady=6)
        list_box.pack(pady=10)
        refresh_list()

    # ---- Transfer / Withdraw / Deposit ----

    def show_move_money(self):
        self.clear_content()
        ctk.CTkLabel(self.content, text="Transfer / Withdraw / Deposit", font=ctk.CTkFont(size=20, weight="bold")).pack(
            anchor="w", pady=(0, 15)
        )

        tabs = ctk.CTkTabview(self.content, width=700, height=420)
        tabs.pack()
        tabs.add("Transfer")
        tabs.add("Withdraw (Card)")
        tabs.add("Withdraw (MBWay)")
        tabs.add("Deposit")

        options = self.account_options()

        # --- Transfer tab ---
        t = tabs.tab("Transfer")
        if options:
            ctk.CTkLabel(t, text="From account").pack(anchor="w", pady=(10, 0))
            from_picker = ctk.CTkOptionMenu(t, values=list(options.keys()))
            from_picker.pack(anchor="w")
            iban_field = LabeledEntry(t, "Destination IBAN", width=320)
            iban_field.pack(anchor="w", pady=6)
            amount_field = LabeledEntry(t, "Amount", width=200)
            amount_field.pack(anchor="w", pady=6)
            desc_field = LabeledEntry(t, "Description (optional)", width=320)
            desc_field.pack(anchor="w", pady=6)
            t_status = status_label(t)
            t_status.pack(anchor="w", pady=6)

            def do_transfer():
                from_account_id = options[from_picker.get()]
                try:
                    amount = float(amount_field.get())
                except ValueError:
                    show_status(t_status, "Amount must be a number.", ok=False)
                    return
                ok, result = DBsys.transfer_by_iban(
                    from_account_id, iban_field.get(), amount, description=desc_field.get() or None
                )
                show_status(t_status, f"Transfer complete (tx {result})" if ok else str(result), ok=ok)
                if ok:
                    self.refresh_accounts()

            ctk.CTkButton(t, text="Send Transfer", command=do_transfer).pack(anchor="w", pady=8)
        else:
            ctk.CTkLabel(t, text="You don't have any accounts yet.").pack(anchor="w", pady=10)

        # --- Withdraw via card tab ---
        t2 = tabs.tab("Withdraw (Card)")
        cards = DBsys.get_cards_for_user(self.user_id)
        card_options = {f"#{c[0]} ending {c[2]} (acct #{c[1]})": c[0] for c in cards}
        if card_options:
            ctk.CTkLabel(t2, text="Card").pack(anchor="w", pady=(10, 0))
            card_picker = ctk.CTkOptionMenu(t2, values=list(card_options.keys()))
            card_picker.pack(anchor="w")
            amount_field2 = LabeledEntry(t2, "Amount", width=200)
            amount_field2.pack(anchor="w", pady=6)
            t2_status = status_label(t2)
            t2_status.pack(anchor="w", pady=6)

            def do_card_withdraw():
                card_id = card_options[card_picker.get()]
                try:
                    amount = float(amount_field2.get())
                except ValueError:
                    show_status(t2_status, "Amount must be a number.", ok=False)
                    return
                ok, result = DBsys.withdraw_via_card(card_id, amount)
                show_status(t2_status, f"Withdrawal complete (tx {result})" if ok else str(result), ok=ok)
                if ok:
                    self.refresh_accounts()

            ctk.CTkButton(t2, text="Withdraw", command=do_card_withdraw).pack(anchor="w", pady=8)
        else:
            ctk.CTkLabel(t2, text="You don't have any cards yet.").pack(anchor="w", pady=10)

        # --- Withdraw via MBWay tab ---
        t3 = tabs.tab("Withdraw (MBWay)")
        all_links = []
        for a in self.accounts_cache:
            all_links.extend(DBsys.get_mbway_links(a[3]))
        mbway_options = {f"#{m[0]} - {m[1]}": m[0] for m in all_links}
        if mbway_options:
            ctk.CTkLabel(t3, text="MBWay link").pack(anchor="w", pady=(10, 0))
            mbway_picker = ctk.CTkOptionMenu(t3, values=list(mbway_options.keys()))
            mbway_picker.pack(anchor="w")
            amount_field3 = LabeledEntry(t3, "Amount", width=200)
            amount_field3.pack(anchor="w", pady=6)
            t3_status = status_label(t3)
            t3_status.pack(anchor="w", pady=6)

            def do_mbway_withdraw():
                mbway_id = mbway_options[mbway_picker.get()]
                try:
                    amount = float(amount_field3.get())
                except ValueError:
                    show_status(t3_status, "Amount must be a number.", ok=False)
                    return
                ok, result = DBsys.withdraw_via_mbway(mbway_id, amount)
                show_status(t3_status, f"Withdrawal complete (tx {result})" if ok else str(result), ok=ok)
                if ok:
                    self.refresh_accounts()

            ctk.CTkButton(t3, text="Withdraw", command=do_mbway_withdraw).pack(anchor="w", pady=8)
        else:
            ctk.CTkLabel(t3, text="No MBWay links yet - add one from the MBWay tab.").pack(anchor="w", pady=10)

        # --- Deposit tab ---
        t4 = tabs.tab("Deposit")
        if options:
            ctk.CTkLabel(t4, text="Into account").pack(anchor="w", pady=(10, 0))
            deposit_picker = ctk.CTkOptionMenu(t4, values=list(options.keys()))
            deposit_picker.pack(anchor="w")
            amount_field4 = LabeledEntry(t4, "Amount", width=200)
            amount_field4.pack(anchor="w", pady=6)
            t4_status = status_label(t4)
            t4_status.pack(anchor="w", pady=6)

            def do_deposit():
                account_id = options[deposit_picker.get()]
                try:
                    amount = float(amount_field4.get())
                except ValueError:
                    show_status(t4_status, "Amount must be a number.", ok=False)
                    return
                ok, result = DBsys.deposit_funds(account_id, amount)
                show_status(t4_status, f"Deposit complete (tx {result})" if ok else str(result), ok=ok)
                if ok:
                    self.refresh_accounts()

            ctk.CTkButton(t4, text="Deposit", command=do_deposit).pack(anchor="w", pady=8)
        else:
            ctk.CTkLabel(t4, text="You don't have any accounts yet.").pack(anchor="w", pady=10)

    # ---- Payment codes ----

    def show_payment_codes(self):
        self.clear_content()
        ctk.CTkLabel(self.content, text="Payment Codes", font=ctk.CTkFont(size=20, weight="bold")).pack(
            anchor="w", pady=(0, 15)
        )

        tabs = ctk.CTkTabview(self.content, width=700, height=340)
        tabs.pack()
        tabs.add("Generate a Code")
        tabs.add("Pay a Code")

        options = self.account_options()

        gen_tab = tabs.tab("Generate a Code")
        if options:
            ctk.CTkLabel(gen_tab, text="Into account").pack(anchor="w", pady=(10, 0))
            gen_picker = ctk.CTkOptionMenu(gen_tab, values=list(options.keys()))
            gen_picker.pack(anchor="w")
            gen_amount = LabeledEntry(gen_tab, "Amount", width=200)
            gen_amount.pack(anchor="w", pady=6)
            gen_desc = LabeledEntry(gen_tab, "Description (optional)", width=320)
            gen_desc.pack(anchor="w", pady=6)
            gen_status = status_label(gen_tab)
            gen_status.pack(anchor="w", pady=6)

            def generate():
                account_id = options[gen_picker.get()]
                try:
                    amount = float(gen_amount.get())
                except ValueError:
                    show_status(gen_status, "Amount must be a number.", ok=False)
                    return
                ok, result = DBsys.generate_payment_code(account_id, amount, description=gen_desc.get() or None)
                show_status(gen_status, f"Code: {result}" if ok else str(result), ok=ok)

            ctk.CTkButton(gen_tab, text="Generate", command=generate).pack(anchor="w", pady=8)

        pay_tab = tabs.tab("Pay a Code")
        if options:
            ctk.CTkLabel(pay_tab, text="Pay from account").pack(anchor="w", pady=(10, 0))
            pay_picker = ctk.CTkOptionMenu(pay_tab, values=list(options.keys()))
            pay_picker.pack(anchor="w")
            code_field = LabeledEntry(pay_tab, "Payment code", width=250)
            code_field.pack(anchor="w", pady=6)
            pay_status = status_label(pay_tab)
            pay_status.pack(anchor="w", pady=6)

            def pay():
                account_id = options[pay_picker.get()]
                ok, result = DBsys.pay_with_code(account_id, code_field.get())
                show_status(pay_status, f"Paid (tx {result})" if ok else str(result), ok=ok)
                if ok:
                    self.refresh_accounts()

            ctk.CTkButton(pay_tab, text="Pay", command=pay).pack(anchor="w", pady=8)

    # ---- Scheduled payments ----

    def show_scheduled_payments(self):
        self.clear_content()
        ctk.CTkLabel(self.content, text="Scheduled Payments", font=ctk.CTkFont(size=20, weight="bold")).pack(
            anchor="w", pady=(0, 15)
        )

        options = self.account_options()
        list_box = ctk.CTkTextbox(self.content, width=700, height=220)

        def refresh_list():
            list_box.delete("1.0", "end")
            rows = DBsys.get_scheduled_payments_for_user(self.user_id)
            if not rows:
                list_box.insert("end", "No scheduled payments yet.")
                return
            for r in rows:
                sched_id, account_id, payee_iban, amount, frequency, next_due, status_, desc = r
                list_box.insert(
                    "end",
                    f"#{sched_id} (acct #{account_id}) - {amount} to {payee_iban} - "
                    f"{frequency}, next: {next_due} - {status_}\n"
                )

        if options:
            form = ctk.CTkFrame(self.content, fg_color="transparent")
            form.pack(anchor="w", pady=(0, 15))

            ctk.CTkLabel(form, text="From account").grid(row=0, column=0, sticky="w", padx=4, pady=4)
            account_picker = ctk.CTkOptionMenu(form, values=list(options.keys()))
            account_picker.grid(row=0, column=1, padx=4, pady=4)

            iban_field = LabeledEntry(form, "Payee IBAN", width=250)
            iban_field.grid(row=1, column=0, padx=4, pady=4)
            amount_field = LabeledEntry(form, "Amount", width=150)
            amount_field.grid(row=1, column=1, padx=4, pady=4)

            ctk.CTkLabel(form, text="Frequency").grid(row=2, column=0, sticky="w", padx=4, pady=4)
            freq_picker = ctk.CTkOptionMenu(form, values=["once", "weekly", "monthly", "yearly"])
            freq_picker.grid(row=2, column=1, padx=4, pady=4)

            date_field = LabeledEntry(form, "Next due date (YYYY-MM-DD)", width=200)
            date_field.grid(row=3, column=0, columnspan=2, pady=4)
            date_field.set(date.today().isoformat())

            status = status_label(self.content)

            def create():
                account_id = options[account_picker.get()]
                try:
                    amount = float(amount_field.get())
                except ValueError:
                    show_status(status, "Amount must be a number.", ok=False)
                    return
                ok, result = DBsys.create_scheduled_payment(
                    account_id, iban_field.get(), amount, freq_picker.get(), date_field.get()
                )
                show_status(status, "Scheduled." if ok else str(result), ok=ok)
                refresh_list()

            ctk.CTkButton(form, text="Schedule Payment", command=create).grid(
                row=4, column=0, columnspan=2, pady=8
            )
            status.pack(anchor="w", pady=6)
        else:
            ctk.CTkLabel(self.content, text="You don't have any accounts yet.").pack(anchor="w")

        list_box.pack(pady=10)
        refresh_list()

    # ---- AI Assistant ----

    def show_ai_assistant(self):
        self.clear_content()
        ctk.CTkLabel(self.content, text="AI Assistant", font=ctk.CTkFont(size=20, weight="bold")).pack(
            anchor="w", pady=(0, 10)
        )
        ctk.CTkLabel(
            self.content,
            text="Ask about your accounts, or about markets/commodities/currencies. "
                 "This assistant can only look things up - it can't move money for you.",
            wraplength=680, justify="left"
        ).pack(anchor="w", pady=(0, 10))

        chat_box = ctk.CTkTextbox(self.content, width=700, height=380)
        chat_box.pack(pady=(0, 10))
        chat_box.configure(state="disabled")

        input_row = ctk.CTkFrame(self.content, fg_color="transparent")
        input_row.pack(fill="x")

        entry = ctk.CTkEntry(input_row, placeholder_text="Type your question...")
        entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        send_button = ctk.CTkButton(input_row, text="Send")
        send_button.pack(side="left")

        def append(text):
            chat_box.configure(state="normal")
            chat_box.insert("end", text + "\n\n")
            chat_box.configure(state="disabled")
            chat_box.see("end")

        def send():
            question = entry.get().strip()
            if not question:
                return
            entry.delete(0, "end")
            append(f"You: {question}")
            send_button.configure(state="disabled", text="Thinking...")

            def worker():
                try:
                    response_text, used_cache = ai.get_ai_response(self.user_id, question)
                except Exception as err:
                    response_text, used_cache = f"Sorry, something went wrong: {err}", False

                def update_ui():
                    prefix = "Assistant (cached prices)" if used_cache else "Assistant"
                    append(f"{prefix}: {response_text}")
                    send_button.configure(state="normal", text="Send")

                self.after(0, update_ui)

            threading.Thread(target=worker, daemon=True).start()

        send_button.configure(command=send)
        entry.bind("<Return>", lambda event: send())


if __name__ == "__main__":
    app = BankApp()
    app.mainloop()
