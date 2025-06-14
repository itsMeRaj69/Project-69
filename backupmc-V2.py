import subprocess
import sys
import os
import shutil
import zipfile
import json
import requests
import time  # For time.sleep
from datetime import datetime
from colorama import init, Fore, Style

# Ensure the necessary packages are installed
def install_package(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    import dropbox
except ImportError:
    print("Dropbox module not found. Installing...")
    install_package('dropbox')
    import dropbox

try:
    from colorama import init, Fore, Style
except ImportError:
    print("Colorama module not found. Installing...")
    install_package('colorama')
    from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Define gradient colors using ANSI escape codes
gradient_colors = [
    Fore.LIGHTYELLOW_EX, Fore.YELLOW, Fore.LIGHTGREEN_EX, Fore.GREEN,
    Fore.LIGHTCYAN_EX, Fore.CYAN, Fore.LIGHTRED_EX, Fore.RED
]

# Clear the screen
def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# Function to print gradient text
def print_gradient_text(text):
    gradient_text = ""
    for i, char in enumerate(text):
        color = gradient_colors[i % len(gradient_colors)]
        gradient_text += f"{color}{char}"
    print(gradient_text)

# Initialize settings
SETTINGS_FILE = 'backup_settings.json'
if not os.path.exists(SETTINGS_FILE):
    settings = {
        'APP_KEY': '',
        'APP_SECRET': '',
        'AUTH_CODE': '',
        'DROPBOX_ACCESS_TOKEN': '',
        'REFRESH_TOKEN': '',
        'SERVER_FOLDER_PATH': '',  # This will store the full path (e.g., /home/user/TestFolder)
        'WORLD_FOLDERS': ['world', 'world_nether', 'world_the_end'],
        'PLUGINS_FOLDER': 'plugins',
        'ADDITIONAL_FILES': []
        }
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4)
else:
    with open(SETTINGS_FILE, 'r') as f:
        settings = json.load(f)

# Global variables
APP_KEY = settings.get('APP_KEY', '')
APP_SECRET = settings.get('APP_SECRET', '')
AUTH_CODE = settings.get('AUTH_CODE', '')
ACCESS_TOKEN = settings.get('DROPBOX_ACCESS_TOKEN', '')
REFRESH_TOKEN = settings.get('REFRESH_TOKEN', '')
SERVER_FOLDER_PATH = settings.get('SERVER_FOLDER_PATH', '')
WORLD_FOLDERS = settings.get('WORLD_FOLDERS', [])
PLUGINS_FOLDER = settings.get('PLUGINS_FOLDER', '')
ADDITIONAL_FILES = settings.get('ADDITIONAL_FILES', [])

def obtain_initial_tokens():
    global AUTH_CODE, ACCESS_TOKEN, REFRESH_TOKEN
    if not AUTH_CODE:
        print(f"{Fore.CYAN}Visit the following URL to authorize the app:")
        print(f"https://www.dropbox.com/oauth2/authorize?client_id={APP_KEY}&token_access_type=offline&response_type=code")
        AUTH_CODE = input(f"{Fore.YELLOW}Enter the authorization code here: {Style.RESET_ALL}").strip()
        settings['AUTH_CODE'] = AUTH_CODE
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=4)
    
    url = "https://api.dropboxapi.com/oauth2/token"
    data = {
        'code': AUTH_CODE,
        'grant_type': 'authorization_code',
        'client_id': APP_KEY,
        'client_secret': APP_SECRET,
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        tokens = response.json()
        ACCESS_TOKEN = tokens['access_token']
        REFRESH_TOKEN = tokens['refresh_token']
        settings['DROPBOX_ACCESS_TOKEN'] = ACCESS_TOKEN
        settings['REFRESH_TOKEN'] = REFRESH_TOKEN
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=4)
    else:
        print("Error obtaining initial tokens:", response.json())
        exit(1)

