from storage import Storage
import secrets
import argparse as ap
import os
from pyfiglet import Figlet
from colorama import Fore

parser = ap.ArgumentParser()
# Add "combinations" option (long and short format) to compute the number of possible combinations
parser.add_argument("--combinations", dest="combinations", metavar="<INT>",
                    help="number of possible combinations with the selected length", type=int)
parser.add_argument("-c", dest="combinations", metavar="<INT>",
                    help="the same of combinations option", type=int)

# Add "show" option (long and short format) to show all the characters that will be used to generate the password
parser.add_argument("-s", "--show", help="show all the characters that will be used to generate the password",
                    action="store_true")

# Add "length" option (long and short format) to generate a password with the selected length
parser.add_argument("--length", dest="length", metavar="<INT>", help="length of password to generate", type=int)
parser.add_argument("-l", dest="length", metavar="<INT>", help="the same of length option", type=int)

# Add "storage" option to access the storage
parser.add_argument("--storage", dest="storage", help="access the storage", action="store_true")

# Add "add" option to add a new password to the storage
parser.add_argument("--add", dest="add", help="add a new password to the storage", action="store_true")

# Add "author" option to show the author of the program
parser.add_argument("--author", dest="author", help="show the author of the program", action="store_true")

# Add "version" option to show the version of the program
parser.add_argument("--version", action="version", version="%(prog)s 1.0")

lowercase = "abcdefghijklmnopqrstuvwxyz"
uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
symbols = "!@#$%^&*()_+"
numbers = "0123456789"
passwd_char = lowercase + uppercase + symbols + numbers

title = "PassGEN"
style = "big"


def create_ascii_art(text, font):
    fig = Figlet(font=font)
    ascii_art = fig.renderText(text)
    return ascii_art


ascii_title = create_ascii_art(title, style)


# Generate the password
def generate(length):
    while True:
        # Check if length is less than 8
        if length < 8:
            print(f"{Fore.RED}Warning: password too weak - password should be at least 8 characters long{Fore.RESET}")
            raise SystemExit
        passwd = ""
        # Generate the password
        for _ in range(length):
            passwd += secrets.choice(passwd_char)
        print(f"Password: {passwd}")
        # Ask the user if the password is ok
        print("1. It's ok\n2. Generate another password")
        answer = input("Choose an option: ")
        if answer == "1":
            return passwd
        else:
            clear_display()
            continue


# Clear the display
def clear_display():
    if os.name == 'nt':
        os.system('cls')  # Windows
    else:
        os.system('clear')  # Unix-like, included macOS
    print(ascii_title)


# Compute the number of possible combinations
def compute_combinations(length):
    number = len(passwd_char) ** length
    return "{:,}".format(number)


# Show all the characters that will be used to generate the password
def show_characters():
    print(f"Lowercase: {lowercase}\nUppercase: {uppercase}\nSymbols: {symbols}\nNumbers: {numbers}\n")


# Count how many options are selected
def count_selected_options():
    count = 0
    if args.combinations:
        count += 1
    if args.length:
        count += 1
    if args.show:
        count += 1
    if args.storage:
        count += 1
    if args.add:
        count += 1
    if args.author:
        count += 1
    return count


