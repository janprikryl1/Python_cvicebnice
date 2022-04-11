soubor_pro_zapis = open("soubor.txt", "w")
soubor_pro_zapis.write("ahoj")
soubor_pro_zapis.close()

soubor_pro_cteni = open("soubor.txt", "r")
print(soubor_pro_cteni.read())
soubor_pro_cteni.close()