import requests
import pyodbc

def read_text_file(file_path):
    """Reads the content of a text file and returns it as a string."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()
    
def write_text_file(file_path, text):
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(text)
        
def get_table_definition_as_string(server, database, schema_table_name, username=None, password=None, driver="{ODBC Driver 17 for SQL Server}"):
    try:
        if username and password:
            conn_str = f"DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        else:
            conn_str = f"DRIVER={driver};SERVER={server};DATABASE={database};Trusted_Connection=yes"

        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        schema, table_name = schema_table_name.split(".")

        # Fetch column definitions
        query = f"""
        SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE, COLUMN_DEFAULT
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = '{schema}' AND TABLE_NAME = '{table_name}'
        """

        cursor.execute(query)
        rows = cursor.fetchall()

        create_table_stmt = f"CREATE TABLE {schema_table_name} ("

        column_definitions = []
        for row in rows:
            col_name = row[0]
            data_type = row[1]
            char_max_length = row[2]
            is_nullable = "NULL" if row[3] == "YES" else "NOT NULL"
            col_default = f"DEFAULT {row[4]}" if row[4] else ""

            if char_max_length and data_type in ("varchar", "nvarchar", "char", "nchar"):
                data_type = f"{data_type}({char_max_length})"

            column_definitions.append(f"    {col_name} {data_type} {col_default} {is_nullable}".strip())

        create_table_stmt += ",\n".join(column_definitions)
        create_table_stmt += "\n);\n"

        # Fetch indexes including included columns
        index_query = f"""
        SELECT i.name AS index_name, 
               i.type_desc, 
               ic.index_column_id, 
               c.name AS column_name,
               ic.is_included_column
        FROM sys.indexes i
        JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
        JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
        WHERE i.object_id = OBJECT_ID('{schema}.{table_name}')
        ORDER BY i.name, ic.index_column_id
        """

        cursor.execute(index_query)
        index_rows = cursor.fetchall()

        indexes = {}
        for row in index_rows:
            index_name = row[0]
            index_type = row[1]
            column_name = row[3]
            is_included = row[4]
            
            if index_name not in indexes:
                indexes[index_name] = {"type": index_type, "columns": [], "included_columns": []}
            
            if is_included:
                indexes[index_name]["included_columns"].append(column_name)
            else:
                indexes[index_name]["columns"].append(column_name)

        for index_name, details in indexes.items():
            index_type = "UNIQUE " if "UNIQUE" in details["type"] else ""
            included_cols = f" INCLUDE ({', '.join(details['included_columns'])})" if details["included_columns"] else ""
            create_table_stmt += f"\nCREATE {index_type}INDEX {index_name} ON {schema_table_name} ({', '.join(details['columns'])}){included_cols};\n"

        cursor.close()
        conn.close()

        return create_table_stmt

    except Exception as e:
        return f"Error: {e}"
    
server = "."
database = "WideWorldImporters"

tables = [
    "Application.People",
    "Application.Countries",
    "Application.DeliveryMethods",
    "Application.PaymentMethods",
    "Application.TransactionTypes",
    "Purchasing.SupplierCategories",
    "Sales.BuyingGroups",
    "Sales.CustomerCategories",
    "Warehouse.Colors",
    "Warehouse.PackageTypes",
    "Application.StateProvinces",
    "Application.Cities",
    "Purchasing.Suppliers",
    "Sales.Customers",
    "Purchasing.PurchaseOrders",
    "Sales.Orders",
    "Warehouse.StockItems",
    "Sales.Invoices",
    "Sales.OrderLines",
    "Warehouse.StockItemHoldings",
    "Sales.CustomerTransactions",
    "Sales.InvoiceLines",
    "Warehouse.StockItemTransactions"
]
op="\n"
for table in tables:
    op+=(get_table_definition_as_string(server, database, table))

Requirement = read_text_file("BusinessRequirement.txt")
Prompt_Template=read_text_file("Prompt template.txt")
prompt=Prompt_Template.replace("[BUSINESS REQUIREMENT]",Requirement).replace("[TABLE STRUCTURE]",op)

write_text_file("op.txt",prompt)

# Define the Ollama API endpoint
# OLLAMA_API_URL = "http://localhost:11434/api/generate"
# OLLAMA_API_URL = "http://olty-win22-100.dev.local:11434/api/generate"

# def read_text_file(file_path):
#     """Reads the content of a text file and returns it as a string."""
#     with open(file_path, 'r', encoding='utf-8') as file:
#         return file.read()
    
# def write_text_file(file_path, text):
#     with open(file_path, 'w', encoding='utf-8') as file:
#         file.write(text)

# prompt = read_text_file("prompt template.txt")        
# prompt = "Write a sql query to get 3rd highest salary from employee table"
# # Define the payload for the API request
# payload = {
#     "model": "deepseek-r1:7b",
#     "prompt": prompt,
#     "stream": False  # Set to False for a single response, True for streaming
# }

# # Send the POST request to the Ollama API
# response = requests.post(OLLAMA_API_URL, json=payload, stream=True)

# # Check if the request was successful
# if response.status_code == 200:
#     # Handle the response
#     try:
#         # If streaming is enabled, read the response line by line
#         if payload.get("stream", False):
#             for line in response.iter_lines():
#                 if line:
#                     # Decode each line as JSON
#                     response_data = line.decode("utf-8")
#                     print("Streaming Response:", response_data)
#         else:
#             # If not streaming, decode the entire response as JSON
#             response_data = response.json()
#             generated_text = response_data.get("response", "")
#             # print("Generated Text:", generated_text)
#             write_text_file("op.txt",generated_text)
#     except Exception as e:
#         print(f"Error decoding JSON: {e}")
# else:
#     print(f"Error: {response.status_code} - {response.text}")