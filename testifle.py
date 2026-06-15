import glob
count = 0
for file in glob.glob("articletxt/*.txt"):
    count+=1

files = glob.glob("articletxt/*.txt")
id_list = []
for file in files:
    id = int(file.replace('articletxt/','').replace('.txt',''))
    id_list.append(id)
    print(id_list)