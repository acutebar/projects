import PySimpleGUI as sg
import time
import threading
import messenger
import mysql.connector as sqltor
import sys

sys.stderr = open('errorlog.txt', 'w')
sg.theme('DarkPurple4')

class Text:
    BOLD = '\033[1m'
    END = '\033[0m'
    UNDERLINE = '\033[4m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'

def asyncly_display_chat(chat, window):
    global run_chat_thread
    local_interactions = interactions.copy()
    #print("BEFORE LOOP")
    while True:
        time.sleep(2)
        #print("Interactions: ", interactions[chat])
        #print("Local interactions: ", local_interactions[chat])
        #print(local_interactions==interactions)
        try:
            a = local_interactions[chat]
        except:
            local_interactions[chat] = [{'sender':'', message:'', timestamp:''}]
        if local_interactions[chat] != interactions[chat]:
            message = str(interactions[chat][-1]['message'])
            timestamp =  str(interactions[chat][-1]['timestamp'])
            sender = str(interactions[chat][-1]['sender'])
            #if sender != local_interactions[chat][-1]['sender']:
            window['-MESSAGES-'].update("\n" + sender + "\t" + f"({timestamp})" + "\n", font_for_value=('Courier', 12, 'bold'), append=True, autoscroll=True)
            window['-MESSAGES-'].update("| " + message + "\n", append=True, autoscroll=True)
            #else:
             #   window['-MESSAGES-'].update("| " + message + "\n", append=True, autoscroll=True)
            local_interactions = interactions.copy()

def asyncly_list_chats(window, mycon, sercon):
    while True:
        time.sleep(2)
        #print("UPDATING CHAT LIST")
        #print("CHATS ARE ", chats)
        window['-CHATS-'].update(chats)

def sign_in_window():
    try:
       fp = open("signindata.txt", "r")
       credentials = fp.read().split(',')
       user=credentials[0]
       pwd=credentials[1]
       sqltor.connect(user=user, passwd=pwd, host="localhost", database=user)
       return (user, pwd)
    except:
        layout = [   
                     [sg.Text(key='-OUTPUT-')],
                     [sg.Text('Display name: '), sg.InputText(key='-DNAME-')],
                     [sg.Text('Password: '), sg.InputText(key='-PWD-')],
                     [sg.Checkbox("Stay signed in", key='-STAY-')],
                     [sg.Submit(bind_return_key=True), sg.Cancel()]
                 ]
        window = sg.Window('Sign in', layout)
        while True:
            event, values = window.read()
            user = values['-DNAME-']
            pwd = values['-PWD-']
            if event == 'Submit':
                try:
                    sqltor.connect(user = user, passwd=pwd, host="localhost", database=user)
                    if values['-STAY-']:
                        fp = open("signindata.txt", "w")
                        fp.write(f"{user},{pwd}")
                        fp.close()
                    break
                except:
                    window['-OUTPUT-'].update('Incorrect password or username!')
                    window['-DNAME-'].update('')
                    window['-PWD-'].update('')
            else:
                window.close()
                sys.exit(0)
        window.close()
        return (values['-DNAME-'], values['-PWD-'])

def sign_up_window():
    layout = [
                 [sg.Text('Display name: '), sg.InputText(key='-DNAME-')],
                 [sg.Text('Password: '), sg.InputText(key='-PWD-')],
                 [sg.Checkbox("Stay signed in", key='-STAY-')],
                 [sg.Submit(bind_return_key=True), sg.Cancel()]
             ]
    event, values = sg.Window('Sign up', layout).read(close=True)
    user = values['-DNAME-']
    pwd = values['-PWD-']
    if event == 'Cancel':
        sys.exit(0)
    if values['-STAY-']:
        fp = open("signindata.txt", "w")
        fp.write(f"{user},{pwd}")
        fp.close()
    #print(values['-PWD-'])
    return (values['-DNAME-'], values['-PWD-'])

def receive_messages():
    global interactions
    global user
    global pwd
    while True:
        time.sleep(2)
        sercon = messenger.establish_server_connection()
        messenger.check_if_server_ready(sercon)
        mycon = messenger.establish_user_connection(user, pwd)
        messenger.check_if_client_ready(mycon)
        #print("Performing periodic update from server...")
        messenger.update_from_server(mycon, sercon)
        for chat_name in messenger.display_chats(mycon, sercon):
            chat_log = []
            chat = messenger.get_chat_history(chat_name, mycon, sercon)
            for x in chat:
                #print(f"{x[0]}:\t{x[1]}\t({str(x[2])})")
                chat_log.append({'sender': x[0], 'message': x[1], 'timestamp': x[2], 'isevent': False})
            #print("AVAILABLE CHATS\n", chat_name)
            interactions[chat_name] = chat_log
        sercon.close()
        mycon.close()

