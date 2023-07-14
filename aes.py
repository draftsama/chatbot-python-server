from cryptography.fernet import Fernet
import sys


class AES:
    __key = b'dHXEojwvBzOnpqq8w7qd8klccSpczX6jfjt-p9XB8gc='

    @staticmethod
    def generate_key():
        # Generate a new AES key
        return Fernet.generate_key()

    @staticmethod
    def encrypt(text: str):

        # Create a Fernet cipher object with the provided key
        cipher = Fernet(AES.__key)
        # Encrypt the plaintext
        ciphertext = cipher.encrypt(text.encode())
        # Return the encrypted data as bytes
        return ciphertext.decode('utf-8')

    @staticmethod
    def decrypt(text: str):
        # Create a Fernet cipher object with the provided key

        cipher = Fernet(AES.__key)
        # Decrypt the ciphertext
        plaintext = cipher.decrypt(text.encode())
        # Return the decrypted data as a string
        return plaintext.decode('utf-8')


# # Example usage
# key = generate_key()
# print("Key:", key)

# key = b'dHXEojwvBzOnpqq8w7qd8klccSpczX6jfjt-p9XB8gc='
# plaintext = "Hello, world!"

# encrypted_data = encrypt(key, plaintext)
# print("Encrypted data:", encrypted_data)

# decrypted_data = decrypt(key, encrypted_data)
# print("Decrypted data:", decrypted_data)

# Example usage
# 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

if (len(sys.argv) < 3):
    print("Please input command")
    exit()

order = sys.argv[1]
text = sys.argv[2]
if (order == '-e' or order == '--encrypt'):
    byte_string = AES.encrypt(text)
    print(byte_string)
elif (order == '-d' or order == '--decrypt'):
    print(AES.decrypt(text))
