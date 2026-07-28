import mysql.connector
from security import *
import shutil
import time
from decimal import Decimal
import random
import hashlib
from datetime import datetime, date, timedelta
import calendar
import secrets
import uuid
import json as _json




# Step 1: connect to the MySQL server (no specific database yet, since the script creates one)
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='DARKrobin24',
    database="BankSystem",
    autocommit=True   # required for conn.start_transaction() below to work correctly -
                       # with autocommit off (the default), the connector opens an implicit
                       # transaction on the first query, so a later explicit
                       # start_transaction() fails with "Transaction already in progress"
)
if conn.is_connected():
    print("Connected")

cursor = conn.cursor()


# 1- list all tables in the database 
# cursor.execute("SHOW TABLES;")
# tables = cursor.fetchall()
# print("Tables in BankSystem: ")
# for t in tables:
#     print(" -",t[0])

# # 2. Peek at row counts for each table, so you can see what's populated
# print("\nRow counts:")
# for (table_name,) in tables:
#     cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
#     count = cursor.fetchone()[0]
#     print(f" - {table_name}: {count} rows")

def printing_sys_lft(txt, defaulte = 0.08):
    terminal_width = shutil.get_terminal_size().columns

    current = ""
    for ch in txt:
        current += ch
        print("\r" + current, end="", flush=True)
        time.sleep(defaulte)
    print()




# ###########################################################################
#           Table:
# ###########################################################################

def print_all_tables():
    cursor.execute("show tables;")
    tables= cursor.fetchall()
    print("Tables in BankSystem: ")
    for t in tables:
        print(" -", t[0])
    print(len(tables), "Tables. ")
        


def get_all_table(table_name):
    # table_name = input("Enter the table name: ")
    print()
    cursor.execute(f"SELECT * FROM {table_name}")

    columns = [cal[0] for cal in cursor.description]
    rows = cursor.fetchall()

    for row in rows:
        print("-"*40)
        for column, value in zip(columns,row):
            print(f"{column}: {value}")
    print()



# was thinking of making a system to delete a table,
# but realised it was usles because theres no point in doing that
# def delete_table(table_name):
    # cursor.execute(f"delete ")



# ================================================================================
#           User/ User-Security:
# ================================================================================

