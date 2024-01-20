from dotenv import load_dotenv, dotenv_values
import subprocess
from colorama import Fore,Style


load_dotenv()
config = dotenv_values(".env")
SIRIL_TMP_DIR=config.get('SIRIL_TMP_DIR')

def write_script(name, content):
    with open(f"{SIRIL_TMP_DIR}/{name}", 'w') as f:
        f.write(content)

def logStart(c):
    print(f"\n\n{Fore.MAGENTA}⍟ {c} ⍟{Fore.RESET}")

def logStep(c):
    print(f"{Fore.CYAN}    ↛ {c}...{Fore.RESET}")

def logStepDetail(c):
    print(f"      {c}")

def logSuccess(c):
    print(f"{Fore.GREEN}✓ {c}{Fore.RESET}")

def logFailure(c):
    print(f"{Fore.RED}[FAILURE] {c}{Fore.RESET}")

def logNote(c):
    print(f"{Style.DIM}{c}{Style.RESET_ALL}")


def sirilLogger(line):
    content = line.decode()
    content = content.replace('log: ', '').replace('[A[2KT', '').replace('\n', '')
    
    if ('Running command' in content and not 'Running command: cd' in content and not 'Running command: requires' in content):
        logStep(f"{content}...")

    if ('Script execution finished successfully' in content or 'succeeded' in content):
        logSuccess(f"{content}...")

    if ('progress:' in content):
        logStepDetail(f"{content}")

    if ('failed' in content and not '0 failed' in content):
        logFailure(content)
        
def siril(title, wd, script, log):
    logStart(title)
    p = subprocess.Popen('/usr/bin/siril-cli -d ' + wd + ' -s ' + script, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    with p.stdout, open(log, 'ab') as file:
        for line in iter(p.stdout.readline, b''):
            sirilLogger(line)
            file.write(line)
        p.communicate()
    logNote(f"Full log: {log}")