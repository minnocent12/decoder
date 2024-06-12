import random

def main():
    TRIES = 8
    DIGITS = 3
    RANGE = 10

    # Generate the secret code
    secret_code = [random.randint(0, RANGE-1) for _ in range(DIGITS)]

    tries = TRIES

    print("Welcome to the Vault Cracker Game!")
    print(f"The secret code consists of {DIGITS} digits from 0 to {RANGE-1}. You have {TRIES} tries to guess it.")

    while tries != 0:
        while True:
            user_input = input(f"\nYou have {tries} tries remaining. Enter your guess (3 digits) or 'q' to quit: ").strip()
            
            if user_input.lower() == 'q':
                print("\nYou have quit the game. The secret code was:", ''.join(map(str, secret_code)))
                return

            if user_input.isdigit() and len(user_input) == 3:
                break
            else:
                print("\n!!! You must enter exactly 3 positive integers !!! *** Try again ***")
        
        guess = [int(digit) for digit in user_input]

        correct_digits = 0
        correct_positions = 0

        for i in range(DIGITS):
            if guess[i] == secret_code[i]:
                correct_digits += 1
            elif guess[i] in secret_code:
                correct_positions += 1

        if correct_digits == DIGITS:
            print("\nCongratulations! You opened the vault! The secret code was:", ''.join(map(str, secret_code)))
            return
        else:
            print(f"Feedback: Too {'low' if int(user_input) < int(''.join(map(str, secret_code))) else 'high'}. {correct_digits} digits are correct and in the right place, {correct_positions} digits are correct but in the wrong place.")
        
        tries -= 1

    print("\nThe vault shuts down permanently due to too many incorrect attempts. You failed to open the vault!")
    print("The secret code was:", ''.join(map(str, secret_code)))

if __name__ == "__main__":
    main()