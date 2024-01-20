from dotenv import load_dotenv, dotenv_values
import subprocess
from .logger import logStart, logNote, sirilLogger

load_dotenv()
config = dotenv_values(".env")
SIRIL_TMP_DIR=config.get('SIRIL_TMP_DIR')

def write_script(name, content):
    with open(f"{SIRIL_TMP_DIR}/{name}", 'w') as f:
        f.write(content)
        
def siril(title, wd, script, log):
    logStart(title)
    p = subprocess.Popen('/usr/bin/siril-cli -d ' + wd + ' -s ' + script, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    with p.stdout, open(log, 'ab') as file:
        for line in iter(p.stdout.readline, b''):
            sirilLogger(line)
            file.write(line)
        p.communicate()
    logNote(f"Full log: {log}")