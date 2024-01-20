import time
import os
import click
from colorama import Fore,Style
from dotenv import load_dotenv, dotenv_values
from .siril import siril, write_script

load_dotenv()
config = dotenv_values(".env")

CPU_THREADS=config.get('CPU_THREADS')
SIRIL_TMP_DIR=config.get('SIRIL_TMP_DIR')
BIASES_TEMPLATE=config.get('BIASES_TEMPLATE')
BIASES_LOG=config.get('BIASES_LOG')
PROCESS_DIR=config.get('PROCESS_DIR')
STACKED_DIR=config.get('STACKED_DIR')
STACKED_BIASES_NAME=config.get('STACKED_BIASES_NAME')

def stackBiases(wd, master_bias_fits=None, replace=False):

    time_start = time.perf_counter()
    write_script(
        name=BIASES_TEMPLATE,
        content=f'''\
requires 1.2.0
SETCPU {CPU_THREADS}
cd biases
CONVERT biases -out=../{PROCESS_DIR}
cd ../{PROCESS_DIR}
STACK biases_.seq rej w 3 3 -norm=mul -out=../{STACKED_DIR}/{STACKED_BIASES_NAME}
'''
)
    siril(
        title="STACKING BIAS FRAMES",
        wd=wd, 
        script=f"{SIRIL_TMP_DIR}/{BIASES_TEMPLATE}",
        log=f"{wd}/{BIASES_LOG}"
    )
    print(f"Stacking Biases Total Time: {round(time.perf_counter() - time_start, 2)}")

def checkBiases(wd, master_bias_fits):
    current_bias_fits=master_bias_fits
    # Biases Handling
    if os.path.exists(f"{wd}/biases") and len(os.listdir(f"{wd}/biases")) != 0:
        if click.confirm(f"{Fore.CYAN}Bias Frames exist in working directory, do you want to use these?{Fore.RESET}", default=True):
            use_bias = True
            if (click.confirm(f"{Fore.RED}Replace{Fore.RESET} the master bias file (Y), or just use for this sesson (N)?\n{Style.DIM}{master_bias_fits}{Style.RESET_ALL}", default=False)):
                print("Using for this session and replacing master")
                replace_bias = True
            else:
                print("Using only for this session")
                replace_bias = False

            stackBiases(wd=wd, master_bias_fits=master_bias_fits, replace=replace_bias)
            current_bias_fits=f"{wd}/{STACKED_DIR}/{STACKED_BIASES_NAME}.fits"
        else:
            print('Ignoring bias frames and stacking with existing master bias library')
    return current_bias_fits