cislo = input("Zadejte celé číslo: ")
try:
    cislo = int(cislo)
except:
    print("chyba")
else:
    print(cislo)