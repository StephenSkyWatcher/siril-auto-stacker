from colorama import Fore,Style

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

    if ('failed' in content and not '0 failed' in content and not '[FAILURE] initial call to atFindTrans failed' in content):
        logFailure(content)