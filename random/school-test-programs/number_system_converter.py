
def binary_to_hex(binary):
    binary = binary[::-1]  # Reverse the binary string
    hexadecimal = 0
    power = 0

    for digit in binary:
        if digit == '1':
            hexadecimal += 2 ** power
        power += 1

    hex_digits = "0123456789ABCDEF"
    hexadecimal_string = ""

    while hexadecimal > 0:
        remainder = hexadecimal % 16
        hexadecimal_string = hex_digits[remainder] + hexadecimal_string
        hexadecimal //= 16

    return hexadecimal_string

def hex_to_binary(hexacdecimal_string):
    pass


def decimal_to_binary(decimal):
    binary_string = ""
    while decimal > 0:
        remainder = decimal % 2
        binary_string = str(remainder) + binary_string
        decimal //= 2
    return binary_string

def binary_to_decimal(binary):
    decimal = 0
    power = 0
    for digit in binary:
        if digit == '1':
            decimal += 2 ** power
        power += 1
    return decimal

binary_number = "101010"
hexadecimal_number = binary_to_hex(binary_number)
print(hexadecimal_number)