def refresh_access_token():
    global ACCESS_TOKEN
    url = "https://api.dropboxapi.com/oauth2/token"
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': REFRESH_TOKEN,
        'client_id': APP_KEY,
        'client_secret': APP_SECRET,
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        new_access_token = response.json()['access_token']
        settings['DROPBOX_ACCESS_TOKEN'] = new_access_token
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=4)
        ACCESS_TOKEN = new_access_token
    else:
        print("Failed to refresh access token:", response.json())
        exit(1)

def initialize_app_keys():
    global APP_KEY, APP_SECRET  # Remove SERVER_FOLDER_NAME from globals
    if not APP_KEY or not APP_SECRET:
        clear_screen()
        print_gradient_text("BACKUPMC V2 - INITIAL SETUP")
        APP_KEY = input(f"{Fore.MAGENTA}Enter your Dropbox App Key: {Style.RESET_ALL}").strip()
        APP_SECRET = input(f"{Fore.MAGENTA}Enter your Dropbox App Secret: {Style.RESET_ALL}").strip()
        
        # Save only APP_KEY and APP_SECRET
        settings['APP_KEY'] = APP_KEY
        settings['APP_SECRET'] = APP_SECRET
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=4)

# Initialize app keys if not set
initialize_app_keys()

# Obtain initial tokens if not set
if not ACCESS_TOKEN or not REFRESH_TOKEN:
    obtain_initial_tokens()
else:
    refresh_access_token()

# Function to select the server folder
def first_time_folder_setup():
    global SERVER_FOLDER_PATH
    clear_screen()
    print_gradient_text("BACKUPMC V2 - FIRST-TIME SETUP")
    print(f"{Fore.CYAN}1. Use THIS DIRECTORY (where the script is located)")
    print(f"{Fore.CYAN}2. Select a custom directory")
    choice = input(f"{Fore.YELLOW}Enter your choice: {Style.RESET_ALL}").strip()

    if choice == '1':
        # Use the CURRENT DIRECTORY (where the script is located)
        SERVER_FOLDER_PATH = os.getcwd()  # Fix: Use current directory, not parent
        print(f"{Fore.GREEN}Using THIS directory: {SERVER_FOLDER_PATH}")
    elif choice == '2':
        custom_folder = input(f"{Fore.YELLOW}Enter the full path to the directory: {Style.RESET_ALL}").strip()
        if os.path.isdir(custom_folder):
            SERVER_FOLDER_PATH = custom_folder
            print(f"{Fore.GREEN}Using custom directory: {SERVER_FOLDER_PATH}")
        else:
            print(f"{Fore.RED}Invalid path! Using THIS directory.")
            SERVER_FOLDER_PATH = os.getcwd()  # Fallback to script's directory
    else:
        print(f"{Fore.RED}Invalid choice. Using THIS directory.")
        SERVER_FOLDER_PATH = os.getcwd()

    # Save to settings
    settings['SERVER_FOLDER_PATH'] = SERVER_FOLDER_PATH
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4)
    time.sleep(2)

# Modified initialization flow
if not SERVER_FOLDER_PATH:
    first_time_folder_setup()

# Paths to Minecraft server files
TEMP_BACKUP_PATH = os.path.join(os.getcwd(), 'tmp_backup')
TEMP_RESTORE_PATH = os.path.join(os.getcwd(), 'tmp_restore')

# Create a Dropbox client
dbx = dropbox.Dropbox(ACCESS_TOKEN)

def zip_folder(folder_path, zip_path):
    """Create a zip file of a folder."""
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, arcname=relative_path)