# its for creating/ add a new user to the DB
def creat_new_user():
    print("Enter the following information:")

    full_name = input("Full name: ")
    email = input("Email: ")
    phone_number = input("Phone number: ")
    national_id = input("National ID: ")
    date_of_birth = input("Date of birth (YYYY-MM-DD): ")
    address = input("Address: ")

    pin = generate_secure_pass()


    try:
        cursor.execute(
            """
            INSERT INTO users
            (full_name, email, phone_number, national_id,
             date_of_birth, address, pin_hash)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (full_name, email, phone_number,
             national_id, date_of_birth,
             address, pin)
        )
    except mysql.connector.errors.IntegrityError:
        print("User in dataBse exists with similar info")
        return False


    conn.commit()

    user_id = cursor.lastrowid

    cursor.execute(
        "SELECT * FROM users WHERE user_id = %s",
        (user_id,)
    )
    

    print(cursor.fetchone())
    return True


# just for printing the user's data, i mainly did it for debuging and 
# shecking if the data got saved 
def get_user_full_data(user_id):
    # user_id = input("Enter user id")
    cursor.execute("select * from users where `user_id` = %s", (user_id,))
    table= cursor.fetchall()
    print(table)


def remove_user(user_id, table_name):
    cursor.execute(f"DELETE from {table_name} where user_id = %s", (user_id,))
    conn.commit()
    get_all_table(table_name)

def set_user_status(user_id, stat, table_name):
    cursor.execute(f"update {table_name} set status = %s where user_id= %s", (stat, user_id))
    conn.commit()
    get_all_table(table_name)


# just for editting user info,
# from name, email, phone num and address and quit when the user is done
def edit_user_info(id, pin):

    # verify identity
    cursor.execute(
        """
        SELECT user_id
        FROM users
        WHERE user_id = %s
          AND pin_hash = %s
        """,
        (id, pin)
    )

    if cursor.fetchone() is None:
        printing_sys_lft("Authentication failed.")
        return

    print()
    printing_sys_lft("Select a number from [1..4] according to the operation: ")
    printing_sys_lft("1. Set new User name. ")
    printing_sys_lft("2. Set new email. ")
    printing_sys_lft("3. Set new phone number. ")
    printing_sys_lft("4. Set new address. ")
    printing_sys_lft("==> Enter 'Quit' to exit. <==")

    while True:

        num = input("[1..4]: ")

        match num:  
            case '1':
                printing_sys_lft("Enter a new user full name: ")
                new_name = input()
                cursor.execute("update users set full_name= %s where user_id = %s", 
                               (new_name, id))
            case '2':
                printing_sys_lft("Enter a new user email: ")
                new_email= input()
                cursor.execute("update users set email = %s where user_id = %s",
                               (new_email, id))
            case '3':
                printing_sys_lft("Enter a new phone number: ")
                new_phone = input()
                cursor.execute("UPDATE users SET phone_number = %s WHERE user_id = %s",
                                (new_phone, id))
            case '4':
                printing_sys_lft("Enter a new address: ")
                new_address = input()
                cursor.execute("UPDATE users SET address = %s WHERE user_id = %s",
                                (new_address, id))
            case "Quit":
                printing_sys_lft("Quitting.....")
                return 

        printing_sys_lft("Do you wish to make any other changes? [y/n]")
        ans = input()
        if ans == 'y':
            continue
        else:
            break

    conn.commit()
    printing_sys_lft("Data saved.")
    get_user_full_data(id)





# /////////////////////////////////////////////////////////////////////////////////
#               Accounts
# /////////////////////////////////////////////////////////////////////////////////


# for seting a new account
def creat_new_account(user_id, iban):

    try:
        cursor.execute(
            """
            INSERT INTO accounts
            (user_id, iban) VALUES (%s, %s) """,
            (user_id, iban)
        )
    except mysql.connector.errors.IntegrityError:
        print("Account exists with similar user_id or iban")
        return False

    conn.commit()

    account_id = cursor.lastrowid

    cursor.execute(
        "SELECT * FROM accounts WHERE user_id = %s",
        (account_id,)
    )
    

    print(cursor.fetchone())
    return True    


# getting the acount useing the account id
def get_account(account_id):
    cursor.execute(
        """
        SELECT *
        FROM accounts
        WHERE account_id = %s
        """,
        (account_id,)    
    )

    account = cursor.fetchall()
    if account is None:
        print("Account doesn't exist.")
        return 

    print(f" -> Account: {account}")




def get_account_id(user_id, iban):

    cursor.execute(
        """
        SELECT account_id
        FROM accounts
        WHERE user_id = %s
          AND iban = %s
        """,
        (user_id, iban)
    )

    account = cursor.fetchone()

    if account is None:
        printing_sys_lft("Authentication failed.")
        return
    
    print(f"Account ID: {account[0]}" )



def get_account_type(account_id, user_id, iban):

    cursor.execute(
        """
        SELECT account_type
        FROM accounts
        WHERE account_id = %s
        AND user_id = %s
          AND iban = %s
        """,
        (account_id, user_id, iban)
    )

    account = cursor.fetchone()

    if account is None:
        printing_sys_lft("Authentication failed.")
        return
    
    print(f"Account type: {account[0]}" )
    print()



def set_account_type(account_id, new_type):

    cursor.execute(
        """
        UPDATE accounts
        SET account_type = %s
        WHERE account_id = %s
        """,
        (new_type, account_id)
    )
    conn.commit()

    cursor.execute(
        """
        SELECT account_type
        FROM accounts
        WHERE account_id = %s
        """,
        (account_id,)
    )

    account = cursor.fetchone()

    if account is None:
        printing_sys_lft("Authentication failed.")
        return
    
    print(f"Account type: {account[0]}")




def get_balance(account_id):

    cursor.execute(
        """
        SELECT balance 
        FROM accounts
        WHERE account_id = %s
        """,
        (account_id,)
    )

    balance= cursor.fetchone()

    if balance is None:
        print(f"No account with ID: {account_id}")
        return 

    print(f"Account balance: {balance[0]}")
    print()


def close_account(account_id):
    cursor.execute(
        """
        UPDATE accounts
        SET status = 'closed'
        WHERE account_id = %s
        """,
        (account_id,)
    )

    conn.commit()

    cursor.execute(
        """
        SELECT *
        FROM accounts
        WHERE account_id = %s
        """,
        (account_id,)
    )

    account = cursor.fetchone()

    if account is None:
        printing_sys_lft("Authentication failed.")
        return
    
    print(f"Account: {account}")



def freez_account(account_id):
    cursor.execute(
        """
        UPDATE accounts
        SET status = 'frozen'
        WHERE account_id = %s
        """,
        (account_id,)
    )

    conn.commit()

    cursor.execute(
        """
        SELECT *
        FROM accounts
        WHERE account_id = %s
        """,
        (account_id,)
    )

    account = cursor.fetchone()

    if account is None:
        printing_sys_lft("Authentication failed.")
        return
    
    print(f"Account: {account}")




def deposit(account_id, amount):

    if int(amount) < 0:
        print("Amount must be positive.")
        return

    cursor.execute(
        """
        SELECT balance 
        FROM accounts
        WHERE account_id = %s
        """,
        (account_id,)
    )

    balance= cursor.fetchone()

    if balance is None:
        print(f"No account with ID: {account_id}")
        return 

    balance = balance[0]

    balance += Decimal(str(amount))

    if balance < Decimal("0.00"):
        balance = Decimal("0.00")

    cursor.execute(
        """
        UPDATE accounts
        SET balance = %s
        WHERE account_id = %s
        """,
        (balance, account_id)
    )
    conn.commit()

    cursor.execute(
        """
        SELECT *
        FROM accounts
        WHERE account_id = %s
        """,
        (account_id,)
    )

    account = cursor.fetchone()

    if account is None:
        printing_sys_lft("Authentication failed.")
        return
    
    print(f"Account: {account}")




def withdraw(account_id, amount):

    if int(amount) < 0:
        print("Amount must be positive.")
        return

    cursor.execute(
        """
        SELECT balance 
        FROM accounts
        WHERE account_id = %s
        """,
        (account_id,)
    )

    balance= cursor.fetchone()

    if balance is None:
        print(f"No account with ID: {account_id}")
        return 

    balance = balance[0]

    balance -= Decimal(str(amount))

    if balance < Decimal("0.00"):
        balance = Decimal("0.00")

    cursor.execute(
        """
        UPDATE accounts
        SET balance = %s
        WHERE account_id = %s
        """,
        (balance, account_id)
    )
    conn.commit()

    cursor.execute(
        """
        SELECT *
        FROM accounts
        WHERE account_id = %s
        """,
        (account_id,)
    )

    account = cursor.fetchone()

    if account is None:
        printing_sys_lft("Authentication failed.")
        return
    
    print(f"Account: {account}")




# set status
def set_account_status(account_id, stat):
    cursor.execute(
        """
        UPDATE accounts
        SET status = %s
        WHERE account_id= %s
        """,
        (stat, account_id)
    )

    conn.commit()

    cursor.execute(
        """
        SELECT *
        FROM accounts
        WHERE account_id= %s
        """,
        (account_id,)
    )

    account = cursor.fetchone()
    
    if account is None:
        printing_sys_lft("Authentication failed.")
        return
        
    print(f"Account: {account}")





# ========================================================================
#               Card 
# ========================================================================



def add_card_to_account(account_id, card_type, expiry_date, daily_limit):
    """
    Creates a new card for an account.

    Returns:
        (True, card_number) on success
        (False, None) on failure
    """

    MAX_ATTEMPTS = 10

    for _ in range(MAX_ATTEMPTS):

        # Generate a random 16-digit card number
        card_number = str(secrets.randbelow(9_000_000_000_000_000) + 1_000_000_000_000_000)
        cvv = random.randint(100,999)

        last_four = card_number[-4:]

        # Hash the FULL card number
        card_number_hash = hashlib.sha256(
            card_number.encode("utf-8")
        ).hexdigest()

        try:
            cursor.execute(
                """
                INSERT INTO cards
                (
                    account_id,
                    card_number_hash,
                    last_four,
                    card_type,
                    expiry_date,
                    daily_limit,
                    cvv
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    account_id,
                    card_number_hash,
                    last_four,
                    card_type,
                    expiry_date,
                    daily_limit,
                    cvv
                ),
            )

            conn.commit()

            card_id = cursor.lastrowid

            # verify the insert
            cursor.execute(
                """
                SELECT card_id, account_id, last_four, card_type,
                       expiry_date, daily_limit
                FROM cards
                WHERE card_id = %s
                """,
                (card_id,),
            )

            print("Card created:")
            print(cursor.fetchone())

            # return the card number so it can be shown ONCE
            return True, card_number

        except mysql.connector.errors.IntegrityError:
            # duplicate card number hash 
            continue

        except mysql.connector.Error as err:
            print(f"Database error: {err}")
            conn.rollback()
            return False, None

    print("Failed to generate a unique card number after multiple attempts.")
    return False, None