def accept_chat_invites():
    global user
    global pwd
    global chats
    while True:
        time.sleep(2)
        sercon = messenger.establish_server_connection()
        messenger.check_if_server_ready(sercon)
        mycon = messenger.establish_user_connection(user, pwd)
        messenger.check_if_client_ready(mycon)
        chats = messenger.display_chats(mycon, sercon)
        #print("Performing periodic update of chats...")
        new_chats = messenger.join_chats(mycon, sercon)
        #print("New chats = ", chats)
        sercon.close()
        mycon.close()

def chats_window(chats, mycon, sercon):
  layout = [
               [sg.Button('+ New'), sg.Button('Exit')],
               [sg.Listbox(chats, key='-CHATS-', enable_events=True, expand_y=True, size=(100, 50))]
           ]
  window = sg.Window(f"Chats -- {user}@Black Rhythm", layout)
  t3 = threading.Thread(target=asyncly_list_chats, args=(window, mycon, sercon, ))
  t3.start()
  while True:
      event, values = window.read(close=False)
      if event == 'Exit' or event == sg.WIN_CLOSED:
          window.close()
          sys.exit(0)
      elif event == '+ New':
          sg.Window("Patience is the key to success", [[sg.Text("Feature is still in progres...")], [sg.Button("I will be patient. I will not compain. If I am not patient, I will reform myself to be patient and wait.")]]).read(close=True)
          window.close()
          chats = makechat(mycon, sercon)
          return chats_window(chats, mycon, sercon)
      else:
          chat=values['-CHATS-'][0]
          window.close()
          current_chat_window(chats, chat, mycon, sercon)
          window.close()
          return chat
  window.close()

def current_chat_window(chats, chat, mycon, sercon):
    global run_chat_thread
    run_chat_thread = True
    mycon = messenger.establish_user_connection(user, pwd)
    messenger.check_if_client_ready(mycon)
    layout = [
                 [sg.Button('Add'), sg.Button('View members')],
                 [sg.MLine(key='-MESSAGES-', size=(100, 50))],
                 [sg.InputText(key='-IN-'), sg.Button('Send', bind_return_key=True), sg.Button('Back to my chats')]
             ]
    window = sg.Window(f"{chat} -- {user}@Black Rhythm", layout, finalize=True)
    chat_log = interactions[chat]
    for x in chat_log:
        window['-MESSAGES-'].update("\n" + str(x['sender']) + "\t" + f"({str(x['timestamp'])})" + "\n", font_for_value=('Courier', 12, 'bold'), append=True, autoscroll=True)
        window['-MESSAGES-'].update("| " + str(x['message']) + "\n", append=True, autoscroll=True)
    t3 = threading.Thread(target=asyncly_display_chat, args=(chat, window, ))
    t3.start()
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            sys.exit(0)
        elif event == 'Send':
            message = values['-IN-']
            messenger.send(chat, message, mycon, sercon)
            #window['-MESSAGES-'].update(message+'\n', append=True)
            window['-IN-'].update('')
        elif event == 'Add':
            window.close()
            add_chat_window(chats, chat, mycon, sercon)
        elif event == 'View members':
            window.close()
            chat_members_window(chats, chat, mycon, sercon)
        elif event == 'Back to my chats':
            window.close()
            chats_window(chats, mycon, sercon)
            run_chat_thread = False
            t3.join()
    t3.join()
    window.close()
    mycon.close()

def makechat(mycon, sercon):
    users = messenger.get_users(sercon)
    layout = [
                 [sg.Text('Name your chat'), sg.InputText(key='-NAME-')],
                 [sg.Text('Searchbar: '), sg.InputText(key='-IN-')],
                 [sg.Text('Members added: '), sg.InputText(key='-MEMSTR-')],
                 [sg.Button('CLEAR'), sg.Button('SEARCH')],
                 [sg.Listbox(users, size=(100, 50), key='-MEMS-', enable_events=True)],
                 [sg.Button('Create chat'), sg.Button('Back to my chats'), sg.Button('Exit')]
             ]
    window = sg.Window(f"New chat -- {user}@Black Rhythm", layout)
    members_till_now = []
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            sys.exit(0)
        elif event == 'Back to my chats':
            window.close()
            chats_window(chats, mycon, sercon)
        elif event == 'SEARCH':
            username = values['-IN-']
            mems_to_display = []
            for x in users:
                #print("Searching users")
                if username in x:
                    #print(username)
                    mems_to_display.append(x)
            window['-MEMS-'].update(mems_to_display)
        elif event == 'Create chat':
            members = values['-MEMSTR-'].split(',')
            members.append(messenger.get_my_id(mycon, sercon))
            members = list(set(members))
            #print(f"Creating chat {values['-NAME-']} with members {members}")
            messenger.create_chat(values['-NAME-'], members, mycon, sercon)
            window.close()
            return messenger.display_chats(mycon, sercon)
        elif event == 'CLEAR':
            members_till_now = []
            window['-MEMSTR-'].update('')
        else:
            #print("HIII")
            members_till_now.append(values['-MEMS-'][0])
            members_till_now = list(set(members_till_now))
            window['-MEMSTR-'].update(','.join(members_till_now))
    window.close()

