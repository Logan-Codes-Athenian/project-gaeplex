import csv

class LocalSheetUtils:
    def __init__(self):
        self.DIR = 'src/sheets'

    def write_to_row(self, sheet_name, given_data):
        # Construct the file path for the sheet
        file_path = f"{self.DIR}/{sheet_name}.csv"
        
        try:
            # Open the CSV file in append mode
            with open(file_path, mode='a', newline='') as file:
                writer = csv.writer(file)
                
                # Write the given data as a new row in the sheet
                writer.writerow(given_data)
                print("wrote to row")
            
            return True  # Indicate successful write
        except Exception as e:
            print(f"Error writing to {sheet_name}.csv: {e}")
            return False  # Indicate failure

    def get_sheet_by_name(self, sheet_name):
        try:
            # Construct the file path for the sheet
            file_path = f"{self.DIR}/{sheet_name}.csv"
            
            # Open and read the CSV file
            with open(file_path, mode='r', newline='') as file:
                reader = csv.reader(file)
                # Return the data as a list of rows (2D array)
                return list(reader)
        
        except FileNotFoundError:
            print(f"Error: {sheet_name}.csv not found.")
            return None

    def update_sheet_by_name(self, sheet_name, updated_data):
        # Construct the file path for the sheet
        file_path = f"{self.DIR}/{sheet_name}.csv"
        
        try:
            # Open the CSV file in write mode to overwrite it
            with open(file_path, mode='w', newline='') as file:
                writer = csv.writer(file)
                
                # Write the updated data to the sheet (overwrite entire content)
                writer.writerows(updated_data)
            
            return True  # Indicate successful update
        except Exception as e:
            print(f"Error updating {sheet_name}.csv: {e}")
            return False  # Indicate failure