def get_cards(account_id):
    cursor.execute(
        """
        SELECT *
        FROM cards
        WHERE account_id = %s
        """,
        (account_id,)
    )

    cards = cursor.fetchall()

    if cards is None:
        print("User account doesn't exist. ")
        return 

    print("Cards: ")
    for card in cards:
        print(card)
        print()



def card_exists(card_id):
    cursor.execute(
        """
        SELECT *
        FROM cards
        WHERE card_id = %s
        """,
        (card_id,)
    )

    card = cursor.fetchone()

    if card is None:
        print("Card doesn't exist.")
        return False

    return True

def rem_card(card_id):

    if card_exists(card_id) is False:
        return False

    
    cursor.execute(
        """
        DELETE FROM cards
        WHERE card_id = %s
        """,
        (card_id,)
    )

    conn.commit()
    print(f"Card with ID: {card_id} was removed.")
    return True



def set_card_type(card_id, card_type):

    if card_exists(card_id) is False:
        return False    

    cursor.execute(
        """
        UPDATE cards
        SET card_type = %s
        WHERE card_id = %s
        """,
        (card_type, card_id)
    )
    conn.commit()

    return True



def set_daily_limit(card_id, new_limit):

    if card_exists(card_id) is False:
        return False
        
    cursor.execute(
        """
        UPDATE cards
        SET daily_limit = %s
        WHERE card_id = %s
        """,
        (new_limit, card_id)
    )
    conn.commit()    

    return True



def set_status(card_id, stat):

    if card_exists(card_id) is False:
        return False

    
    cursor.execute(
        """
        UPDATE cards
        SET status = %s
        WHERE card_id = %s
        """,
        (stat, card_id)
    )
    conn.commit()    

    return True



# instead of always returning every card on an account.
def get_card(card_id):

    if card_exists(card_id) is False:
        return False

    
    cursor.execute(
        """
        SELECT * 
        FROM cards 
        WHERE card_id = %s
        """,
        (card_id,)
    )
    card = cursor.fetchone()

    if card is None:
        print("Card doesn't exist.")
        return 

    return card



# expire cards automatically
def expire_cards():
    
    cursor.execute(
        """
        UPDATE cards
        SET status = 'expired'
        WHERE expiry_date < %s
        """,
        (datetime.today().strftime('%Y-%m-%d'))
    )
    conn.commit()


# Could:
    # mark old card as blocked //
    # create a new card //
    # keep on the same account // 
    # generate new number // 
    # new expiry date // 

def replace_card(card_id, new_expiry_date):

    if card_exists(card_id) is False:
        return False

    old_card = get_card(card_id)

    cursor.execute(
        """
        UPDATE cards
        SET status = 'blocked'
        WHERE card_id = %s
        """,
        (card_id,)
    )
    conn.commit()
    print("Old card is now blocked and will be removed.")
    rem_card(card_id)
    printing_sys_lft("Creating new card.......")
    printing_sys_lft("............",0.10)
    printing_sys_lft("Done", 0.10)

    # print(old_card[1], old_card[4], old_card[6])
    return add_card_to_account(old_card[1], old_card[4], new_expiry_date, old_card[6])




def block_card(card_id):

    if card_exists(card_id) is False:
        return False

    
    cursor.execute(
        """
        UPDATE cards
        SET status = 'blocked'
        WHERE card_id = %s
        """,
        (card_id,)
    )
    conn.commit()    

    return True



def unblock_card(card_id):

    if card_exists(card_id) is False:
        return False

    
    cursor.execute(
        """
        UPDATE cards
        SET status = 'active'
        WHERE card_id = %s
        """,
        (card_id,)
    )
    conn.commit()    

    return True


def is_card_active(card_id):

    card = get_card(card_id)
    if not card:
        return False

    if card[7] == "active":
        return True

    return False


def is_card_expired(card_id):
    """
    Checks the actual expiry_date, not just the status column - status only
    gets flipped to 'expired' when expire_cards() runs, so relying on status
    alone would say a card is fine right up until the next batch run even
    if its expiry date has already passed.
    """
    card = get_card(card_id)
    if not card:
        return True

    expiry_date, status = card[5], card[7]
    return status == "expired" or expiry_date < date.today()



# Checks

    # active?
    # not expired?
    # amount <= daily_limit?
#  then true, else false 
def can_spend(card_id, amount):

    amount = Decimal(str(amount))
    card = get_card(card_id)
    if not card:
        return False

    if is_card_active(card_id) is False:
        print("Card is inactive. ")
        return False
    elif is_card_expired(card_id) is True:
        print("Card is expired.")
        return False

    daily_limit = card[6]
    spent_today = _card_spent_today(card_id)
    if spent_today + amount > daily_limit:
        print("Amount would exceed the daily limit.")
        return False

    return True
    

def count_cards(account_id):
    cursor.execute(
        """
        SELECT * 
        FROM cards
        WHERE account_id = %s
        """,
        (account_id,)
    )
    cards = cursor.fetchall()

    return len(cards)



def count_active_cards(account_id):
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM cards
        WHERE status = 'active'
          AND account_id = %s
        """,
        (account_id,)
    )

    return cursor.fetchone()[0]

def count_blocked_cards(account_id):
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM cards
        WHERE status = 'blocked'
          AND account_id = %s
        """,
        (account_id,)
    )

    return cursor.fetchone()[0]


def find_card_by_last_four(last_four):
    """
    Returns ALL matching cards, not just one - the last 4 digits are only
    10,000 possible combinations, so they're not unique across a real card
    base. Use this to narrow down candidates (e.g. 'which of your cards
    ends in 1234?'), not as a unique lookup key.
    """
    cursor.execute(
        """
        SELECT *
        FROM cards
        WHERE last_four = %s
        """,
        (last_four,)
    )
    return cursor.fetchall()


def freez_card(card_id):

    if card_exists(card_id) is False:
        return False

    cursor.execute(
        """
        UPDATE cards
        SET status = 'frozen'
        WHERE card_id = %s
        """,
        (card_id,)
    )
    conn.commit()
    return True




def _account_exists(account_id):
    cursor.execute("SELECT 1 FROM accounts WHERE account_id = %s", (account_id,))
    return cursor.fetchone() is not None


