from sage.all import * #for matrix operations
import random #generating random numbers
from math import gcd

# This function generates a symmetric key of a given key size, which is essentially a binary square matrix that is invertible.
def generate_symmetric_key(key_size, DEBUG=False): 
    n = key_size #dimension (size) of square matrix
    A = random_matrix(GF(2), n, n) #generate a random nxn matrix over the field Z/2Z (i.e. the set {0, 1}). In other words, generate a random binary matrix
    while True:
        if A.det() != 0: #check if invertible
          break
        A = random_matrix(GF(2), n, n)
    return matrix_to_int(A, DEBUG)

# converts a symmetric key matrix generated in <generate_symmetric_key> to an integer by reading the matrix as a binary string. For example the matrix (1 0; 0 1) will be converted to (1001)_2 = 9
def matrix_to_int(M, DEBUG=false): 
    intstr = ""
    for x in M[0:]:
        for y in x[0:]:
            intstr = intstr+str(y)
    return int(intstr, base=2)

# converts an integer into a square matrix of a given dimension. For example, if the input is 9, 2, the output will be the matrix (1 0; 0 1)
def int_to_matrix(m, size): 
    A = zero_matrix(GF(2), size, size)
    intstr = bin(m)[2:]
    while len(intstr) % size != 0:
        intstr = "0"+intstr
    col_size = len(intstr)/size
    for i in range(size):
        for j in range(size):
            A[i, j] = int(intstr[int(col_size*i + j)])
    return A


# takes in the message (string), symmetric key (int) and block_size (int) and returns the encrypted values as a list
def encrypt_symmetric(message, key, block_size, DEBUG=False): 
  M = pack(message, block_size, DEBUG) #split <message> into blocks (integers) of size <block_size> bits each
  length = len(M)
  R = []
  for i in range(length): #encrypting each block seperately
    x = M[i]
    bin_str = bin(x)[2:]
    while len(bin_str) < 8*block_size - 1: #convert block into binary string
      bin_str = "0"+bin_str
    vect = vector(GF(2), [int(k) for k in bin_str]) #convert binary string into binary vector
    cipher_text = ""
    for y in int_to_matrix(key, block_size*8-1)*vect: #multiply the matrix key with the vector and convert resultant vector into a binary string
        digit = str(y)
        cipher_text = cipher_text + digit
    R.append(int(cipher_text, base=2)) #convert binary string into an integer
  return R #return list of encrypted integers


# takes in a list of integers R, block_size and returns a decrypted message (string)
def decrypt_symmetric(R, key, block_size, DEBUG=False): 
    M = []
    keyinv = (int_to_matrix(key, block_size*8-1)).inverse() #find inverse of symmetric key
    for x in R:
       #convert each integer into a binary string
       bin_str = bin(x)[2:]
       while len(bin_str) < 8*block_size - 1:
           bin_str = "0"+bin_str
       
       vect = vector(GF(2), [mod(int(k), 2) for k in bin_str]) #convert binary string into binary vector
       decipher = "" #decrypted text variable initialized
       for y in keyinv*vect: #multiply the inverse of the key (a matrix) with the binary vector to get back the original binary vector of the message and convert it back to an integer
           digit = str(y)
           decipher = decipher+digit

       M.append(int(decipher, base=2))
    
    message = unpack(M, block_size, DEBUG) #converting list of decrypted integers into string
    return message

#-----------------RSA--------------------------#

#encrypt message and return a list of integers
def encrypt(message, public_key, block_size, DEBUG=False): 
  M = pack(message, block_size, DEBUG)
  len_M = len(M)
  R = [0] * len_M
  for i in range(len_M):
      R[i] = direct_encrypt(M[i], public_key)
  return R

#perform RSA encrytion on an integer
def direct_encrypt(msg_int, public_key, DEBUG=False): 
   return pow(msg_int, public_key[0], public_key[1])

#decrypt a list of integers using RSA to get back a message (string)
def decrypt(R, private_key, block_size, DEBUG=False): 
 M = []
 for i in R:
     M.append(direct_decrypt(i, private_key))
 
 message = unpack(M, block_size, DEBUG)
 return message

#decrypt integer using RSA
def direct_decrypt(cipher_int, private_key, DEBUG=false): 
    return pow(cipher_int, private_key[0], private_key[1])