def add_chat_window(chats, chat, mycon, sercon):
    users = messenger.get_users(sercon)
    layout = [
                 [sg.Text('Searchbar: '), sg.InputText(key='-IN-')],
                 [sg.Text('Members added: '), sg.InputText(key='-MEMSTR-')],
                 [sg.Button('CLEAR'), sg.Button('SEARCH')],
                 [sg.Listbox(users, size=(100, 50), key='-MEMS-', enable_events=True)],
                 [sg.Button('Add'), sg.Button('Back to chat'), sg.Button('Exit')]
             ]
    window = sg.Window(f"Add to {chat} -- {user}@Black Rhythm", layout)
    current_members = messenger.get_chat_members(chat, mycon, sercon)
    members_till_now = []
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            sys.exit(0)
        elif event == 'Back to chat':
            window.close()
            current_chat_window(chats, chat, mycon, sercon)
        elif event == 'SEARCH':
            username = values['-IN-']
            mems_to_display = []
            for x in users:
                #print("Searching users")
                if username in x:
                    #print(username)
                    mems_to_display.append(x)
            window['-MEMS-'].update(mems_to_display)
        elif event == 'Add':
            members = values['-MEMSTR-'].split(',')
            #print(f"Creating chat {values['-NAME-']} with members {members}")
            current_members.extend(members)
            messenger.create_chat(chat, list(set(current_members)), mycon, sercon)
            window.close()
            for x in members:
                interactions[chat].append({'sender': '', 'message': f"{user} added {x}", 'timestamp': messenger.get_cur_time(), 'isevent': True})
                interactions[chat].append({'sender': '', 'message': f"{user} added {x}", 'timestamp': '', 'isevent': True})
            current_chat_window(chats, chat, mycon, sercon)
        elif event == 'CLEAR':
            members_till_now = []
            window['-MEMSTR-'].update('')
        else:
            #print("HIII")
            members_till_now.append(values['-MEMS-'][0])
            members_till_now = list(set(members_till_now))
            window['-MEMSTR-'].update(','.join(members_till_now))
    window.close()

def chat_members_window(chats, chat, mycon, sercon):
    members = messenger.get_chat_members(chat, mycon, sercon)
    layout = [
                 [sg.Button('Add'), sg.Button('Back')],
                 [sg.Listbox(members, key='-MEMBERS-', size=(100, 50), enable_events=True)],
             ]
    window = sg.Window(f"{chat} -- {user}@Black Rhythm", layout)
    event, values = window.read(close=True)
    if event == sg.WIN_CLOSED:
        sys.exit(0)
    elif event == 'Back':
        current_chat_window(chats, chat, mycon, sercon)
    else:
        DMwith = values['-MEMBERS-'][0]
        myid = messenger.get_my_id(mycon, sercon)
        alpha = [DMwith, myid]
        alpha.sort()
        DMname = "DM" + alpha[0] + alpha[1]
        if DMname in messenger.display_chats(mycon, sercon):
            current_chat_window(chats, DMname, mycon, sercon)
        else:
            messenger.create_chat(DMname, alpha, mycon, sercon)
            current_chat_window(chats, DMname, mycon, sercon)

def username_window(mycon, sercon):
    layout = [[sg.Text(key='-UP-')], [sg.Text('Enter username'), sg.InputText(key='-IN-'), sg.Button('Submit', bind_return_key=True)]]
    window = sg.Window('Create username', layout)
    while True:
        event, values = window.read()
        if event == 'Submit':
            ret = messenger.create_account(values['-IN-'], pwd, mycon, sercon)
            if ret == 1:
                break
            else:
                window['-UP-'].update('This username already exists')
    window.close()



sercon = messenger.establish_server_connection()
messenger.check_if_server_ready(sercon)

layout = [[sg.Button('Sign in'), sg.Button('Sign up')]]
event, values = sg.Window('Black Rhythm', layout).read(close=True)
if event == "Sign up":
    (user, pwd) = sign_up_window()
    messenger.sqlsignup(user, pwd)
    mycon = messenger.establish_user_connection(user, pwd)
    messenger.check_if_client_ready(mycon)
    username_window(mycon, sercon)
    mycon.close()
elif event == "Sign in":
    (user, pwd) = sign_in_window()

##print("Connection established")

sercon.close()

interactions = {}
chats = []

t1 = threading.Thread(target=accept_chat_invites, daemon=True)
t1.start()
t2 = threading.Thread(target=receive_messages, daemon=True)
t2.start()

#print("Password is:", pwd)

sercon = messenger.establish_server_connection()
messenger.check_if_server_ready(sercon)
mycon = messenger.establish_user_connection(user, pwd)
messenger.check_if_client_ready(mycon)

run_chat_thread = True

chat = chats_window(chats, mycon, sercon)

sercon.close()
mycon.close()