def purchase(card_id, merchant_account_id, amount):
    """
    A card purchase: debits the cardholder via the card (so daily_limit,
    active/expiry checks, locking, and the ledger all apply - the same
    protections withdraw_via_card() gives any other card withdrawal) and
    credits the merchant's account. If crediting the merchant fails for any
    reason, the cardholder is refunded and the original debit is marked
    'reversed' rather than silently leaving them out of pocket.
    """
    if card_exists(card_id) is False:
        return False, "Card doesn't exist."
    if _account_exists(merchant_account_id) is False:
        return False, "Merchant account doesn't exist."

    debit_ok, debit_result = withdraw_via_card(card_id, amount)
    if not debit_ok:
        return False, debit_result

    credit_ok, credit_result = deposit_funds(
        merchant_account_id, amount, description=f"Purchase via card {card_id}"
    )
    if not credit_ok:
        cursor.execute(
            "SELECT from_account_id FROM transactions WHERE transaction_id = %s",
            (debit_result,)
        )
        row = cursor.fetchone()
        cardholder_account_id = row[0] if row else None
        if cardholder_account_id:
            deposit_funds(
                cardholder_account_id, amount,
                description=f"Refund for failed purchase (tx {debit_result})"
            )
            cursor.execute(
                "UPDATE transactions SET status = 'reversed' WHERE transaction_id = %s",
                (debit_result,)
            )
            conn.commit()
        return False, f"Purchase failed and was refunded: {credit_result}"

    return True, {"debit_transaction": debit_result, "credit_transaction": credit_result}


def transfer(card_id, destination_account_id, amount):
    """
    Card-initiated transfer to another account at this bank. Debits via
    the card (daily_limit/active/expiry enforced) and credits the
    destination account, refunding the cardholder if the credit leg fails.
    """
    if card_exists(card_id) is False:
        return False, "Card doesn't exist."
    if _account_exists(destination_account_id) is False:
        return False, "Destination account doesn't exist."

    debit_ok, debit_result = withdraw_via_card(card_id, amount)
    if not debit_ok:
        return False, debit_result

    credit_ok, credit_result = deposit_funds(
        destination_account_id, amount, description=f"Transfer via card {card_id}"
    )
    if not credit_ok:
        cursor.execute(
            "SELECT from_account_id FROM transactions WHERE transaction_id = %s",
            (debit_result,)
        )
        row = cursor.fetchone()
        cardholder_account_id = row[0] if row else None
        if cardholder_account_id:
            deposit_funds(
                cardholder_account_id, amount,
                description=f"Refund for failed transfer (tx {debit_result})"
            )
            cursor.execute(
                "UPDATE transactions SET status = 'reversed' WHERE transaction_id = %s",
                (debit_result,)
            )
            conn.commit()
        return False, f"Transfer failed and was refunded: {credit_result}"

    return True, {"debit_transaction": debit_result, "credit_transaction": credit_result}



# ========================================================================
#               Internal helpers (row locking + ledger writes)
# ========================================================================
# Every function below that moves money goes through these two helpers so
# there's one consistent place enforcing locking and one consistent place
# writing to the transactions ledger, instead of each function inventing
# its own version (which is how deposit()/withdraw() above ended up with
# no ledger entries and no protection against concurrent requests).

def _lock_account(account_id):
    """
    Locks an account row for the rest of the CURRENT transaction (must be
    called after conn.start_transaction()). Returns (balance, overdraft_limit,
    status) or None. This is what stops two withdrawals from both reading
    the same starting balance and both succeeding.
    """
    cursor.execute(
        """
        SELECT balance, overdraft_limit, status
        FROM accounts
        WHERE account_id = %s
        FOR UPDATE
        """,
        (account_id,)
    )
    return cursor.fetchone()


