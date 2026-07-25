import mysql.connector
from security import *
import shutil
import time
from decimal import Decimal


# Step 1: connect to the MySQL server (no specific database yet, since the script creates one)
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='DARKrobin24',
    database="BankSystem"
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
            INSERT INTO Users
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
          AND full_name = %s
          AND pin = %s
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
def set_account(user_id, iban):

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

    print(account)




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

    

set_account_status(1, "active")








































































































































































































cursor.close()
conn.close()


