def upload_to_dropbox(file_path, dropbox_path):
    """Upload a file to Dropbo, overwriting if it exists."""
    try:
        CHUNK_SIZE = 4 * 1024 * 1024  # 4MB chunk size for large files
        with open(file_path, 'rb') as f:
            file_size = os.path.getsize(file_path)
            if file_size <= CHUNK_SIZE:
                dbx.files_upload(f.read(), dropbox_path, mode=dropbox.files.WriteMode.overwrite)
            else:
                upload_session_start_result = dbx.files_upload_session_start(f.read(CHUNK_SIZE))
                cursor = dropbox.files.UploadSessionCursor(session_id=upload_session_start_result.session_id,
                                                           offset=f.tell())
                commit = dropbox.files.CommitInfo(path=dropbox_path, mode=dropbox.files.WriteMode.overwrite)
                
                while f.tell() < file_size:
                    if (file_size - f.tell()) <= CHUNK_SIZE:
                        dbx.files_upload_session_finish(f.read(CHUNK_SIZE),
                                                        cursor,
                                                        commit)
                    else:
                        dbx.files_upload_session_append(f.read(CHUNK_SIZE),
                                                        cursor.session_id,
                                                        cursor.offset)
                        cursor.offset = f.tell()
                        print(f'\rUploading {os.path.basename(file_path)}: {round(cursor.offset / file_size * 100)}%', end='')

            print(f"\r{Fore.CYAN}Upload of {os.path.basename(file_path)} completed successfully.")

    except dropbox.exceptions.ApiError as api_err:
        print(f"\r{Fore.RED}Error uploading {os.path.basename(file_path)}: {api_err}")
    except Exception as e:
        print(f"\r{Fore.RED}An error occurred during upload of {os.path.basename(file_path)}: {e}")
        
def upload_directory_to_dropbox(local_directory, dropbox_directory):
    """Upload the contents of a local directory to a Dropbox directory."""
    for root, dirs, files in os.walk(local_directory):
        for file in files:
            local_path = os.path.join(root, file)
            relative_path = os.path.relpath(local_path, local_directory)
            dropbox_path = f'{dropbox_directory}/{relative_path}'.replace("\\", "/")
            upload_to_dropbox(local_path, dropbox_path)

