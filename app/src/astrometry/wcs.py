import subprocess


def get_center_coords(wcsfile):

    wcs = subprocess.run(['wcsinfo', wcsfile],
                         stdout=subprocess.PIPE, universal_newlines=True)

    for line in wcs.stdout.split("\n"):
        if "ra_center " in line:
            ra = line.split(" ")[1].strip()
        if "dec_center " in line:
            dec = line.split(" ")[1].strip()

    return ra, dec
