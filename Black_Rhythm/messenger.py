import mysql.connector as sqltor
import random
import datetime
import sys
import base64
import crypt
import PySimpleGUI as sg
import time
import threading


#Uploads msg to server
def update_to_server(chat, msg, to, mycon, sercon): 
    #print("Uploading message to server...")
    with sercon.cursor() as sercursor:
        sercursor.execute(f"insert into messages value (\"{chat}\", \"{get_my_id(mycon, sercon)}\", \"{to}\", \"{msg}\", \"{get_cur_time()}\")")
    sercon.commit()

#Update unreceived messages from server
def update_from_server(mycon, sercon, block_size=5): 
    most_recent = last_received(mycon, sercon, "my_interactions")
    p = f"select chat, from_user, to_user, message, date from messages where (from_user = \"{get_my_id(mycon, sercon)}\" or to_user = \"{get_my_id(mycon, sercon)}\") and date > {most_recent}"
    ##print(p)
    chats = display_chats(mycon, sercon)
    #print(chats)
    for y in chats:
        p = f"select chat, from_user, message, date from messages where (chat = \"{y}\") and date > \"{most_recent}\""
        #print(p)
        with sercon.cursor() as sercursor:
            sercursor.execute(f"select chat, from_user, message, date from messages where (chat = \"{y}\") and date > \"{most_recent}\"")
            msg_log = sercursor.fetchall()
        #print("MESSAGE LOG:\n-------------\n ", msg_log)
        for x in msg_log:
            ##print("New messages: ", x)
            key = pack_cipher(get_chat_key(x[0], mycon, sercon))
            msg = decrypt_symmetric_message(x[2], key, block_size)
            p = f"insert into my_interactions values (\"{x[0]}\", \"{x[1]}\", \"{msg}\", \"{x[3]}\")"
            #print(p)
            with mycon.cursor() as mycursor:
                try: 
                    mycursor.execute(f"insert into my_interactions values (\"{x[0]}\", \"{x[1]}\", \"{msg}\", \"{x[3]}\")")
                except: 
                    mycursor.execute(f"insert into my_interactions values (\"{x[0]}\", \"{x[1]}\", \"Unable to decrypt\", \"{x[3]}\")")
            mycon.commit()

#encrypts message with symmetric key and sends
def send(chat, msg, mycon, sercon, block_size=5): 
    key = get_chat_key(chat, mycon, sercon)
    cipher = encrypt_symmetric_message(msg, key, block_size)
    ##print(cipher)
    update_to_server(chat, cipher, chat, mycon, sercon)

#gets symmetric key of chat
def get_chat_key(chat, mycon, sercon): 
    #print(f"select sym_key from chats where chat_name = \"{chat}\"")
    with mycon.cursor() as mycursor:
      mycursor.execute(f"select sym_key from chats where chat_name = \"{chat}\"")
      key = mycursor.fetchone()[0]
    return key


#finds time when messages last updated from server
def last_received(mycon, sercon, table): 
    try:
        with mycon.cursor() as mycursor:
          mycursor.execute(f"select date from {table} order by date asc;")
          most_recent = mycursor.fetchall()[-1][0]
        return most_recent
    except:
        return "1999-01-01 00:00:00"

    #fetches information from my_id table
def get_my_info(argument, mycon, sercon): 
    try:
        #print("Fetching", argument)
        with mycon.cursor() as mycursor:
          mycursor.execute(f"select {argument} from my_id;")
          data = mycursor.fetchone()[0]
        return data
    except:
        return 0

#returns my_id
def get_my_id(mycon, sercon): 
    return get_my_info("my_id", mycon, sercon)


#creates a new chat by generating symmetric key and sending the encrypted symmetric key to all members
def create_chat(name, members, mycon, sercon, key_size=39): 
    #print("Creating new chat...")
    sym_key = sym_key_generate(key_size)
    existing_chats = display_chats(mycon, sercon)
    if name in existing_chats:
        with mycon.cursor() as mycursor:
            mycursor.execute(f"delete from chats where chat_name = \"{name}\"")
    for uid in members:
        add_member_to_chat(name, uid, sym_key, mycon, sercon)
        with mycon.cursor() as mycursor:
          mycursor.execute(f"insert into chats values (\"{name}\", \"{uid}\", \"{sym_key}\", \"{get_cur_time()}\");")
    mycon.commit()
    #print("Chat created successfully!")

#shares chat symmetric key with specified member
def add_member_to_chat(chat_name, uid, sym_key, mycon, sercon): 
    key = pack_cipher(sym_key)
    pubkey = get_public_key(uid, mycon, sercon).split()
    cipher_text = encrypt_exchange_message(key, uid, pubkey)
    with sercon.cursor() as sercursor:
        sercursor.execute(f"insert into chat_log values (\"{chat_name}\", \"{get_my_id(mycon, sercon)}\", \"{uid}\", \"{cipher_text}\", \"{get_cur_time()}\");")
    sercon.commit()

