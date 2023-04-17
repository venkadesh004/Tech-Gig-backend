with open("requirements.txt", "r") as reader:
    l = []
    data = reader.readlines()
    for i in data:
        # print(i) 
        string = ""
        for j in i:
            if j == "=":
                break
            else:
                string += j
        l.append(string)

print(l)

with open("requirements.txt", "w+") as writer:
    for i in l:
        print(i)
        writer.write(i)
        writer.write("\n")