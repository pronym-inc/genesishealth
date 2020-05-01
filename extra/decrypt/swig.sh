swig -python -module aes interface.i
gcc -c -fPIC aes.c aes_wrap.c -I/usr/include/python2.6
gcc -shared -lpython *.o -o _aes.so -I/usr/include/python2.6
