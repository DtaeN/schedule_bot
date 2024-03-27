import subprocess
import datetime 

def run_script_and_log():
    with open('output.log', 'w') as log_file:
        process = subprocess.Popen(['python', 'bot.py'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            timestamped_line = f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {line.strip()}"
            print(timestamped_line)
            log_file.write(timestamped_line + '\n')
            log_file.flush() 
        process.wait()

run_script_and_log()