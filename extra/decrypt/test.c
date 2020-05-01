#include <stdio.h>
#include <string.h>
#define BUFSIZE 16

void hex2char(char *a, unsigned char *buf)
{
  int ch;
  char tmp[2];
  int i, j;
  for (i=0,j=0; i<strlen(a); i=i+2,j++) {
    tmp[0] = a[i];
    tmp[1] = a[i+1];
    sscanf(tmp, "%x", &ch);
    buf[j] = ch;
    /* printf("%i %i %i \"%s\"\n", j, i, ch, buf); */
  }
}

int main(int argc, char **argv)
{
  unsigned char b[BUFSIZE];
  bzero(b, BUFSIZE+1);
  hex2char("3D75AF12F7EAB46764B725CE95DBEBA9", b);
  printf("strlen(b) -> %zu\n", strlen((char*)b));

  /*
  int k;
  for (k=0; k<strlen(buf); k++) { }
  */

  return 0;
}

