AES128

// receive data 
GatewayType=D0 91 22 69 6B E5 51 AC AE A5 3D 1C B5 CF 15 75    << must be transfer to Hex
/GatewayID=DF BB 98 B2 0C F1 7C C7 74 4A 15 EC 60 E0 83 00
/DeviceType=DD 91 22 69 6B E5 51 AC AE A5 3D 1C B5 CF 15 75
/DeviceID=7F EC 09 C6 CA 7D 68 B0 ED 7E 71 88 70 AE 46 40
/ExtensionID=A1 BC 2C 25 A9 73 86 E8 F4 1F D2 54 F6 3A E5 84
/Year=3D 75 AF 12 F7 EA B4 67 64 B7 25 CE 95 DB EB A9
/Month=2D FA 41 8C BE C7 8F 9D 5E 53 5A 1D C2 56 11 30 
/Day=E3 60 BD DF 07 4F ED CA DE 0B 63 B2 DD EA CC 77
/Hour=2D FA 41 8C BE C7 8F 9D 5E 53 5A 1D C2 56 11 30
/Minute=C4 A4 46 74 3A A5 26 B2 46 BF DB B3 7E 5F 69 69
/Second=A1 BC 2C 25 A9 73 86 E8 F4 1F D2 54 F6 3A E5 84
/DataType=AD FF 45 49 07 A2 98 3D 86 8D 0C D8 95 DB 97 A1
/Value1=B2 95 C9 4A 75 FB D9 2E 85 2E 29 2C 36 95 CE 99
/Value2=E0 5E 99 08 31 A3 98 20 AC B4 D5 DC 45 DE BB E9
/Value3=9C 62 8F 86 34 DD 64 02 22 20 F4 75 F0 D4 71 AD
/Value4=B3 C2 06 1D 5A 80 F0 FC 9B FF 0F 06 12 65 65 CF
/Value5= B3 C2 06 1D 5A 80 F0 FC 9B FF 0F 06 12 65 65 CF
/Value6= B3 C2 06 1D 5A 80 F0 FC 9B FF 0F 06 12 65 65 CF


#include "aes.h"

void decrypt(char *src,unsigned char *return_str)
{
	unsigned char *key ="71B6715044B182AA233E3C1ECFB8E6AB";          // encrypt Key 	
	memset(return_str,0x00,sizeof(return_str));
	strcpy((char*)return_str,src);
	aes_decrypt(return_str,key);
}
1: must be the transfer the data to Hex
  D0 91 22 69 6B E5 51 AC AE A5 3D 1C B5 CF 15 75
 0xD0 ,0x91 .......0x75
2: put hex data into src than call  decrypt(src_str,decrypt_str);
		
