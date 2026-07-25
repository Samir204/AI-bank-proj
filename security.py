import random
import string
import secrets








def generate_random_string():
    # Concatenate uppercase, lowercase letters and digits
    length = random.randint(5,8)
    characters = string.ascii_uppercase + string.digits + string.ascii_letters
    # Select 'length' random characters and join them
    return ''.join(random.choices(characters, k=length))

    
# For cryptographically secure strings (e.g., for passwords or tokens),
#  use the secrets module instead:

def generate_secure_pass():
    # length = random.randint(8,12)
    characters = string.ascii_uppercase + string.digits + string.ascii_letters
    return ''.join(secrets.choice(characters) for _ in range(12))



