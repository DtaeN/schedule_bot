import subprocess
import datetime 
import os
# Указываем полный путь к файлу
log_directory = 'logs'  # Замените на фактический путь к директории журналов

# Проверяем, существует ли директория для журналов, и если нет, создаем ее
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

# Формируем полный путь к файлу журнала
log_file_path = os.path.join(log_directory, f'{datetime.datetime.now().strftime("%d-%m-%Y")}.log')

def run_script_and_log():
    with open(log_file_path, "a") as log_file:
        log_file.write("------------START------------\n")
        log_file.flush() 
        process = subprocess.Popen(['python', 'bot.py'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            timestamped_line = f"[{datetime.datetime.now().strftime("%d-%m-%Y | %H:%M:%S")}] {line.strip()}"
            print(timestamped_line)
            log_file.write(timestamped_line + '\n')
            log_file.flush() 
        process.wait()

run_script_and_log()