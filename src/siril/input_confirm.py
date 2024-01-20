import click

def confirm(q):
    if click.confirm(q, default=True):
        return True
    else:
        return False