def _insert_transaction(from_account_id, to_account_id, amount, transaction_type,
                         status='completed', reference=None, description=None,
                         idempotency_key=None, currency='EUR'):
    processed_at = datetime.now() if status == 'completed' else None
    cursor.execute(
        """
        INSERT INTO transactions
        (from_account_id, to_account_id, amount, currency, transaction_type,
         status, reference, description, idempotency_key, processed_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (from_account_id, to_account_id, amount, currency, transaction_type,
         status, reference, description, idempotency_key, processed_at)
    )
    return cursor.lastrowid


def _get_existing_by_idempotency_key(idempotency_key):
    """
    Real banking APIs require an idempotency key on anything that moves
    money, precisely so that a retried request (timeout, dropped connection,
    a user double-tapping 'send') can never charge someone twice.
    """
    if not idempotency_key:
        return None
    cursor.execute(
        "SELECT transaction_id, status FROM transactions WHERE idempotency_key = %s",
        (idempotency_key,)
    )
    return cursor.fetchone()


# ========================================================================
#               Transactions
# ========================================================================

def transfer_funds(from_account_id, to_account_id, amount, description=None, idempotency_key=None):
    """
    Moves money between two accounts at this bank. Used directly, and also
    reused by transfer_by_iban(), pay_with_code(), and the scheduled
    payment processor below, so all money movement shares the same
    locking/overdraft/ledger behavior.

    Real-world practices applied:
      - row locking (SELECT ... FOR UPDATE) so concurrent transfers can't race
      - accounts locked in a fixed order (lowest account_id first) so two
        transfers going opposite directions can't deadlock each other
      - idempotency key so a retried/duplicate request can't move money twice
      - overdraft_limit respected instead of a hard floor of zero
    """
    amount = Decimal(str(amount))
    if amount <= 0:
        return False, "Amount must be positive."
    if from_account_id == to_account_id:
        return False, "Cannot transfer to the same account."

    existing = _get_existing_by_idempotency_key(idempotency_key)
    if existing:
        return True, f"Already processed as transaction {existing[0]} ({existing[1]})"

    try:
        conn.start_transaction()

        first_id, second_id = sorted([from_account_id, to_account_id])
        first_row = _lock_account(first_id)
        second_row = _lock_account(second_id)
        rows = {first_id: first_row, second_id: second_row}
        from_row, to_row = rows[from_account_id], rows[to_account_id]

        if from_row is None or to_row is None:
            conn.rollback()
            return False, "One or both accounts don't exist."

        from_balance, from_overdraft, from_status = from_row
        to_balance, _, to_status = to_row

        if from_status != 'active' or to_status != 'active':
            conn.rollback()
            return False, "One or both accounts are not active."

        if from_balance - amount < -from_overdraft:
            conn.rollback()
            return False, "Insufficient funds (including overdraft limit)."

        cursor.execute("UPDATE accounts SET balance = balance - %s WHERE account_id = %s",
                        (amount, from_account_id))
        cursor.execute("UPDATE accounts SET balance = balance + %s WHERE account_id = %s",
                        (amount, to_account_id))

        transaction_id = _insert_transaction(
            from_account_id, to_account_id, amount, 'transfer_iban',
            status='completed', description=description, idempotency_key=idempotency_key
        )

        conn.commit()
        return True, transaction_id

    except mysql.connector.Error as err:
        conn.rollback()
        return False, f"Database error: {err}"


def transfer_by_iban(from_account_id, to_iban, amount, description=None, idempotency_key=None):
    """
    Resolves the destination IBAN to an account at this bank and transfers
    funds. NOTE: this only works for IBANs that exist in our own `accounts`
    table. A transfer to a (different) bank would need to go out over a real
    payment rail (SEPA Credit Transfer in the EU, SWIFT internationally)
    that's a settlement network integration this script can't do on its own,
    so unknown IBANs are rejected rather than silently pretending to send
    money that never arrives.
    """
    cursor.execute("SELECT account_id, status FROM accounts WHERE iban = %s", (to_iban,))
    row = cursor.fetchone()
    if row is None:
        return False, "Destination IBAN not found at this bank."

    to_account_id, to_status = row
    if to_status != 'active':
        return False, "Destination account is not active."

    return transfer_funds(from_account_id, to_account_id, amount, description, idempotency_key)


def _card_spent_today(card_id):
    """
    Shared by withdraw_via_card() and can_spend() so the two can't drift
    out of sync on what 'already spent today' means.
    """
    cursor.execute(
        """
        SELECT COALESCE(SUM(amount), 0) FROM transactions
        WHERE transaction_type = 'withdrawal_card' AND reference = %s
          AND status = 'completed' AND DATE(created_at) = CURDATE()
        """,
        (str(card_id),)
    )
    return cursor.fetchone()[0]


def withdraw_via_card(card_id, amount):
    """
    Withdraws using a bank card, enforcing the card's daily_limit the
    same control every card issuer applies at ATMs/POS terminals before
    authorizing a transaction.
    """
    amount = Decimal(str(amount))
    if amount <= 0:
        return False, "Amount must be positive."

    cursor.execute(
        "SELECT account_id, status, expiry_date, daily_limit FROM cards WHERE card_id = %s",
        (card_id,)
    )
    card = cursor.fetchone()
    if card is None:
        return False, "Card not found."

    account_id, card_status, expiry_date, daily_limit = card
    if card_status != 'active':
        return False, "Card is not active."
    if expiry_date < date.today():
        return False, "Card has expired."

    spent_today = _card_spent_today(card_id)

    if spent_today + amount > daily_limit:
        return False, f"Daily card limit exceeded (limit: {daily_limit}, already used: {spent_today})."

    try:
        conn.start_transaction()
        row = _lock_account(account_id)
        if row is None:
            conn.rollback()
            return False, "Account not found."

        balance, overdraft_limit, status = row
        if status != 'active':
            conn.rollback()
            return False, "Account is not active."
        if balance - amount < -overdraft_limit:
            conn.rollback()
            return False, "Insufficient funds (including overdraft limit)."

        cursor.execute("UPDATE accounts SET balance = balance - %s WHERE account_id = %s",
                        (amount, account_id))
        transaction_id = _insert_transaction(
            account_id, None, amount, 'withdrawal_card',
            status='completed', reference=str(card_id), description="Card withdrawal"
        )
        conn.commit()
        return True, transaction_id

    except mysql.connector.Error as err:
        conn.rollback()
        return False, f"Database error: {err}"


def withdraw_via_mbway(mbway_id, amount):
    """Same pattern as withdraw_via_card(), for MBWay-linked withdrawals."""
    amount = Decimal(str(amount))
    if amount <= 0:
        return False, "Amount must be positive."

    cursor.execute("SELECT account_id, status FROM mbway_links WHERE mbway_id = %s", (mbway_id,))
    link = cursor.fetchone()
    if link is None:
        return False, "MBWay link not found."

    account_id, link_status = link
    if link_status != 'active':
        return False, "MBWay link is not active."

    try:
        conn.start_transaction()
        row = _lock_account(account_id)
        if row is None:
            conn.rollback()
            return False, "Account not found."

        balance, overdraft_limit, status = row
        if status != 'active':
            conn.rollback()
            return False, "Account is not active."
        if balance - amount < -overdraft_limit:
            conn.rollback()
            return False, "Insufficient funds (including overdraft limit)."

        cursor.execute("UPDATE accounts SET balance = balance - %s WHERE account_id = %s",
                        (amount, account_id))
        transaction_id = _insert_transaction(
            account_id, None, amount, 'withdrawal_mbway',
            status='completed', reference=str(mbway_id), description="MBWay withdrawal"
        )
        conn.commit()
        return True, transaction_id

    except mysql.connector.Error as err:
        conn.rollback()
        return False, f"Database error: {err}"


def deposit_funds(account_id, amount, description=None):
    """
    Ledger-backed deposit. Prefer this over the plain deposit() above going
    forward - this one locks the row and writes a transactions record;
    deposit() does neither.
    """
    amount = Decimal(str(amount))
    if amount <= 0:
        return False, "Amount must be positive."

    try:
        conn.start_transaction()
        row = _lock_account(account_id)
        if row is None:
            conn.rollback()
            return False, "Account not found."

        _, _, status = row
        if status != 'active':
            conn.rollback()
            return False, "Account is not active."

        cursor.execute("UPDATE accounts SET balance = balance + %s WHERE account_id = %s",
                        (amount, account_id))
        transaction_id = _insert_transaction(
            None, account_id, amount, 'deposit', status='completed', description=description
        )
        conn.commit()
        return True, transaction_id

    except mysql.connector.Error as err:
        conn.rollback()
        return False, f"Database error: {err}"


def reverse_transaction(transaction_id, reason=None):
    """
    Reversal/chargeback support - standard for disputed payments, failed
    downstream processing, or fraud response. Rather than editing the
    original row, the original is marked 'reversed' and a brand new
    transaction moves the money back, so the ledger keeps an honest,
    append-only history of what actually happened.
    """
    try:
        conn.start_transaction()

        cursor.execute(
            """
            SELECT from_account_id, to_account_id, amount, status, transaction_type
            FROM transactions WHERE transaction_id = %s FOR UPDATE
            """,
            (transaction_id,)
        )
        tx = cursor.fetchone()
        if tx is None:
            conn.rollback()
            return False, "Transaction not found."

        from_account_id, to_account_id, amount, status, tx_type = tx

        if status != 'completed':
            conn.rollback()
            return False, f"Only completed transactions can be reversed (current status: {status})."
        if from_account_id is None or to_account_id is None:
            conn.rollback()
            return False, "Can't auto-reverse a transaction with an external leg - handle manually."

        first_id, second_id = sorted([from_account_id, to_account_id])
        _lock_account(first_id)
        _lock_account(second_id)

        cursor.execute("UPDATE accounts SET balance = balance + %s WHERE account_id = %s",
                        (amount, from_account_id))
        cursor.execute("UPDATE accounts SET balance = balance - %s WHERE account_id = %s",
                        (amount, to_account_id))
        cursor.execute("UPDATE transactions SET status = 'reversed' WHERE transaction_id = %s",
                        (transaction_id,))

        note = f"Reversal of transaction {transaction_id}"
        if reason:
            note += f": {reason}"

        reversal_id = _insert_transaction(
            to_account_id, from_account_id, amount, tx_type, status='completed', description=note
        )

        conn.commit()
        return True, reversal_id

    except mysql.connector.Error as err:
        conn.rollback()
        return False, f"Database error: {err}"


def get_transaction_history(account_id, start_date=None, end_date=None, limit=50, offset=0):
    """Paginated statement-style history - what a bank app shows under 'Transactions'."""
    query = """
        SELECT transaction_id, from_account_id, to_account_id, amount, currency,
               transaction_type, status, reference, description, created_at
        FROM transactions
        WHERE (from_account_id = %s OR to_account_id = %s)
    """
    params = [account_id, account_id]

    if start_date:
        query += " AND created_at >= %s"
        params.append(start_date)
    if end_date:
        query += " AND created_at <= %s"
        params.append(end_date)

    query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    return rows


# ========================================================================
#               Payment Codes  (Multibanco-style reference codes)
# ========================================================================

def _generate_reference_code():
    entity = f"{secrets.randbelow(90000) + 10000}"
    reference = f"{secrets.randbelow(900000000) + 100000000}"
    return f"{entity}-{reference}"


def generate_payment_code(account_id, amount, description=None, valid_days=1):
    """
    Creates a payment reference a merchant/biller can hand to a payer - like
    a Multibanco reference in Portugal, or a virtual account number
    elsewhere. Whoever pays the code sends money straight to account_id.
    """
    amount = Decimal(str(amount))
    if amount <= 0:
        return False, "Amount must be positive."

    expires_at = datetime.now() + timedelta(days=valid_days)

    for _ in range(10):
        code = _generate_reference_code()
        try:
            cursor.execute(
                """
                INSERT INTO payment_codes (code, account_id, amount, description, expires_at)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (code, account_id, amount, description, expires_at)
            )
            conn.commit()
            return True, code
        except mysql.connector.errors.IntegrityError:
            continue  # code collision (extremely unlikely) - try again

    return False, "Could not generate a unique payment code."


