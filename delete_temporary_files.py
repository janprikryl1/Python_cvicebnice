from os import listdir, path, remove
from datetime import datetime, timedelta

for file in listdir("temporary_files"):
     if datetime.fromtimestamp(path.getmtime("temporary_files/"+file)) < datetime.today() - timedelta(days=1):
         remove("temporary_files/"+file)
