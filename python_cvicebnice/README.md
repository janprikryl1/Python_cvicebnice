# Webová cvičebnice pro Python
## Jak importovat data?
### Data se ukládají do databáze mysql, všechna data z pythoncvicebnice.eu.pythonanywhere.com jsou v souboru data_dump.json
### - do databáze se importují po vytvoření databáze s názvem, který je napsán v pythoncvicebnice/settings.py na řádku 83 a migrací příkazy:
##### python.exe .\manage.py makemigrations
### a
##### python.exe .\manage.py migrate
### Data importujte příkazem:
##### python.exe manage.py loaddata data_dump.json

<br>

### Aby nedošlo k zaplnění kapacity úložiště kvůli možným souborům, které žáci mohou vytvořit, měl by se jednou denně spouštěn program delete_temporary_file.py
#### - spouštět by se mohl například pomocí crontabu