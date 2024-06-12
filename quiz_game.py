def main():
    print("Welcome to my quiz!")

    while True:
        playing = input("Do you want to play? (Y/N): ").strip().upper()
        if playing == "Y":
            break
        elif playing == "N":
            print("Maybe next time. Goodbye!")
            return
        else:
            print("Invalid input. Please enter 'Y' for yes or 'N' for no.")

    print("Great! Let's play!")
    


if __name__ == "__main__":
    main()