#joins all chats user has been invited to
def join_chats(mycon, sercon): 
    new_chats = []
    most_recent_chat = last_received(mycon, sercon, "chats")
    with sercon.cursor() as sercursor:
        sercursor.execute(f"select * from chat_log where (add_req = \"{get_my_id(mycon, sercon)}\") and date > \"{most_recent_chat}\";")
        chats = sercursor.fetchall()
    existing_chat_names = display_chats(mycon, sercon)
    #print("Most recent chat:", most_recent_chat)
    #print("New chats are")
    for x in chats:
        #print(x[0], "is the current chat")
        if x[0] not in existing_chat_names:
            #print(f"Joining {x[0]}")
            new_chats.append(x[0])
            private_key_unpacked = get_my_info("my_priv_key", mycon, sercon).split()
            private_key = (pack_cipher(private_key_unpacked[0]), pack_cipher(private_key_unpacked[1]))
            key = unpack_cipher(decrypt_exchange_message(x[3], private_key))
            members = get_chat_members(x[0], mycon, sercon)
            for m in members:
                with mycon.cursor() as mycursor:
                    mycursor.execute(f"insert into chats values (\"{x[0]}\", \"{m}\", \"{key}\", \"{x[4]}\");")
        else:
           with mycon.cursor() as mycursor:
               #print("delete from chats where chat_name = \"{x[0]}\"")
               mycursor.execute(f"delete from chats where chat_name = \"{x[0]}\"")
               new_chats.append(x[0])
               private_key_unpacked = get_my_info("my_priv_key", mycon, sercon).split()
               private_key = (pack_cipher(private_key_unpacked[0]), pack_cipher(private_key_unpacked[1]))
               key = unpack_cipher(decrypt_exchange_message(x[3], private_key))
               members = get_chat_members(x[0], mycon, sercon)
               for m in members:
                   with mycon.cursor() as mycursor:
                       mycursor.execute(f"insert into chats values (\"{x[0]}\", \"{m}\", \"{key}\", \"{x[4]}\");")
    mycon.commit()
    return new_chats

#returns all members of the chat
def get_chat_members(chat_name, mycon, sercon): 
    members = []
    with sercon.cursor() as sercursor:
        sercursor.execute(f"select add_req from chat_log where chat = \"{chat_name}\";")
        additions = sercursor.fetchall()
    for x in additions:
        if x[0] not in members:
            members.append(x[0])
    with sercon.cursor() as sercursor:
        sercursor.execute(f"select creator from chat_log where chat = \"{chat_name}\";")
        x = sercursor.fetchall()
    members.append(x[0][0])
    return list(set(members))

#returns all chats the user is a part of
def display_chats(mycon, sercon): 
    with mycon.cursor() as mycursor:
      mycursor.execute("select distinct chat_name from chats;")
      chat_names = mycursor.fetchall()
    chats = []
    for x in chat_names:
        chats.append(x[0])
    return chats

#gets current date and time
def get_cur_time(): 
    return datetime.datetime.now()

#gets public key of specified user
def get_public_key(uid, mycon, sercon): 
    with sercon.cursor() as sercursor:
        sercursor.execute(f"select public_key from users where user_id = \"{uid}\"")
        pubkey = sercursor.fetchall()[0][0]
    return pubkey

#creates an account (keys, user id) and uploads to server
def create_account(uid, pwd, mycon, sercon, key_size=1024): 
    with sercon.cursor() as sercursor:
        sercursor.execute(f"select user_id from users where user_id = \"{uid}\";")
        data=sercursor.fetchall()
    if len(data) == 0:
        (priv_key, public_key) = exchange_key_generate(key_size)
        with sercon.cursor() as sercursor:
            sercursor.execute(f"insert into users values (\"{uid}\", \"{pwd}\", \"{public_key}\");")
        with mycon.cursor() as mycursor:
            mycursor.execute(f"insert into my_id values (\"{uid}\", \"{pwd}\", \"{priv_key}\", \"{public_key}\");")
        sercon.commit()
        mycon.commit()
        #print("Account created!")
        return 1
    else:
        #print("Error! The username already exists...")
        return 0

def get_chat_history(chat_name, mycon, sercon):
    with mycon.cursor() as mycursor:
      mycursor.execute(f"select from_user, message, date from my_interactions where chat_name = \"{chat_name}\"")
      chat = mycursor.fetchall()
    return chat

def initiate_client(mycon): #creates a user
    #print("Creating account...")
    with mycon.cursor() as mycursor:
      mycursor.execute("create table if not exists my_interactions (chat_name varchar(30), from_user varchar(30), message text, date timestamp);")
    #print("Table interactions created")
    with mycon.cursor() as mycursor:
      mycursor.execute("create table if not exists chats (chat_name varchar(30), members varchar(30), sym_key text, date timestamp);")
    #print("Table chats created")
    with mycon.cursor() as mycursor:
      mycursor.execute("create table if not exists my_id (my_id varchar(30), password varchar(30), my_priv_key text, my_pub_key text);")
    #print("Table my_id created")
    mycon.commit()
    #print("Created account succesfully!")

