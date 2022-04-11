def suma(*cisla):
    vysledek = 0
    for i in cisla:
        vysledek += i
    return vysledek


print(f'Suma: {suma(1,8,9,10,900,80,46,90,4*8)}')