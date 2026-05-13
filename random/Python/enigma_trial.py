from enigma.machine import EnigmaMachine
from itertools import *

machine = EnigmaMachine.from_key_sheet(
    rotors='V IV II',
    ring_settings='4 1 25',
    reflector='B',
    plugboard_settings='WJ VD PO MQ FX SR NE LG UC BK'
)
machine.set_display('KAO')

plaintext = 'SIXXAMXREPORTXGOODXTOXFLYXHEILXHITLER'
ciphertext = machine.process_text(plaintext)
crib = 'SIXXAM'

rotor_options = ["I","II","III","IV","V"]

def find_enigma_settings(cribtext, ciphertext):
    for rotor_selection in permutations(rotor_options, 3):
        for ring_settings in product(range(1, 27), repeat=3):
            for plugboard_combination in product(range(26), repeat=20):
                plugboard = ' '.join([chr(p + 65) + chr((p + 1) % 26 + 65) for p in plugboard_combination[::2]])
                machine = EnigmaMachine.from_key_sheet(
                    rotors=' '.join(rotor_selection),
                    reflector='B',
                    ring_settings=' '.join(map(str, ring_settings)),
                    plugboard_settings=plugboard
                )
                decrypted_text = machine.decrypt(ciphertext)
                if decrypted_text[:len(cribtext)] == cribtext:
                    return rotor_selection, ring_settings, plugboard
    return None  # Return None if no configuration matches

settings = find_enigma_settings(crib, ciphertext)
if settings:
    print("Found settings:", settings)
else:
    print("No settings found")