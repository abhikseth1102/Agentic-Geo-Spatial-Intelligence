with open('data/AIS_2023_08_28.csv', 'r') as fin, open('data/AIS_Raw_Excel_Friendly.csv', 'w') as fout:
    for i, line in enumerate(fin):
        fout.write(line)
        if i >= 500000:
            break
print('Done cutting 500,000 rows!')
