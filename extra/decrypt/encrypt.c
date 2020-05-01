#include <stdio.h>
#include <string.h>
#include "aes.h"

void HexToChar(unsigned char hex, unsigned char * destination, int index)
{
  unsigned char H_Nibble=0, L_Nibble=0;
  
  L_Nibble = hex & 0x0F;
  H_Nibble = (hex & 0xF0) >> 4;
  if (L_Nibble < 10) L_Nibble = L_Nibble + 0x30;
  else L_Nibble = L_Nibble + 0x37;
  if (H_Nibble < 10) H_Nibble = H_Nibble + 0x30;
  else H_Nibble = H_Nibble + 0x37;
  destination[index] = H_Nibble;
  destination[index + 1] = L_Nibble;
}

int main(int argc, char* argv[])
{
    unsigned char *unencrypted = (unsigned char*) argv[argc-2];
    unsigned char *key = (unsigned char*) argv[argc-1];
    int unencrypted_length = strlen((const char *) unencrypted);
    unsigned char get_encrypted[16];
    unsigned char encrypted[16];
    unsigned char parsed[34];
    unsigned char checksum=0;
    int i=0;

    memset(parsed, '\0', sizeof(parsed));
    memset(get_encrypted, '\0', sizeof(get_encrypted));
    // Save unencrypted data for later use.
    memcpy(get_encrypted, unencrypted, unencrypted_length);
    // Encrypt it.
    aes_encrypt(get_encrypted, key);
    memcpy(encrypted, get_encrypted, sizeof(encrypted));
    // Convert the hex into 0-F characters.
    for (i=0; i < sizeof(encrypted); i += 1) {
      HexToChar(encrypted[i], parsed, i * 2);
      checksum += parsed[i * 2] + parsed[i * 2 + 1];
    }
    
    // Calculate checksum 
    HexToChar(checksum, parsed, 32);
    // Add null character.
    parsed[34] = '\0';
    // Output encrypted string.
    printf("%s", parsed);
    return 0;
}