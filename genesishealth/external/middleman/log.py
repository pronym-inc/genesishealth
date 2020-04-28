def log(loc, b):
    f = open(loc, 'a')
    try:
        f.write(b)
    finally:
        f.close()
