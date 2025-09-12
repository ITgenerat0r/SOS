# import base64
import hashlib
# pip install pycryptodome
from Crypto.Cipher import AES
from Crypto import Random


# RSA
from time import time
import rsa


# ECIES
# from ecies import decrypt as eciesdecrypt
# from ecies import encrypt as eciesencrypt
# from ecies.utils import generate_eth_key



BLOCK_SIZE = 16


class Security():
	def __init__(self, log=False):
		self.__logs = log
		self.__aes_key = "develop"

		self.__version = "2.0"

		# RSA
		self.__len_key = 2048
		self.__len_en = {128 : 5, 256 : 21, 512 : 53, 1024 : 117, 2048 : 245, 4096 : 4096}
		self.__len_encrypt = 245
		self.__set_encrypt_len(self.__len_key)
		self.__len_decrypt = int(self.__len_key / 8)


	# rsa
	def set_key_len(self, ln=0):
		if ln:
			self.__set_encrypt_len(ln)

	# rsa
	def __set_encrypt_len(self, ln=2048):
		if ln in self.__len_en:
			self.__len_encrypt = self.__len_en[ln]


	def enable_log(self, log=True):
		self.__logs = log


	def bytes2hexstr(self, data):
		return f"{data.hex()}"

	def hexstr2bytes(self, data):
		return b'' + bytes.fromhex(data)

	def new_iv(self):
		return self.bytes2hexstr(Random.new().read(AES.block_size))



	def __pad(self, s):
		# print(f"len(s) = {len(s)}")
		# print(f"+++ {(BLOCK_SIZE - len(s) % BLOCK_SIZE)} +++")
		# print(f"+++{chr(BLOCK_SIZE - len(s) % BLOCK_SIZE)}+++")
		# l = (BLOCK_SIZE - len(s) % BLOCK_SIZE) -1
		# return s + l * '0' + hex(l)[2:]

		return s + ((BLOCK_SIZE - len(s) % BLOCK_SIZE) * chr(BLOCK_SIZE - len(s) % BLOCK_SIZE)).encode('utf-8')


	def __unpad(self, s):
		# l = int(s[len(s) - 1:], 16) + 1
		# print(f"L: {l}")

		# return s[: -int(s[len(s) - 1:], 16)-1]

		if s:
			return s[: -ord(s[len(s) - 1 :])]
		else:
			return b''


	def encrypt(self, plain_text, key, iv):
		if self.__logs:
			print("ENCRYPT")
			print("----------------------------")
			print(f"plain_text({len(plain_text)}): '{plain_text}'")
			print("----------------------------")
			print(f"key({len(key)}): {key}")
			print(f"iv({len(iv)}): {iv}")
		# private_key = hashlib.sha256(key.encode("utf-8")).digest()
		# plain_text = self.__pad(plain_text)
		if self.__logs:
			print("----------------------------")
			print(f"padded plain_text({len(plain_text)}): '{plain_text}'")
			print("----------------------------")
		cipher = AES.new(self.hexstr2bytes(key), AES.MODE_CBC, self.hexstr2bytes(iv))
		p_text = self.__pad(plain_text.encode('utf-8'))

		print(f"p_text({len(p_text)})")
		enc_data = cipher.encrypt(p_text)
		return self.bytes2hexstr(enc_data)


	def decrypt(self, data, key, iv):
		if self.__logs:
			print("DECRYPT")
			print(f"data: {data}")
			print(f"key: {key}")
			print(f"iv: {iv}")
		cipher_text = self.hexstr2bytes(data)
		# private_key = hashlib.sha256(key.encode("utf-8")).digest()
		# private_key = self.hexstr2bytes(key)
		cipher = AES.new(self.hexstr2bytes(key), AES.MODE_CBC, self.hexstr2bytes(iv))
		return bytes.decode(self.__unpad(cipher.decrypt(cipher_text)))


	def sha256(self, data):
		return self.bytes2hexstr(hashlib.sha256(data.encode("utf-8")).digest())




	# ===== RSA =========================================


	def generate_rsa_keys(self, ln=2048):
		start_time = time()
		if ln:
			self.__len_key = ln
		if self.__logs:
			print(f"Generate keys({self.__len_key})...")
		self.__len_decrypt = int(self.__len_key / 8)
		(pub, priv) = rsa.newkeys(self.__len_key)
		self.__set_encrypt_len(self.__len_key)
		end_time = time()
		delta_time = end_time - start_time
		if self.__logs:
			print(f"Keys generated for {delta_time}s.")

		pb = rsa.PublicKey.save_pkcs1(pub, format='DER')
		pv = rsa.PrivateKey.save_pkcs1(priv, format='DER')
			# return str(pk, 'utf-8')[self.__len_begin:-self.__len_end]
			# return pk.hex()[self.__len_begin*2:-self.__len_end*2]
		return self.bytes2hexstr(pv), self.bytes2hexstr(pb)

	def rsa_encrypt(self, message, key):
		# шифруем
		try:
			pb = self.hexstr2bytes(key)
			pub_key = rsa.PublicKey.load_pkcs1(pb, format='DER')
			crypto = ""
			message = "" + str(message)
			message = message.encode('utf-8')
			if len(message) > self.__len_encrypt:
				# print("before while mark")
				while len(message)>0:
					stack = message[:self.__len_encrypt]
					message = message[self.__len_encrypt:]
					if self.__logs:
						print(len(stack))
					sc = rsa.encrypt(stack, pub_key)
					# print(red_text(f"{len(sc)} : {sc}"))
					if self.__logs:
						print()
						print(len(sc))
						print(sc)
						print()
					crypto += sc.hex()
					# print("len(crypto):", len(crypto))
			else:
				# print("else mark")
				res = rsa.encrypt(message, pub_key)
				crypto = res.hex()
			# print("\r\nEncrypted:", crypto)
			return crypto
		except Exception as e:
			return f"Encrypt_err: {e}"

	def rsa_decrypt(self, cryptos, key):
		#расшифровываем
		try:
			pv = self.hexstr2bytes(key)
			priv_key = rsa.PrivateKey.load_pkcs1(pv, format='DER')
			# print("decrypt len:", len(cryptos))
			message = b''
			# crypto = b'' + str(cryptos)
			# crypto = cryptos.encode('utf-8')
			# crypto = self.check(cryptos)
			crypto = bytes.fromhex(cryptos)
			# print("before if mark", len(crypto))
			if len(crypto)>self.__len_decrypt:
				# print("before while mark")
				while len(crypto)>0:
					stack = crypto[:self.__len_decrypt]
					# print(yellow_text(f"{len(stack)} : {stack}"))
					if self.__logs:
						print()
						print(len(stack))
						print(stack)
						print()
					crypto = crypto[self.__len_decrypt:]
					# print("e mark")
					message += rsa.decrypt(stack, priv_key)
			else:
				# print("else mark")
				message = rsa.decrypt(crypto, priv_key)
			# print("\r\nDecrypted:", crypto)
			return message.decode('utf-8')
		except Exception as ex:
			return f"Decrypt_err: {ex}"


	# ===================================================







	# ===== ECIES =======================================
	# def generate_ecies_key(self):
	# 	# priv_key = ecies.utils.generate_eth_key()
	# 	priv_key = generate_eth_key()
	# 	priv_key_hex = priv_key.to_hex()
	# 	pub_key_hex = priv_key.public_key.to_hex()
	# 	return priv_key_hex, pub_key_hex

	# def ecies_encrypt(self, key, data):
	# 	return self.bytes2hexstr(eciesencrypt(key, data.encode('utf-8')))


	# def ecies_decrypt(self, key, data):
	# 	return eciesdecrypt(key, self.hexstr2bytes(data)).decode('utf-8')

	# ===================================================



