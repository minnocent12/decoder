import random
import string
import time

def generate_unique_key(key_length=15):
    timestamp = str(int(time.time()))[-5:]  # Use last 5 digits of current timestamp
    random_part = ''.join(random.choices(string.ascii_letters + string.digits, k=key_length - 5))
    unique_key = timestamp + random_part
    return unique_key

# Example usage:
if __name__ == "__main__":
    unique_key = generate_unique_key()
    print("Generated unique key:", unique_key)