def initiate_server(sercon): #initiates server
    #print("Initiating server...")
    with sercon.cursor() as sercursor:
        sercursor.execute("create table if not exists messages (chat varchar(30), from_user varchar(30), to_user varchar(30), message text, date timestamp);")
    with sercon.cursor() as sercursor:
        sercursor.execute("create table if not exists chat_log (chat varchar(30), creator varchar(30), add_req varchar(30), sym_key text, date timestamp);")
    with sercon.cursor() as sercursor:
        sercursor.execute("create table if not exists users (user_id varchar(30), password varchar(30), public_key text);")
    sercon.commit()
    
def check_if_server_ready(sercon): #checks if server is initiated
    try:
        with sercon.cursor() as sercursor:
            sercursor.execute("select * from users;")
            sercursor.fetchall()
        with sercon.cursor() as sercursor:
            sercursor.execute("select * from messages;")
            sercursor.fetchall()
    except:
        initiate_server(sercon)

def check_if_client_ready(mycon): #checks if user is initiated
    try:
        with mycon.cursor() as mycursor:
          mycursor.execute("select * from my_id;")
          mycursor.fetchall()
        with mycon.cursor() as mycursor:
          mycursor.execute("select * from my_interactions;")
          mycursor.fetchall()
        with mycon.cursor() as mycursor:
          mycursor.execute("select * from chats;")
          mycursor.fetchall()
    except:
        initiate_client(mycon)

def get_users(sercon):
    with sercon.cursor() as sercursor:
        sercursor.execute("select user_id from users")
        users = sercursor.fetchall()
    members = [x[0] for x in users]
    return members

def establish_server_connection():
    try:
        sercon=sqltor.connect(user="achyut",passwd="8celtics",host="localhost",database="server", consume_results=True)
    except:
        con = sqltor.connect(user="root", host="localhost")
        with con.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE server;")
        sercon=sqltor.connect(user="achyut",passwd="8celtics",host="localhost",database="server", consume_results=True)
        con.commit()
        con.close()
    return sercon

def establish_user_connection(user, pwd):
    mycon=sqltor.connect(user = user, passwd=pwd, host="localhost", database=user, consume_results=True)
    return mycon

#creates sql user
def sqlsignup(uid, pwd): 
    con = sqltor.connect(user="root", host="localhost")
    cursor = con.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {uid};")
    cursor.execute(f"CREATE USER IF NOT EXISTS \'{uid}\'@\'localhost\' IDENTIFIED BY \'{pwd}\';")
    cursor.execute(f"GRANT ALL PRIVILEGES ON {uid}.* TO \'{uid}\'@\'localhost\';")
    cursor.execute("FLUSH PRIVILEGES;")
    con.commit()
    con.close()



# ENCRYPTION PART #

#base64encode
def unpack_cipher(x): 
    group = bytearray()
    while x != 0:
        y = x & 0xff
        group.append(y)
        x = x >> 8
    return base64.b64encode(group[::-1]).decode()

#base64decode
def pack_cipher(message): 
    x = 0
    a = base64.b64decode(message)
    x = a[0]
    for i in range(1, len(a)):
        x = x<<8
        x = x | a[i]
    return x

#rsa key generate
def exchange_key_generate(bits=1024, confidence=10): 
    keys = crypt.generate_key(bits, confidence)
    priv_key = keys[0]
    pub_key = keys[1]
    encoded_priv_key = unpack_cipher(priv_key[0]) + " " + unpack_cipher(priv_key[1])
    encoded_pub_key = unpack_cipher(pub_key[0]) + " " + unpack_cipher(pub_key[1])
    encoded_keys = (encoded_priv_key, encoded_pub_key)
    return encoded_keys

#rsa encrypts message
def encrypt_exchange_message(message, uid, pubkey): 
    pubkey_packed = (pack_cipher(pubkey[0]), pack_cipher(pubkey[1]))
    cipher = crypt.direct_encrypt(message, pubkey_packed)
    cipher_text = unpack_cipher(cipher)
    return cipher_text

#rsa decrypts message
def decrypt_exchange_message(message, private_key): 
    #print("Decrypting message...")
    message_packed = pack_cipher(message)
    #print(private_key)
    #print(message_packed)
    decipher = crypt.direct_encrypt(message_packed, private_key)
    return decipher

#symmetric key encrypts message
def encrypt_symmetric_message(msg, key, block_size=5): 
    int_key = pack_cipher(key)
    R = crypt.encrypt_symmetric(msg, int_key, block_size)
    t = [unpack_cipher(x) for x in R]
    cipher_text = ' '.join(t)
    return cipher_text

#symmetric key decrypts message
def decrypt_symmetric_message(cipher, key, block_size=5): 
    ciphers = cipher.split()
    t = [pack_cipher(x) for x in ciphers]
    #print(t, key, block_size)
    decipher = crypt.decrypt_symmetric(t, key, block_size)
    return decipher

#symmetric key generator
def sym_key_generate(size=39): 
    #print("Generating key")
    key = crypt.generate_symmetric_key(size)
    #print(key)
    key_unpacked = unpack_cipher(key)
    return key_unpacked



