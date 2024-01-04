Black Rhythm is a basic messenger app that provides end-to-end encryption. The app uses asymmetric RSA encryption to exchange 
symmetric keys to establish a secure channel. This repository contains the source code and instructions for the app.

## Implementation
The app is implemented using python with a central MySQL database. The central database stores encrypted messages and metadata of interactions between 
users. Since only the encrypted cipher texts are stored, messages cannot be read by anyone, even if they have access to the server. RSA private keys
never leave the clients and symmetric keys are only transmitted to other clients on the chat over a secure RSA channel, and are never available at
the server.

### Encryption
For encryption, a combination of RSA and symmetric key encryption is used. On the first interaction between two users, 
a symmetric key is exchanged on a secure asymmetric RSA channel between them. Once the symmetric key between two users is set up, 
future messages are encrypted using the symmetric key. 

The message is first broken up into blocks, each of which is converted to a binary string (seen as a vector). The symmetric key is 
an invertible square matrix with the same number of rows as the number of rows in the vector. 

For example, consider two users who share a symmetric key that is equivalent to the matrix represented by
$$
\begin{pmatrix}
1 & 0 & 0 \\
1 & 1 & 0 \\
0 & 1 & 1
\end{pmatrix}
$$
If one user wants to send the message represented by the vector $(0, 1, 1)$, they simply multiply the vector with the matrix and that is the encrypted vector. To decrypt, simply multiply by the inverse.

### Group chats
The app also  allows you to create chats with more than one user. Each group chat has its own symmetric key 
that is shared with all its members. When a member is added to or removed from a group chat, the symmetric key is regenerated
and pushed to all users in the chat.

In fact, any chat is internally processed as a group chat. A DM is simply a group chat with not more than two members.

## Running the Code
### Dependencies
The following are required to be preinstalled, apart from python:
- Sagemath
- MySQL
### Instructions
- First, download the program and the dependencies on three computers. One will act as the server and the other two as users.
- Ensure that the SQL config file of the server is set up to allow other computers to connect. 
- Obtain the IP address of the server computer.
- Install the program on the other two computers as well and point the IP address in file `messenger.py` to the IP address of the server. Moreover, ensure that the program can connect to your local SQL server by modifying the password if required.
- Start chatting by running `gui.py`