if __name__ == "__main__":
    args = parser.parse_args()

    # Check if at least one option is selected
    if count_selected_options() == 0:
        parser.print_help()
        raise SystemExit

    clear_display()

    # Check if show option is selected
    if args.show:
        show_characters()
        raise SystemExit

    # Check if combinations options is selected
    if args.combinations:
        print(f"Number of possible combinations: {compute_combinations(args.combinations)}")
        raise SystemExit

    password = None
    # Check if length option is selected
    if args.length:
        password = generate(args.length)
        # Check if write option is selected, otherwise exit
        if args.add:
            # Connect to the storage
            st = Storage()
            clear_display()
            # Log in the user
            print(f"LOGIN")
            name = input("Username: ")
            master_pass = input("Password: ")
            login = st.user_login(name, master_pass)
            if login:
                while True:
                    clear_display()
                    # if the user is logged in, ask for service and username and add the password
                    print(f"Access granted to {st.name} (user id: {st.user_id})\n")
                    print("1. Add a service\n2. Update a service\n3. Exit")
                    # Ask for the operation to perform
                    choice = input("Choose an option: ")
                    if choice == "1":
                        clear_display()
                        # Ask for service and username
                        service = input("Service: ")
                        user = input("Username: ")
                        added = st.add_password(service, user, password)
                        if added:
                            clear_display()
                            # if added is True, the password is added successfully
                            print(f"{Fore.GREEN}Password added successfully{Fore.RESET}")
                            st.close()
                            raise SystemExit
                        else:
                            clear_display()
                            # if added is False, the password is not added because the service already exists
                            print(f"{Fore.RED}Service already exists{Fore.RESET}")
                            input("\nPress any key to continue...")
                            continue
                    elif choice == "2":
                        clear_display()
                        # Show all the services stored in the database
                        if len(st.show_services()) == 0:
                            print("No information stored")
                            input("\nPress any key to continue...")
                            continue
                        res = st.show_services()
                        for i, service in enumerate(res):
                            print(f"{i + 1}. {service[1]}")
                        # Ask for the service to update
                        n_service = input("Choose a service: ")
                        changed = False
                        for i, service in enumerate(res):
                            if n_service == str(i + 1):
                                # if the service is found, ask for the old password and update it
                                clear_display()
                                old_password = input("Old password: ")
                                if st.update_password(service[1], old_password, password):
                                    # if the password is updated successfully, print message
                                    clear_display()
                                    st.close()
                                    changed = True
                                    print(f"{Fore.GREEN}Password updated successfully{Fore.RESET}")
                                    raise SystemExit
                                else:
                                    clear_display()
                                    # if the old password is wrong, print message
                                    changed = True
                                    print(f"{Fore.RED}Wrong password{Fore.RESET}")
                                    input("\nPress any key to continue...")
                                    break
                        if not changed:
                            # if the service is not found, print message
                            clear_display()
                            print(f"{Fore.RED}Service not found{Fore.RESET}")
                            input("\nPress any key to continue...")
                        continue

                    elif choice == "3":
                        # Close connection and exit
                        clear_display()
                        st.close()
                        print(f"{Fore.GREEN}Connection closed{Fore.RESET}")
                        raise SystemExit
                    else:
                        # If the option is not valid, print message
                        clear_display()
                        print(f"{Fore.RED}Invalid option{Fore.RESET}")
                        input("\nPress any key to continue...")
                        continue
            else:
                clear_display()
                # if login is False, the user is not logged in because the username or the password is wrong
                print(f"{Fore.RED}Login failed - Wrong username or password{Fore.RESET}")
                st.close()
                raise SystemExit

        else:
            clear_display()
            # if add options is not selected, the password is generated and printed
            print(f"{Fore.GREEN}Password generated successfully{Fore.RESET}\t\tPASSWORD: {password}")
            raise SystemExit

    # Check if storage option is selected
    if args.storage:
        # Connect to the storage
        st = Storage()
        # Ask the user if he wants to register or login
        print("1. Register\n2. Login\n3. Exit")
        choice = input("Choose an option: ")
        if choice == "1":
            clear_display()
            # Ask for username and password
            name = input("Username: ")
            password = input("Password: ")
            if name == "" or password == "":
                clear_display()
                print(f"{Fore.RED}Username and password cannot be empty{Fore.RESET}")
                raise SystemExit
            # Register the user
            registration = st.user_registration(name, password)
            if registration:
                # if registration is True, close connection, print message and exit
                st.close()
                clear_display()
                print(f"{Fore.GREEN}Registration successful{Fore.RESET}")
                raise SystemExit
            else:
                # if registration is False, close connection, print message and exit
                st.close()
                clear_display()
                print(f"{Fore.RED}Registration failed - User already exists{Fore.RESET}")
                raise SystemExit
        elif choice == "2":
            clear_display()
            # Ask for username and password
            name = input("Username: ")
            password = input("Password: ")
            login = st.user_login(name, password)
            if login:
                while True:
                    clear_display()
                    # if login is True, ask for the operation to perform
                    print(f"Access granted to {st.name} (user id: {st.user_id})\n")
                    print("1. Add a new password\n2. Delete information\n3. Update information\n4. Show information\n5. Exit")
                    op = input("Choose an option: ")
                    if op == "1":
                        clear_display()
                        # Ask for service, username and password
                        service = input("Service: ")
                        user = input("Username: ")
                        passwd = input("Password: ")
                        adding = st.add_password(service, user, passwd)
                        if adding:
                            clear_display()
                            # if adding is True, the password is added successfully
                            print(f"{Fore.GREEN}Password added successfully{Fore.RESET}")
                            input("\nPress any key to continue...")
                            continue
                        else:
                            clear_display()
                            # if adding is False, the password is not added because the service already exists
                            print(f"{Fore.RED}Service already exists{Fore.RESET}")
                            input("\nPress any key to continue...")
                            continue
                    elif op == "2":
                        clear_display()
                        # Show all the services stored in the database
                        if len(st.show_services()) == 0:
                            print("No information stored")
                            input("\nPress any key to continue...")
                            continue
                        res = st.show_services()
                        for i, service in enumerate(res):
                            print(f"{i + 1}. {service[1]}")
                        # Ask for the service to delete
                        n_service = input("Choose a service: ")
                        deleted = False
                        for i, service in enumerate(res):
                            if n_service == str(i + 1):
                                # if the service is found, delete it
                                st.delete_password(service[1])
                                deleted = True
                                clear_display()
                                print(f"{Fore.GREEN}Password deleted successfully{Fore.RESET}")
                                break
                        # if the service is not found, print message
                        if not deleted:
                            clear_display()
                            print(f"{Fore.RED}Service not found{Fore.RESET}")

                        input("\nPress any key to continue...")
                        continue
                    elif op == "3":
                        clear_display()
                        # Show all the services stored in the database
                        if len(st.show_services()) == 0:
                            print("No information stored")
                            input("\nPress any key to continue...")
                            continue
                        res = st.show_services()
                        for i, service in enumerate(res):
                            print(f"{i + 1}. {service[1]}")
                        # Ask for the service to update
                        n_service = input("Choose a service: ")
                        changed = False
                        for i, service in enumerate(res):
                            if n_service == str(i + 1):
                                # if the service is found, ask for the old and new password and update it
                                clear_display()
                                old_password = input("Old password: ")
                                new_password = input("New password: ")
                                if st.update_password(service[1], old_password, new_password):
                                    # if the password is updated successfully, print message
                                    clear_display()
                                    changed = True
                                    print(f"{Fore.GREEN}Password updated successfully{Fore.RESET}")
                                else:
                                    clear_display()
                                    # if the old password is wrong, print message
                                    print(f"{Fore.RED}Wrong password{Fore.RESET}")
                                break

                        # if the service is not found, print message
                        if not changed:
                            clear_display()
                            print(f"{Fore.RED}Service not found{Fore.RESET}")

                        input("\nPress any key to continue...")
                        continue
                    elif op == "4":
                        clear_display()
                        # Show all the services stored in the database
                        if len(st.show_services()) == 0:
                            print("No information stored")
                            input("\nPress any key to continue...")
                            continue
                        res = st.show_services()
                        for i, service in enumerate(res):
                            print(f"{i + 1}. {service[1]}")
                        # Ask for the service to decrypt
                        n_service = input("Choose a service: ")
                        showed = False
                        for i, service in enumerate(res):
                            if n_service == str(i + 1):
                                # if the service is found, decrypt it and print it
                                username, password = st.retrieve_information(service[1])
                                clear_display()
                                showed = True
                                print(f"{Fore.GREEN}{str(service[1]).upper()}{Fore.RESET}\nUsername: {username.decode('utf-8')}"
                                      f"\nPassword: {password.decode('utf-8')}")
                                break

                        # if the service is not found, print message
                        if not showed:
                            clear_display()
                            print(f"{Fore.RED}Service not found{Fore.RESET}")
                        input("\nPress any key to continue...")
                        continue
                    elif op == "5":
                        # Close connection and exit
                        clear_display()
                        st.close()
                        print(f"{Fore.GREEN}Connection closed{Fore.RESET}")
                        raise SystemExit
                    else:
                        # If the option is not valid, print message
                        clear_display()
                        print(f"{Fore.RED}Invalid option{Fore.RESET}")
                        input("\nPress any key to continue...")
                        continue
            else:
                # if login is False, the user is not logged in because the username or the password is wrong
                clear_display()
                print(f"{Fore.RED}Login failed - Wrong username or password{Fore.RESET}")
                raise SystemExit
        elif choice == "3":
            # Close connection and exit
            clear_display()
            st.close()
            print(f"{Fore.GREEN}Connection closed{Fore.RESET}")
            raise SystemExit
        else:
            # If the option is not valid, print message
            clear_display()
            print(f"{Fore.RED}Invalid option{Fore.RESET}")
            raise SystemExit

    # Check if author option is selected
    if args.author is not None:
        print("Author: Nicola Staniscia\nGitHub: https://github.com/NicolaStaniscia\n"
              "LinkedIn: https://linkedin.com/in/nicola-staniscia\nCreation date: 2023-12-23\n")
        raise SystemExit

    # Check if version option is selected
    if args.version:
        print(args.version)
        raise SystemExit