def check_payment_code(code):
    """Preview a code before paying it - like scanning a reference to see the amount due."""
    cursor.execute(
        "SELECT account_id, amount, description, is_used, expires_at FROM payment_codes WHERE code = %s",
        (code,)
    )
    row = cursor.fetchone()
    if row:
        print(row)
    return row


def pay_with_code(payer_account_id, code):
    """
    Pays a payment code - like entering a Multibanco reference at an ATM
    or in home banking. Marking the code used and moving the money can't be
    a single call to transfer_funds() (it opens its own transaction), so
    this uses a compensating-action pattern: mark the code used, then if
    the transfer fails, undo that flag. This "saga" style is genuinely how
    real distributed banking systems coordinate multi-step operations.
    """
    try:
        conn.start_transaction()
        cursor.execute(
            """
            SELECT account_id, amount, is_used, expires_at
            FROM payment_codes WHERE code = %s FOR UPDATE
            """,
            (code,)
        )
        row = cursor.fetchone()

        if row is None:
            conn.rollback()
            return False, "Payment code not found."

        payee_account_id, amount, is_used, expires_at = row

        if is_used:
            conn.rollback()
            return False, "This payment code has already been used."
        if expires_at < datetime.now():
            conn.rollback()
            return False, "This payment code has expired."

        cursor.execute("UPDATE payment_codes SET is_used = TRUE WHERE code = %s", (code,))
        conn.commit()

    except mysql.connector.Error as err:
        conn.rollback()
        return False, f"Database error: {err}"

    success, result = transfer_funds(payer_account_id, payee_account_id, amount,
                                      description=f"Payment code {code}")

    if not success:
        cursor.execute("UPDATE payment_codes SET is_used = FALSE WHERE code = %s", (code,))
        conn.commit()

    return success, result


def cancel_payment_code(code):
    """Lets whoever generated the code invalidate it early (e.g. an invoice was cancelled)."""
    cursor.execute(
        "UPDATE payment_codes SET expires_at = NOW() WHERE code = %s AND is_used = FALSE",
        (code,)
    )
    conn.commit()
    return cursor.rowcount > 0


# ========================================================================
#               Scheduled / Recurring Payments (standing orders)
# ========================================================================

