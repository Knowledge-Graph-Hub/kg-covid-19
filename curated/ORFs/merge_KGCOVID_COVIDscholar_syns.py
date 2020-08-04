

KGCOVID_syns_p = "uniprot_sars-cov-2.gpi"
COVIDscholar_syns_p = "synonyms_list_COVIDscholar.txt"

with open(KGCOVID_syns_p, 'r') as fk:
    count = 0
    # skip header

    line = fk.readline()
    while line.find("!") == 0:
        line = fk.readline()
        print(line)

    countORFs = 0
    countORFs_total = 0
    while line:
        #print(line)
        line_split = line.split("\t")
        #print(len(line_split))
        cur_gene_name = line_split[2]
        cur_syns = line_split[4].split("|")
        print(cur_syns)
        countORFs_total = countORFs_total + 1
        #print(cur_gene_name)
        found = 0
        with open(COVIDscholar_syns_p, 'r') as fc:
            linec = fc.readline()
            while linec:#and found == 0:
                linec_split = linec.split(", ")
                #print(linec_split)
                if cur_gene_name in linec_split:
                    #print("found")
                    found = 1
                    countORFs = countORFs + 1

                    for syn in cur_syns:
                        if syn in linec_split:
                            print("found kg/cs: "+syn)
                        else:
                            print("not found in cs: " + syn)

                    for synin in linec_split:
                        if synin in cur_syns:
                            pass
                            #print("found cs :" + synin)
                        else:
                            print("not found in kg: " + synin)


                    break
                linec = fc.readline()

        #print("found "+str(found))
        if found == 0:
            print("did not find "+cur_gene_name)
        line = fk.readline()

    print('{:d} {:d}'.format(countORFs, countORFs_total) )#countORFs+" / "+countORFs_total)

