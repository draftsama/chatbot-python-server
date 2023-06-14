import traceback

contents = []
try:
    print(contents[3])
except Exception as e:
    error_message = traceback.format_exc()  # Get the formatted error message
    with open('output.txt', 'w') as file:
        file.write(error_message)