# ------ TEST ---------------------------------------


# RSA

# cl = Security(True)
# key_len = 2048
# priv_key, pub_key = cl.generate_rsa_keys(key_len)
# print(f"Private key({len(priv_key)}): ", priv_key)
# print(f"Public key({len(pub_key)}): ", pub_key)

# data = "testing rsa"
# print("init data: ", data)

# #
# en_data = cl.rsa_encrypt(data, pub_key)
# print("Encrypted data:", en_data)

# #
# de_data = cl.rsa_decrypt(en_data, priv_key)
# print("Decrypted data:", de_data)



# ------






# cl = Security()
# print(cl.sha256('test'))

# from Crypto.PublicKey import ECC

# mykey = ECC.generate(curve='p521')
# print(mykey)
# print()



# # private_data = mykey.export_key(format='DER', passphrase="pwd", protection='PBKDF2WithHMAC-SHA512AndAES256-CBC', prot_params={'iteration_count':131072})
# private_data = mykey.export_key(format='DER')
# print(cl.bytes2hexstr(private_data))
# print()



# public_data = mykey.public_key().export_key(format='DER')
# print(cl.bytes2hexstr(public_data))





# ECC

# cl = Security()
# privKeyHex, pubKeyHex = cl.generate_ecies_key()


# print("Encryption public key:", pubKeyHex)
# print("Decryption private key:", privKeyHex)
# print()

# plaintext = 'Some plaintext for encryption'
# print("Plaintext:", plaintext)
# print()

# encrypted = cl.ecies_encrypt(pubKeyHex, plaintext)
# # print("Encrypted:", binascii.hexlify(encrypted))
# print("Encrypted:", encrypted)
# print()

# decrypted = cl.ecies_decrypt(privKeyHex, encrypted)
# print("Decrypted:", decrypted)








# AES

# cp = Security(True)
# # message = "asdfasdf-0123456789abcef0123456789abcdef"
# message = "DATA: default: 1235215ffasdfasdfп"
# # message = input("->")
# key = cp.sha256("develop")
# # iv = "c33bfeae1263c98633bc9e66c6ab8746"
# iv = cp.new_iv()

# print(f"Init text({len(message)}): ", message)
# encrypted_msg = cp.encrypt(message, key, iv)
# print(f"Encrypted Message({len(encrypted_msg)}):", encrypted_msg)
# decrypted_msg = cp.decrypt(encrypted_msg, key, iv)
# print("Decrypted Message:", decrypted_msg)

# ---------------------------------------------------