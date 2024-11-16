import requests
import json
import os
import logging
from threading import Timer, Thread
from flet import colors, Text, ProgressBar
memory_cache = {}
# Configuration
API_KEY = "AIzaSyBu1Jn1O8RDAe1SFNFwaBr2Sozw5qUmZ9Y"  # Remplacez par votre API Key
SPREADSHEET_ID = "1BOi13OBrITCVjbHY5osOJFZs4lp0gMVYQCFdRWzrpHY"
STATE_FILE = "app_state.json"

logging.basicConfig(level=logging.INFO)
def save_state(route):
    """Saves the current application state."""
    with open(STATE_FILE, "w") as f:
        json.dump({"route": route}, f)
def load_state():
    """Loads the previous application state."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f).get("route", "/")
    return "/"
def is_connected_to_internet():
    """Checks for an Internet connection."""
    try:
        requests.get("http://www.google.com", timeout=3)
        return True
    except requests.ConnectionError:
        return False
def get_spreadsheet_metadata():
    """Retrieves metadata for the Google Sheets spreadsheet."""
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}?fields=spreadsheetId,properties.modifiedTime,properties.title,sheets.properties&key={API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        metadata = response.json()
        logging.info(f"Metadata response: {json.dumps(metadata, indent=4)}")
        return metadata
    except requests.exceptions.RequestException as e:
        logging.error(f"Error retrieving metadata: {e}")
        return None
def download_all_sheets():
    """
    Downloads all sheets from the spreadsheet dynamically, applies zfill(10) to the 'mobile' field, 
    and saves them as JSON files in the 'assets' directory with leading zeros preserved.
    """
    # URL to fetch sheet metadata and sheet data
    metadata_url = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}?fields=sheets.properties.title&key={API_KEY}"
    try:
        # Fetch metadata to get sheet names
        metadata_response = requests.get(metadata_url)
        metadata_response.raise_for_status()
        metadata = metadata_response.json()

        # Extract sheet names
        sheet_names = [sheet["properties"]["title"] for sheet in metadata.get("sheets", [])]
        logging.info(f"Found sheets: {sheet_names}")

        # Download each sheet
        for sheet_name in sheet_names:
            sheet_data_url = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values/{sheet_name}?key={API_KEY}"
            sheet_response = requests.get(sheet_data_url)
            sheet_response.raise_for_status()
            sheet_data = sheet_response.json()

            # Process the 'mobile' field
            if "values" in sheet_data:
                headers = sheet_data["values"][0]
                rows = sheet_data["values"][1:]
                mobile_index = headers.index("mobile") if "mobile" in headers else None

                if mobile_index is not None:
                    for row in rows:
                        if len(row) > mobile_index:
                            # Ensure the mobile field is treated as a string and zero-padded
                            row[mobile_index] = str(row[mobile_index]).zfill(10)

                # Reassemble the sheet data
                sheet_data["values"] = [headers] + rows

            json_file_path = os.path.join('assets', f"contacts_{sheet_name}.json")
            with open(json_file_path, "w", encoding="utf-8") as f:
                json.dump(sheet_data, f, ensure_ascii=False, indent=4)
            logging.info(f"Downloaded and saved: {json_file_path}")

        logging.info("All sheets downloaded successfully.")

    except requests.exceptions.RequestException as e:
        logging.error(f"Error downloading sheets: {e}")

# ------------------------- GESTION DE LA PROGRESSION ------------------------- #
def show_loading_indicator(container):
    """Adds a ProgressBar to the container."""
    if container.controls and isinstance(container.controls[0], ProgressBar):
        return  # If already present, do nothing

    loading_bar = ProgressBar(width=300)
    container.controls.insert(0, loading_bar)
    container.update()

def hide_loading_indicator(container):
    """Removes the ProgressBar from the container."""
    if container.controls and isinstance(container.controls[0], ProgressBar):
        container.controls.pop(0)
    container.update()
def show_message(container, message, color):
    """Displays a temporary message above the button."""
    if container.controls and isinstance(container.controls[0], Text):
        container.controls.pop(0)
    message_text = Text(message, color=color, size=16)
    container.controls.insert(0, message_text)
    container.update()
    def remove_message():
        if container.controls and container.controls[0] == message_text:
            container.controls.pop(0)
            container.update()
    Timer(2, remove_message).start()

def update_data_if_online(page, container):
    """Always downloads the data when the update button is clicked."""
    show_loading_indicator(container)

    def download_task():
        if is_connected_to_internet():
            try:
                logging.info("Internet connection detected. Starting download...")
                
                # Download all sheets dynamically
                download_all_sheets()

                hide_loading_indicator(container)
                show_message(container, "Data updated successfully.", colors.GREEN)
            except Exception as e:
                logging.error(f"Error during data update: {e}")
                hide_loading_indicator(container)
                show_message(container, "Error during update.", colors.RED)
        else:
            logging.warning("No Internet connection.")
            hide_loading_indicator(container)
            show_message(container, "No Internet connection.", colors.RED)

    Thread(target=download_task).start()
# ------------------------- FILTRAGE DES DONNÉES ------------------------- #
def load_contacts_by_service(service_name):
    """Charge les contacts selon leur service."""
    local_data_file = os.path.join('assets', "contacts_services.json")
    try:
        if os.path.exists(local_data_file):
            with open(local_data_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            rows = data.get("values", [])
            headers = rows[0]  # En-têtes
            contacts = [dict(zip(headers, row)) for row in rows[1:]]
            return [contact for contact in contacts if contact.get("service") == service_name]
        else:
            logging.error(f"Fichier {local_data_file} introuvable.")
            return []
    except Exception as e:
        logging.error(f"Erreur lors du chargement des contacts : {e}")
        return []
def load_inspectors_by_cycle(cycle_name):
    """
    Charge les inspecteurs par cycle à partir du fichier JSON.
    """
    local_data_file = "assets/contacts_inspectors.json"
    try:
        if os.path.exists(local_data_file):
            with open(local_data_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Assurez-vous que 'values' est la clé utilisée dans le fichier JSON
            rows = data.get("values", [])
            headers = rows[0]  # La première ligne contient les en-têtes
            inspectors = [
                dict(zip(headers, row)) for row in rows[1:]
            ]  # Convertir en dictionnaire

            # Filtrer les inspecteurs par cycle
            return [inspector for inspector in inspectors if inspector.get("cycle") == cycle_name]
        else:
            logging.error(f"Fichier {local_data_file} introuvable.")
            return []
    except Exception as e:
        logging.error(f"Erreur lors du chargement des inspecteurs : {e}")
        return []
# Cache en mémoire
def load_data(sheet_name, force_reload=False):
    """
    Loads data from a specific sheet's JSON file or from memory cache.
    """
    global memory_cache

    if not force_reload and sheet_name in memory_cache:
        logging.info(f"Using cache for {sheet_name}.")
        return memory_cache[sheet_name]

    try:
        # Lazy imports
        import os
        import json

        local_data_file = f"assets/contacts_{sheet_name}.json"
        if os.path.exists(local_data_file):
            with open(local_data_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                rows = data.get("values", [])
                if rows and isinstance(rows[0], list):  # If data is in nested list format
                    headers = rows[0]
                    rows = [dict(zip(headers, row)) for row in rows[1:]]  # Convert to dictionaries
                memory_cache[sheet_name] = rows
                logging.info(f"{sheet_name} loaded from {local_data_file}.")
                return memory_cache[sheet_name]
        else:
            logging.warning(f"File {local_data_file} not found. Returning empty list.")
            return []  # Return an empty list if the file is missing
    except Exception as e:
        logging.error(f"Error loading data for {sheet_name}: {e}")
        return []  # Return an empty list on error
def download_sheets_in_background(spreadsheet_id, api_key):
    """
    Downloads all sheets from the Google Sheets spreadsheet in a background thread
    and ensures the 'mobile' field is zero-padded to 10 digits.
    """
    try:
        # URL to access the Google Sheets metadata
        url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}?key={api_key}"

        # Request to get the spreadsheet metadata
        response = requests.get(url)
        response.raise_for_status()
        spreadsheet_data = response.json()

        # Retrieve sheet names
        sheet_names = [sheet["properties"]["title"] for sheet in spreadsheet_data["sheets"]]
        logging.info(f"Sheet names retrieved: {sheet_names}")

        # Download and save each sheet
        for sheet_name in sheet_names:
            sheet_data_url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{sheet_name}?key={api_key}"
            sheet_response = requests.get(sheet_data_url)
            sheet_response.raise_for_status()
            sheet_data = sheet_response.json()

            # Process the data to apply zfill(10) to the 'mobile' field
            if "values" in sheet_data:
                headers = sheet_data["values"][0]
                rows = sheet_data["values"][1:]
                mobile_index = headers.index("mobile") if "mobile" in headers else None

                if mobile_index is not None:
                    for row in rows:
                        if len(row) > mobile_index and row[mobile_index].isdigit():
                            row[mobile_index] = row[mobile_index].zfill(10)

                # Re-assemble data with headers
                sheet_data["values"] = [headers] + rows

            # Save to a JSON file
            file_path = f"assets/contacts_{sheet_name}.json"
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(sheet_data, f, ensure_ascii=False, indent=4)
            logging.info(f"Data for sheet {sheet_name} saved to {file_path}.")

        logging.info("All sheets downloaded successfully.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error downloading sheets: {e}")


def build_google_sheets_url(endpoint, sheet_name=None):
    """Constructs the URL for Google Sheets API calls."""
    base_url = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}"
    if endpoint == "metadata":
        return f"{base_url}?fields=spreadsheetId,properties.modifiedTime,properties.title,sheets.properties&key={API_KEY}"
    elif endpoint == "sheet_data" and sheet_name:
        return f"{base_url}/values/{sheet_name}?key={API_KEY}"
    return None


