#random password generator

import string,random


def random_password_generator():
    all_choices=string.ascii_letters+string.digits
    return ''.join(random.choices(all_choices,k=8))