def zip_additional_files(additional_files, zip_path):
    """Zip additional files and folders."""
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for item in additional_files:
            item_path = os.path.join(SERVER_FOLDER_PATH, item)
            if os.path.isdir(item_path):
                for root, _, files in os.walk(item_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        relative_path = os.path.relpath(file_path, SERVER_FOLDER_PATH)
                        zipf.write(file_path, arcname=relative_path)
            else:
                if os.path.exists(item_path):
                    zipf.write(item_path, arcname=os.path.basename(item_path))
                else:
                    print(f"{Fore.RED}Warning: {item} does not exist.")            
            
def start_backup():
    clear_screen()
    print_gradient_text("BACKUPMC V2")

    print(f"{Fore.CYAN}Starting backup process...")

    # Create a temporary backup folder
    if not os.path.exists(TEMP_BACKUP_PATH):
        os.makedirs(TEMP_BACKUP_PATH)

    try:
        # Zip world folders to the temporary backup folder
        for world_folder in WORLD_FOLDERS:
            src_path = os.path.join(SERVER_FOLDER_PATH, world_folder)
            dest_zip_path = os.path.join(TEMP_BACKUP_PATH, f'{world_folder}.zip')
            zip_folder(src_path, dest_zip_path)
            print(f"Zipped {world_folder}")

        # Zip plugins folder to the temporary backup folder
        plugins_src_path = os.path.join(SERVER_FOLDER_PATH, PLUGINS_FOLDER)
        plugins_dest_zip_path = os.path.join(TEMP_BACKUP_PATH, 'plugins.zip')
        zip_folder(plugins_src_path, plugins_dest_zip_path)
        print("Zipped plugins folder")

        # Zip additional files to the temporary backup folder
        if ADDITIONAL_FILES:
            additional_files_path = os.path.join(TEMP_BACKUP_PATH, 'AdditionalFiles.zip')
            zip_additional_files(ADDITIONAL_FILES, additional_files_path)
            print("Zipped additional files")

        # Upload the temporary backup folder to Dropbox
        print("Uploading to Dropbox...")
        upload_directory_to_dropbox(TEMP_BACKUP_PATH, '/backups')

        # Show completion message without clearing screen
        print(f"{Fore.GREEN}Backup completed successfully!")        

    except Exception as e:
        # Show error message for 4 seconds
        print(f"{Fore.RED}Backup failed: {e}")
        time.sleep(4)
        return

    finally:
        # Delete the temporary backup folder regardless of success or failure
        shutil.rmtree(TEMP_BACKUP_PATH, ignore_errors=True)
        input("Press Enter to return to the main menu...")

# Functions of Extraction Process

def extract_directly(zip_path, destination_folder):
    """Extract the entire zip file directly to the destination folder."""
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(destination_folder)
    print(f"{Fore.GREEN}Extraction completed successfully.")

def extract_zip_to_named_folder(zip_path, destination_folder):
    """Extract the contents of a zip file to a folder named after the zip file."""
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        extract_folder = os.path.join(destination_folder, os.path.splitext(os.path.basename(zip_path))[0])
        os.makedirs(extract_folder, exist_ok=True)
        zip_ref.extractall(extract_folder)

def extract_specific_content(zip_path, destination_folder):
    """Extract specific content from a zip file to the server folder."""
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        print(f"{Fore.CYAN}Files in the archive:")
        file_list = zip_ref.namelist()
        for i, file in enumerate(file_list):
            print(f"{Fore.BLUE}{i + 1}. {file}")
        
        file_choice = input(f"{Fore.GREEN}Enter the number of the file to extract: {Style.RESET_ALL}").strip()
        file_choice = int(file_choice) - 1

        if file_choice < 0 or file_choice >= len(file_list):
            print(f"{Fore.RED}Invalid choice.")
            time.sleep(2)
            return

        specific_file = file_list[file_choice]
        zip_ref.extract(specific_file, destination_folder)
        print(f"{Fore.GREEN}Restored {specific_file} successfully.") 
 
def copy_backup_directly(zip_path, destination_folder):
    """Copy the backup zip file directly to the server folder without extraction."""
    shutil.copy(zip_path, destination_folder)
    print(f"{Fore.GREEN}Backup copied to the server folder successfully.") 

    
def restore_backup():
    while True:
        try:
            clear_screen()
            print_gradient_text("BACKUPMC V2 - RESTORE")

            print(f"{Fore.CYAN}Fetching list of available backups from Dropbox...")

            # List all backup files in the Dropbox backups directory
            response = dbx.files_list_folder('/backups')
            backups = [entry.name for entry in response.entries if isinstance(entry, dropbox.files.FileMetadata)]

            if not backups:
                print(f"{Fore.RED}No backups found.")
                time.sleep(2)
                return

            print(f"{Fore.CYAN}Available backups:")
            for i, backup in enumerate(backups):
                print(f"{Fore.BLUE}{i+1}. {backup}")

            print(f"{Fore.BLUE}x. Exit")

            choice = input(f"{Fore.YELLOW}Select a backup to restore (enter the number): {Style.RESET_ALL}").strip()
            if choice.lower() == 'x':
                return

            choice = int(choice) - 1
            if choice < 0 or choice >= len(backups):
                print(f"{Fore.RED}Invalid choice.")
                time.sleep(2)
                return

            backup_to_restore = backups[choice]
            backup_local_path = os.path.join(TEMP_RESTORE_PATH, backup_to_restore)

            # Ensure the directory exists before downloading
            if not os.path.exists(TEMP_RESTORE_PATH):
                os.makedirs(TEMP_RESTORE_PATH)

            # Download selected backup from Dropbox
            print(f"{Fore.CYAN}Downloading {backup_to_restore}...")

            with open(backup_local_path, "wb") as f:
                metadata, res = dbx.files_download(f'/backups/{backup_to_restore}')
                f.write(res.content)
            
            print(f"{Fore.GREEN}Download completed.")

            # Restore options
            print(f"{Fore.CYAN}Select restore option:")
            print(f"{Fore.BLUE}1. Extract directly to the server folder")
            print(f"{Fore.BLUE}2. Extract to archive name with replace")
            print(f"{Fore.BLUE}3. Extract specific content into the server folder")
            print(f"{Fore.BLUE}4. Skip extraction and copy directly to the server folder")
            print(f"{Fore.BLUE}x. Exit")
            
            restore_choice = input(f"{Fore.GREEN}Enter your choice: {Style.RESET_ALL}").strip()
            if restore_choice.lower() == 'x':
                return

            if restore_choice == '1':
                # Extract directly to the server folder
                extract_directly(backup_local_path, SERVER_FOLDER_PATH)
                print(f"{Fore.GREEN}Restore completed successfully.")

            elif restore_choice == '2':
                # Extract the entire archive to its original location with replace
                extract_zip_to_named_folder(backup_local_path, SERVER_FOLDER_PATH)
                print(f"{Fore.GREEN}Restore completed successfully.")

            elif restore_choice == '3':
                # Extract specific content into the server folder
                extract_specific_content(backup_local_path, SERVER_FOLDER_PATH)

            elif restore_choice == '4':
                # Skip extraction and copy directly to the server folder
                copy_backup_directly(backup_local_path, SERVER_FOLDER_PATH)

            else:
                print(f"{Fore.RED}Invalid choice.")
                time.sleep(2)                            

        except Exception as e:
            print(f"{Fore.RED}An error occurred during restoration: {e}")
            time.sleep(4)
            return

        finally:
            # Clean up temporary restore folder
            shutil.rmtree(TEMP_RESTORE_PATH, ignore_errors=True)
            input("Press Enter to return to the main menu...")

def delete_backups():
    try:
        clear_screen()
        print_gradient_text("BACKUPMC V2 - DELETE BACKUPS")

        print(f"{Fore.CYAN}Fetching list of available backups from Dropbox...")

        # List all backup files in the Dropbox backups directory
        response = dbx.files_list_folder('/backups')
        backups = [entry.name for entry in response.entries if isinstance(entry, dropbox.files.FileMetadata)]

        if not backups:
            print(f"{Fore.RED}No backups found.")
            time.sleep(2)
            return

        print(f"{Fore.CYAN}Available backups:")
        for i, backup in enumerate(backups):
            print(f"{Fore.BLUE}{i+1}. {backup}")

        print(f"{Fore.BLUE}x. Exit")

        choice = input(f"{Fore.YELLOW}Select a backup to delete (enter the number): {Style.RESET_ALL}").strip()
        if choice.lower() == 'x':
            return

        choice = int(choice) - 1
        if choice < 0 or choice >= len(backups):
            print(f"{Fore.RED}Invalid choice.")
            time.sleep(2)
            return

        backup_to_delete = backups[choice]
        dbx.files_delete_v2(f'/backups/{backup_to_delete}')
        print(f"{Fore.GREEN}Backup '{backup_to_delete}' deleted successfully.")

        input("Press Enter to return to the main menu...")

    except Exception as e:
        print(f"{Fore.RED}An error occurred during deletion: {e}")
        time.sleep(4)
        return

def manage_settings():
    while True:
        clear_screen()
        print_gradient_text("BACKUPMC V2 - MANAGE SETTINGS")
        print(f"{Fore.CYAN}1. Add/Remove Folder/Files (To backup)")
        print(f"{Fore.CYAN}2. Change Dropbox App Credentials")
        print(f"{Fore.CYAN}3. Change Server Directory")
        print(f"{Fore.CYAN}4. Delete Backups")
        print(f"{Fore.CYAN}x. Exit to menu")
        
        choice = input(f"{Fore.YELLOW}Enter your choice: {Style.RESET_ALL}").strip()

        if choice == '1':
            # Add/Remove Folder/Files
            print(f"{Fore.CYAN}Current additional files/folders: {ADDITIONAL_FILES}")
            file_or_folder = input(f"{Fore.YELLOW}Enter the file/folder name to add or remove: {Style.RESET_ALL}").strip()

            if file_or_folder in ADDITIONAL_FILES:
                ADDITIONAL_FILES.remove(file_or_folder)
                print(f"{Fore.RED}Removed {file_or_folder} from additional files.")
            else:
                ADDITIONAL_FILES.append(file_or_folder)
                print(f"{Fore.GREEN}Added {file_or_folder} to additional files.")

            settings['ADDITIONAL_FILES'] = ADDITIONAL_FILES
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(settings, f, indent=4)

            input("Press Enter to continue...")

        elif choice == '2':
            # Change App Key, Secret Key, and Server Folder Name
            new_app_key = input(f"{Fore.MAGENTA}Enter new app key: {Style.RESET_ALL}").strip()
            new_app_secret = input(f"{Fore.MAGENTA}Enter new app secret: {Style.RESET_ALL}").strip()
            
            print(f"{Fore.YELLOW}Visit the following URL to authorize the app:")
            print(f"https://www.dropbox.com/oauth2/authorize?client_id={new_app_key}&token_access_type=offline&response_type=code")
            new_auth_code = input(f"{Fore.YELLOW}Enter the authorization code here: {Style.RESET_ALL}").strip()

            settings['APP_KEY'] = new_app_key
            settings['APP_SECRET'] = new_app_secret
            settings['AUTH_CODE'] = new_auth_code

            with open(SETTINGS_FILE, 'w') as f:
                json.dump(settings, f, indent=4)

            # Update the global variables
            global APP_KEY, APP_SECRET, AUTH_CODE
            APP_KEY = new_app_key
            APP_SECRET = new_app_secret
            AUTH_CODE = new_auth_code

            # Obtain new tokens with the new credentials
            obtain_initial_tokens()

            input("Press Enter to continue...")
            
        elif choice == '3':
            first_time_folder_setup()    
            
        elif choice == '4':
            # Delete Backups
            delete_backups()

        elif choice.lower() == 'x':
            return

        else:
            print(f"{Fore.RED}Invalid choice.")
            time.sleep(2)

def main_menu():
    while True:
        clear_screen()
        print_gradient_text("BACKUPMC V2")

        print(f"{Fore.CYAN}1. Start Backup")
        print(f"{Fore.CYAN}2. Restore Backups")
        print(f"{Fore.CYAN}3. Manage Settings")
        print(f"{Fore.CYAN}x. Exit")

        choice = input(f"{Fore.YELLOW}Enter your choice: {Style.RESET_ALL}").strip()

        if choice == '1':
            start_backup()
        elif choice == '2':
            restore_backup()
        elif choice == '3':
            manage_settings()
        elif choice.lower() == 'x':
            clear_screen()
            print(f"{Fore.GREEN}Goodbye!")
            time.sleep(2)
            break
        else:
            print(f"{Fore.RED}Invalid choice.")
            time.sleep(2)

# Entry point
if __name__ == '__main__':
    # Add argument parsing
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "1":
            start_backup()
        elif command == "2":
            restore_backup()
        elif command == "3":
            manage_settings()
        elif command.lower() == "x":
            clear_screen()
            print(f"{Fore.GREEN}Goodbye!")
            time.sleep(2)
            sys.exit(0)
        else:
            print(f"{Fore.RED}Invalid argument. Usage:")
            print(f"{Fore.CYAN}python3 backupmc-V2.py [option]")
            print(f"{Fore.CYAN}Options:")
            print(f"{Fore.CYAN}1 - Start Backup")
            print(f"{Fore.CYAN}2 - Restore Backups")
            print(f"{Fore.CYAN}3 - Manage Settings")
            print(f"{Fore.CYAN}x - Exit")
            sys.exit(1)
    else:
        main_menu()
