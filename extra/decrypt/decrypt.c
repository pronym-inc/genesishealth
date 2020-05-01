#include <stdio.h>
#include <string.h>
#include "aes.h"

void CharToHex(char *src, unsigned char start_char, unsigned char *dest)
{
  unsigned char i=0;
  unsigned char H_Nibble=0, L_Nibble=0;
 
  H_Nibble=src[start_char+i];
  L_Nibble=src[start_char+i+1];
  if(H_Nibble>0x39) H_Nibble= (H_Nibble-0x41)+0x0a;
  else H_Nibble= H_Nibble-0x30;
  if(L_Nibble>0x39) L_Nibble= (L_Nibble-0x41)+0x0a;
  else L_Nibble= L_Nibble-0x30;
  *dest=((H_Nibble & 0x0F)<<4)  + (L_Nibble & 0x0F);
}

int main(int argc, char* argv[])
{
  unsigned char *key = (unsigned char*) argv[argc-1];
  unsigned char return_str[17];
  char ascil_value[18];
  char *temp;
  int i=0,j=0;
  char bytestr_value[2];
  unsigned char byte_value;
  unsigned char checksum=0;
  unsigned char recv_checksum=0;
  memset(return_str,0x00,sizeof(char)*17);
  memset(ascil_value,0x00,sizeof(char)*18);
  if(argc<=1){
    printf("parameter error\n");
    return 1;
  }
  temp= argv[argc-2];
  // check sum
  for(i=0;i<strlen(temp)-2;i++) checksum += temp[i];
  // transfer to hex
  if(strlen(temp)!=34){
    printf("parameter error\n");
    return 1;
  }
  for(i=0,j=0;i<(strlen(temp));i+=2,j++){
    memset(bytestr_value,0x00,sizeof(bytestr_value));
    bytestr_value[0]= temp[i];
    bytestr_value[1]= temp[i+1];
    CharToHex(bytestr_value,0,&byte_value);
    if(i<(strlen(temp)-2))
      return_str[j]= byte_value;
    else
      recv_checksum=  byte_value;
  }
  if(recv_checksum!=checksum){
    printf("checksum error\n");
    return 1;
  }
  aes_decrypt(return_str,key) ;
  printf("%s",return_str);
  return 0;
}