def create_scheduled_payment(account_id, payee_iban, amount, frequency, next_due_date, description=None):
    """frequency: 'once', 'weekly', 'monthly', 'yearly' - a standing order/direct debit."""
    amount = Decimal(str(amount))
    if amount <= 0:
        return False, "Amount must be positive."
    if frequency not in ('once', 'weekly', 'monthly', 'yearly'):
        return False, "Invalid frequency."

    cursor.execute(
        """
        INSERT INTO scheduled_payments
        (account_id, payee_iban, amount, frequency, next_due_date, description)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (account_id, payee_iban, amount, frequency, next_due_date, description)
    )
    conn.commit()
    return True, cursor.lastrowid


def pause_scheduled_payment(scheduled_id):
    cursor.execute("UPDATE scheduled_payments SET status = 'paused' WHERE scheduled_id = %s", (scheduled_id,))
    conn.commit()
    return cursor.rowcount > 0


def resume_scheduled_payment(scheduled_id):
    cursor.execute("UPDATE scheduled_payments SET status = 'active' WHERE scheduled_id = %s", (scheduled_id,))
    conn.commit()
    return cursor.rowcount > 0


def cancel_scheduled_payment(scheduled_id):
    # NOTE: the schema's status CHECK only allows active/paused/completed/failed,
    # so 'paused' is reused here to mean "cancelled, won't run again." Add a real
    # 'cancelled' value to the CHECK constraint later if you want to distinguish
    # "paused, might resume" from "cancelled for good."
    cursor.execute("UPDATE scheduled_payments SET status = 'paused' WHERE scheduled_id = %s", (scheduled_id,))
    conn.commit()
    return cursor.rowcount > 0


def _advance_due_date(current_due, frequency):
    if frequency == 'weekly':
        return current_due + timedelta(days=7)
    if frequency == 'monthly':
        month = current_due.month + 1
        year = current_due.year + (month - 1) // 12
        month = ((month - 1) % 12) + 1
        day = min(current_due.day, calendar.monthrange(year, month)[1])
        return date(year, month, day)
    if frequency == 'yearly':
        try:
            return current_due.replace(year=current_due.year + 1)
        except ValueError:  # Feb 29 on a non-leap year
            return current_due.replace(year=current_due.year + 1, day=28)
    return None  # 'once' has no next date


def process_due_scheduled_payments():
    """
    The batch job every bank runs (usually nightly) to execute standing
    orders/direct debits that have come due. In production this would be
    triggered by a scheduler (cron, APScheduler, etc.) rather than called
    by hand.
    """
    cursor.execute(
        """
        SELECT scheduled_id, account_id, payee_iban, amount, frequency, next_due_date
        FROM scheduled_payments
        WHERE status = 'active' AND next_due_date <= CURDATE()
        """
    )
    due_payments = cursor.fetchall()

    results = []
    for scheduled_id, account_id, payee_iban, amount, frequency, next_due_date in due_payments:
        success, result = transfer_by_iban(
            account_id, payee_iban, amount, description=f"Scheduled payment #{scheduled_id}"
        )

        if success:
            if frequency == 'once':
                cursor.execute("UPDATE scheduled_payments SET status = 'completed' WHERE scheduled_id = %s",
                                (scheduled_id,))
            else:
                new_due_date = _advance_due_date(next_due_date, frequency)
                cursor.execute("UPDATE scheduled_payments SET next_due_date = %s WHERE scheduled_id = %s",
                                (new_due_date, scheduled_id))
            conn.commit()
        else:
            # Left 'active' so it's retried next run (e.g. insufficient funds today).
            # A production system would also track a retry count and eventually
            # flag it 'failed' + notify the user after N misses.
            print(f"Scheduled payment {scheduled_id} failed: {result}")

        results.append((scheduled_id, success, result))

    return results


# checkes the system and returns (no payments) if theres no payments
# prints n + the payments needed to do 
# returns false if the account_id doesn't exist
def check_if_theres_payments(account_id):
    cursor.execute(
        """
        SELECT *
        FROM scheduled_payments
        WHERE account_id = %s
        """,
        (account_id,)
    )

    payments = cursor.fetchall()

    if payments is None:
        print("Account doesn't exsist")
        return False
    if len(payments) == 0:
        print("No payments.")
        return True

    print(f"You have {len(payments)} deu.")
    for payment in payments:
        print()
        print(payment)
    return True
    



# ========================================================================
#               Market Data + AI Recommendations
# ========================================================================
# Kept logically separate from the money-movement tables on purpose: a bug
# in the market scraper or the AI advisor should never be able to touch a
# real account balance, so nothing here writes to accounts/transactions.

def add_market_asset(symbol, name, asset_type='stock'):
    """asset_type: 'stock', 'etf', or 'crypto'."""
    try:
        cursor.execute(
            "INSERT INTO market_assets (symbol, name, asset_type) VALUES (%s, %s, %s)",
            (symbol, name, asset_type)
        )
        conn.commit()
        return True, cursor.lastrowid
    except mysql.connector.errors.IntegrityError:
        return False, "An asset with that symbol already exists."


def get_asset_by_symbol(symbol):
    cursor.execute("SELECT * FROM market_assets WHERE symbol = %s", (symbol,))
    return cursor.fetchone()


def record_market_price(asset_id, price):
    """
    Call this every time your scraper pulls a fresh quote. Prices are
    append-only (never overwritten or updated in place) so you keep a full
    price history to chart and to feed the AI recommender.
    """
    price = Decimal(str(price))
    if price <= 0:
        return False, "Price must be positive."

    cursor.execute(
        "INSERT INTO market_prices (asset_id, price) VALUES (%s, %s)",
        (asset_id, price)
    )
    conn.commit()
    return True, cursor.lastrowid


def get_latest_price(asset_id):
    cursor.execute(
        """
        SELECT price, fetched_at FROM market_prices
        WHERE asset_id = %s ORDER BY fetched_at DESC LIMIT 1
        """,
        (asset_id,)
    )
    return cursor.fetchone()


def is_price_stale(asset_id, max_age_minutes=15):
    """
    Real trading/advisory systems refuse to act on a quote that's too old -
    acting on a stale price is how you end up recommending a 'buy' at a
    price that isn't real anymore.
    """
    row = get_latest_price(asset_id)
    if row is None:
        return True
    _, fetched_at = row
    return (datetime.now() - fetched_at) > timedelta(minutes=max_age_minutes)


def get_price_history(asset_id, start=None, end=None, limit=100):
    """For charting, or for feeding a model that needs a price series."""
    query = "SELECT price, fetched_at FROM market_prices WHERE asset_id = %s"
    params = [asset_id]
    if start:
        query += " AND fetched_at >= %s"
        params.append(start)
    if end:
        query += " AND fetched_at <= %s"
        params.append(end)
    query += " ORDER BY fetched_at DESC LIMIT %s"
    params.append(limit)

    cursor.execute(query, tuple(params))
    return cursor.fetchall()


def save_ai_recommendation(user_id, asset_id, action, confidence=None, reasoning=None):
    """action: 'buy', 'sell', or 'hold'."""
    if action not in ('buy', 'sell', 'hold'):
        return False, "Invalid action."

    cursor.execute(
        """
        INSERT INTO ai_recommendations (user_id, asset_id, action, confidence, reasoning)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (user_id, asset_id, action, confidence, reasoning)
    )
    conn.commit()
    return True, cursor.lastrowid


def get_recommendations_for_user(user_id, limit=20):
    cursor.execute(
        """
        SELECT r.recommendation_id, a.symbol, r.action, r.confidence, r.reasoning, r.created_at
        FROM ai_recommendations r
        JOIN market_assets a ON a.asset_id = r.asset_id
        WHERE r.user_id = %s
        ORDER BY r.created_at DESC
        LIMIT %s
        """,
        (user_id, limit)
    )
    return cursor.fetchall()


def get_latest_recommendation_per_asset(user_id):
    """
    Only the most recent recommendation per asset - a user shouldn't see a
    three-day-old 'buy' sitting next to today's 'sell' for the same stock.
    """
    cursor.execute(
        """
        SELECT r.asset_id, a.symbol, r.action, r.confidence, r.created_at
        FROM ai_recommendations r
        JOIN market_assets a ON a.asset_id = r.asset_id
        WHERE r.user_id = %s
          AND r.created_at = (
              SELECT MAX(r2.created_at)
              FROM ai_recommendations r2
              WHERE r2.user_id = r.user_id AND r2.asset_id = r.asset_id
          )
        ORDER BY a.symbol
        """,
        (user_id,)
    )
    return cursor.fetchall()


