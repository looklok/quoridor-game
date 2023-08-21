def get_boolean_input(prompt):
    while True:
        user_input = input(prompt).strip().lower()
        if user_input in ("yes", "y", "true", "t", "1"):
            return True
        elif user_input in ("no", "n", "false", "f", "0"):
            return False
        else:
            print("Invalid input. Please enter 'yes' or 'no'.")

def get_numOfMCTSSimulations(prompt):
    while True:
        try:
            parsed_int = int(input(prompt))
            return parsed_int
        except ValueError:
            print("Wrong input !!")
            print("please enter an integer")
        


def flush_stdin():
    try:
        # This will read any existing input in the buffer and discard it
        sys.stdin.read()
    except KeyboardInterrupt:
        pass