#generate RSA key pairs
def generate_key(bits, confidence, DEBUG=false): 
  p = generate_primes(bits+4,confidence, DEBUG)
  q = generate_primes(bits,confidence, DEBUG)
  print(f"p = {p}\nq = {q}")
  e = generate_e(p, q, DEBUG)
  ϕ = (p-1)*(q-1)
  ret = bezout(ϕ, e, DEBUG)
  d = ret[1] % ((p-1)*(q-1))
  d = d if d>=0 else d+(p-1)*(q-1)
  n = p*q
  return ((e,n), (d,n))


# takes a string, splits it into blocks of block size <block_size> characters each. Converts each block into an integer and returns a list of integers
def pack(message, block_size, DEBUG=False): 
   if len(message) % block_size != 0: #ensure message length is divisible by block size
       spaces = ' ' * (block_size - len(message) % block_size)
       message += spaces

   iterations = len(message) // block_size #number of blocks required
   ret = [0] * iterations
   for i in range(iterations):
       M = 0
       group = message[(i*block_size):((i+1)*block_size)] #groups <block_size> characters of <message> together
       for x in group:
           M = (M << 8) | ord(x) #convert each character to ASCII and append to the end of the existing integer M by left shifting
       ret[i] = M
       if DEBUG:
           print(f"M = {M}")

   if DEBUG:
       print("Packing...")
       print("Packed")
   return ret


# takes a list of integers, converts each integer back to a string and returns the concatenation of all such strings
def unpack(M, block_size, DEBUG=False): 
   message = ""
   for x in M:
       group = ""
       #decode a single block
       for i in range(block_size):
           y = x & 0xff #last 8 bits of integer x
           group = chr(y) + group #convert y to a character and append to string <group>
           x = x >> 8 #"remove" last 8 bits of x (right shift)
       message += group
   return message

# generates e of public key
def generate_e(p, q, DEBUG=False):
 y = random.randint(0, (p-1)*(q-1))
 while gcd(y, (p-1)*(q-1)) != 1:
   y += 1
 return y

# given a and b, finds a pair x,y such that ax + by = gcd(a, b). Implementation of gcd algorithm
def bezout(a, b, DEBUG=False):
 x = [[a, 1, 0], [b, 0, 1]]
 i = 0
 while x[i+1][0] != 0:
   rem = x[i][0] % x[i+1][0]
   q = x[i][0] // x[i+1][0]
   n1 = x[i][1] - q * x[i+1][1]
   n2 = x[i][2] - q * x[i+1][2]
   x.append([rem, n1, n2])
   i += 1
 if DEBUG:
   print(x)
 return x[i][1], x[i][2]

# fast modular arithmetic. This function is still too slow to use, as it is written in python.
def fmod(a, b, n, DEBUG=False):
 t = b
 power = 0
 res = 1
 while t != 0:
  t = t >> 1
  power += 1

 mods = [0] * power
 power -= 1
 t = b
 mods[0] = a % n
 for i in range(power):
  mods[i+1] = (mods[i]**2) % n

 for i in range(power+1):
  res = res * mods[i] if t & 1 == 1 else res
  t = t >> 1

 return res % n

# generate a random prime
def generate_primes(bits, confidence, DEBUG=False):
 num = generate_random(bits)
 found = False
 while not found:
   num += 2
   found = prime_check_low(num, DEBUG) and prime_check_fermat(num, confidence, DEBUG)
 return num

#generate random odd integer
def generate_random(bits):
 range_start = 2**(bits-1)
 range_end = 2**bits
 num = random.randint(range_start, range_end)
 num = num + 1 if num % 2 == 0 else num
 return num

#fermat primality testing
def prime_check_fermat(num, confidence, DEBUG=False): 
 i = 1
 prime = True
 while i <= confidence and prime:
  a = random.randint(2, num-1)
  rem = pow(a, num-1, num)
  prime = True if rem == 1 else False
  i += 1
 return prime

#primality test for small primes
def prime_check_low(num, DEBUG=False): 
 prime = True
 low_primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101, 103, 107, 109, 113, 127, 131, 137, 139, 149, 151, 157, 163, 167, 173, 179, 181, 191, 193, 197, 199, 211, 223, 227, 229, 233, 239, 241, 251, 257, 263, 269, 271, 277, 281, 283, 293, 307, 311, 313, 317, 331, 337, 347, 349]
 for x in low_primes:
   if num % x == 0:
     prime = False
     break
 return prime