# ========================================================================
#               Audit Log
# ========================================================================
# Every action that touches money, auth, or account status should write a
# row here. Real banks log this by regulatory requirement (traceability
# for fraud investigations and disputes) - it isn't optional the way it
# might feel for a student project.

def log_audit_event(user_id, action, ip_address=None, details=None):
    """
    Never raises a logging failure should never take down the operation
    that triggered it. Prints a warning instead if the insert fails.
    """
    try:
        details_json = _json.dumps(details) if details is not None else None
        cursor.execute(
            """
            INSERT INTO audit_log (user_id, action, ip_address, details)
            VALUES (%s, %s, %s, %s)
            """,
            (user_id, action, ip_address, details_json)
        )
        conn.commit()
        return True
    except mysql.connector.Error as err:
        print(f"[audit log warning] failed to record '{action}' for user {user_id}: {err}")
        return False


def get_audit_log_for_user(user_id, limit=50):
    cursor.execute(
        """
        SELECT log_id, action, ip_address, details, created_at
        FROM audit_log
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT %s
        """,
        (user_id, limit)
    )
    return cursor.fetchall()


def get_recent_audit_events(limit=100):
    """Global activity feed - what an ops/admin dashboard would show."""
    cursor.execute(
        "SELECT * FROM audit_log ORDER BY created_at DESC LIMIT %s",
        (limit,)
    )
    return cursor.fetchall()


def search_audit_log(action=None, user_id=None, start_date=None, end_date=None, limit=100):
    """
    Flexible filter for compliance/fraud investigations - e.g. 'show me
    every withdrawal across all users in the last 24 hours.'
    """
    query = "SELECT * FROM audit_log WHERE 1=1"
    params = []
    if action:
        query += " AND action = %s"
        params.append(action)
    if user_id:
        query += " AND user_id = %s"
        params.append(user_id)
    if start_date:
        query += " AND created_at >= %s"
        params.append(start_date)
    if end_date:
        query += " AND created_at <= %s"
        params.append(end_date)
    query += " ORDER BY created_at DESC LIMIT %s"
    params.append(limit)

    cursor.execute(query, tuple(params))
    return cursor.fetchall()


# ========================================================================
#               Sessions (login/logout, token-based auth)
# ========================================================================
# Same principle as the password/masterKey hashing from your earlier
# password-manager project: the raw session token is shown to the caller
# ONCE and only its hash is stored, so a leaked database dump doesn't hand
# out working login sessions.

def _hash_token(raw_token):
    return hashlib.sha256(raw_token.encode('utf-8')).hexdigest()


def create_session(user_id, expires_in_minutes=30):
    """
    Call this on successful login. Returns (session_id, raw_token) - give
    raw_token to the client (cookie/header) and never store it anywhere
    yourself; only its hash lives in the DB.
    """
    session_id = str(uuid.uuid4())
    raw_token = secrets.token_urlsafe(32)
    token_hash = _hash_token(raw_token)
    expires_at = datetime.now() + timedelta(minutes=expires_in_minutes)

    cursor.execute(
        """
        INSERT INTO sessions (session_id, user_id, token_hash, expires_at)
        VALUES (%s, %s, %s, %s)
        """,
        (session_id, user_id, token_hash, expires_at)
    )
    conn.commit()

    log_audit_event(user_id, 'LOGIN', details={'session_id': session_id})

    return session_id, raw_token


def validate_session(raw_token):
    """
    Call this on every authenticated request. Returns the user_id if the
    token is valid, not revoked, and not expired - otherwise None.
    """
    token_hash = _hash_token(raw_token)
    cursor.execute(
        "SELECT user_id, expires_at, revoked FROM sessions WHERE token_hash = %s",
        (token_hash,)
    )
    row = cursor.fetchone()
    if row is None:
        return None

    user_id, expires_at, revoked = row
    if revoked or expires_at < datetime.now():
        return None

    return user_id


def revoke_session(session_id):
    """Logout for a single device/session."""
    cursor.execute("UPDATE sessions SET revoked = TRUE WHERE session_id = %s", (session_id,))
    conn.commit()
    return cursor.rowcount > 0


def revoke_all_sessions_for_user(user_id):
    """
    'Log out everywhere' - a real feature in every major banking app for
    when you suspect your account may be compromised.
    """
    cursor.execute("UPDATE sessions SET revoked = TRUE WHERE user_id = %s", (user_id,))
    conn.commit()
    log_audit_event(user_id, 'LOGOUT_ALL_DEVICES')
    return cursor.rowcount


def get_active_sessions_for_user(user_id):
    """'Manage your devices' screen - active, non-revoked, non-expired sessions."""
    cursor.execute(
        """
        SELECT session_id, created_at, expires_at
        FROM sessions
        WHERE user_id = %s AND revoked = FALSE AND expires_at > NOW()
        ORDER BY created_at DESC
        """,
        (user_id,)
    )
    return cursor.fetchall()


def cleanup_expired_sessions():
    """
    Periodic maintenance job (same batch-job pattern as
    process_due_scheduled_payments()) - clears out sessions that expired a
    while ago so the table doesn't grow forever.
    """
    cursor.execute("DELETE FROM sessions WHERE expires_at < NOW() - INTERVAL 7 DAY")
    conn.commit()
    return cursor.rowcount


# ========================================================================
#               Views (read-only convenience wrappers)
# ========================================================================

def get_account_overview(user_id):
    """Quick balance + account summary - what user_account_overview was built for."""
    cursor.execute("SELECT * FROM user_account_overview WHERE user_id = %s", (user_id,))
    return cursor.fetchall()


def get_upcoming_payments_for_user(user_id):
    cursor.execute("SELECT * FROM upcoming_payments WHERE user_id = %s", (user_id,))
    return cursor.fetchall()


def get_all_upcoming_payments():
    """Ops-style view across every user - which standing orders are due in the next 7 days."""
    cursor.execute("SELECT * FROM upcoming_payments")
    return cursor.fetchall()


if __name__ == "__main__":

    # creat_new_user()
    # creat_new_account(1, "9876 54321")
    # deposit(1, 1000.0)
    # add_card_to_account(1, "debit", "2030-01-01", 100.0)



    get_account(1)
    print()
    get_cards(1)
    # # add_card_to_account(1, "debit", "2030-01-02", 100.0)
    # print("ppppppppppp")
    # get_cards(1)
    # print("-----------")
    # replace_card(2, "2040-01-01")



    cursor.close()
    conn.close()
