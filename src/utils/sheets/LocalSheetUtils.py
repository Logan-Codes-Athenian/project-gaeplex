import pandas as pd
import os

class LocalSheetUtils:
    def __init__(self):
        self.DIR = 'src/sheets'
        os.makedirs(self.DIR, exist_ok=True)

    def write_to_row(self, sheet_name, given_data):
        file_path = f"{self.DIR}/{sheet_name}.csv"
        try:
            # If the file exists, read it; otherwise, create a new DataFrame.
            if os.path.exists(file_path):
                df = pd.read_csv(file_path, encoding="utf-8")
                # Create a DataFrame for the new row.
                new_row_df = pd.DataFrame([given_data], columns=df.columns)
                # Append the new row.
                df = pd.concat([df, new_row_df], ignore_index=True)
            else:
                df = pd.DataFrame([given_data])
            # Write the updated DataFrame back to CSV.
            df.to_csv(file_path, index=False, encoding="utf-8")
            print("wrote to row")
            return True
        except Exception as e:
            print(f"Error writing to {sheet_name}.csv: {e}")
            return False

    def get_sheet_by_name(self, sheet_name):
        file_path = f"{self.DIR}/{sheet_name}.csv"
        try:
            # Read the CSV using pandas.
            df = pd.read_csv(file_path, encoding="utf-8")
            print(f"Dataframe for Get Sheet: {file_path}\n{df}")
            # Return the df.
            return df
        except FileNotFoundError:
            print(f"Error: {sheet_name}.csv not found.")
            return None
        except Exception as e:
            print(f"Error reading {sheet_name}.csv: {e}")
            return None

    def update_sheet_by_name(self, sheet_name, updated_data):
        file_path = f"{self.DIR}/{sheet_name}.csv"
        try:
            # Assume updated_data is a list of lists with the first row as header.
            header = updated_data[0]
            data_rows = updated_data[1:]
            df = pd.DataFrame(data_rows, columns=header)
            df.to_csv(file_path, index=False, encoding="utf-8")
            return True
        except Exception as e:
            print(f"Error updating {sheet_name}.csv: {e}")
            return False
