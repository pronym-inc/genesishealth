decrypt: aes
	gcc -Wall -g3 -o decrypt *.o decrypt.c

encrypt: aes
	gcc -Wall -g3 -o encrypt *.o encrypt.c

aes:
	gcc -c aes.c

clean:
	-rm *.o
	-rm encrypt
	-rm decrypt

