import argparse as ap
import matplotlib.pyplot as plt
import logging

def readLines(file, identifiers, split = False):
    '''
    reads all lines in the file starting with the given identifier

    :param file:        path to the file from which to read
    :param identifier:  iterable containing line identifiers
    :param split:       if True splits the line at tabs and extracts the read count

    :return:            list of strings containing the read lines
    '''
    with open(file, 'r') as f:
        d = {k: [] for k in identifiers}
        for line in f:
            try:
                k, l = line.rstrip().split(maxsplit = 1)

            except ValueError:
                continue

            try:
                if not split:
                    d[k].append(l)

                else:
                    d[k].append(int(l.split('\t')[-1]))

            except KeyError:
                continue

    return d


logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
parser = ap.ArgumentParser()
parser.add_argument('-f6', '--F6fullreport', nargs = '+',
                    help = 'space-separated list of full combined report file located in the F6 folder')
parser.add_argument('-f3f', '--F3fullreportFlashed', nargs = '+',
                    help = 'space-separated list of full report of flashed reads located in the F3 folder')
parser.add_argument('-f3n', '--F3fullreportNonflashed', nargs = '+',
                    help = 'space-separated list of full report of nonflashed reads located in the F3 folder')
parser.add_argument('-rn', '--readNum', nargs = '+', type = int,
                    help = 'space-separated list of total number of read pairs')
parser.add_argument('-s', '--sampleNames', nargs = '+',
                    help = 'space-separated list of sample names corresponding to input files')
parser.add_argument('-o', '--outFile', required = True,
                    help = 'file to save the plot to')
args = parser.parse_args()

if not all(len(a) == len(args.F6fullreport) for a in [args.F3fullreportFlashed,
                                                      args.F3fullreportNonflashed,
                                                      args.readNum,
                                                      args.sampleNames]):
    raise Exception('all input parameters must have the same number of arguments')


fnfkeys = {'11' : 'number of reads',
           '11b': 'number of reads with capture',
           '11c': 'number of reads with capture and reporter',
           '11d': 'number of reads without capture or reporter',
           '11f': 'number of single-capture reads',
           '16' : 'number of deduplicated reads'}

ckeys = {'16'  : 'total deduplicated reads',
         '16bb': 'number of reads with n contacts'}

separate, combined = {}, {}
for s, f, nf, c in zip(args.sampleNames, args.F3fullreportFlashed, args.F3fullreportNonflashed, args.F6fullreport):
    separate[s] = {'f': readLines(f, fnfkeys, split = True), 'nf': readLines(nf, fnfkeys, split = True)}
    combined[s] = readLines(c, ckeys)

fig, axs = plt.subplots(1, 2)
ax1, ax2 = axs

# generate overall barchart
pos = list(range(1, len(args.readNum) + 1))
ax1.bar(pos,  [100] * len(args.readNum), label = 'total readpairs', color = 'dimgrey')
for k, label, color in zip(['11', '11b', '11c', '16'],
                           ['aligned readpairs', 'capture only readpairs', 'capture and reporter readpairs', 'unique readpairs'],
                           ['paleturquoise', 'royalblue', 'limegreen', 'darkgreen']):
    v = []
    for s, rn in zip(args.sampleNames, args.readNum):
        v.append((sum(separate[s]['f'][k]) + sum(separate[s]['nf'][k]))/rn*100)

    ax1.bar(pos, v, label = label, color = color)

ax1.set_title('alignment and filter statistics')
ax1.legend()
ax1.set_xticks(pos)
ax1.set_xticklabels(args.sampleNames, rotation = 45, ha = 'right')


twoway, threeway, nway = [], [], []
for s in args.sampleNames:
    twoway.append(0)
    threeway.append(0)
    nway.append(0)

    for l in combined[s]['16bb']:
        l = l.split('\t')

        if 'having 1' in l[0]:
            twoway[-1] += int(l[1])

        elif 'having 2' in l[0]:
            threeway[-1] += int(l[1])

        else:
            nway[-1] += int(l[1])

bottom = [0] * len(args.sampleNames)
for w, label, color in zip([nway, threeway, twoway], ['>3way', '3way', '2way'], ['darkgreen', 'limegreen', 'dimgrey']):
    ax2.bar(pos, w, bottom = bottom, label = label, color = color)
    bottom = [i + j for i, j in zip(w, bottom)]

ax2.set_title('n-way read fractions')
ax2.legend()
ax2.set_xticks(pos)
ax2.set_xticklabels(args.sampleNames, rotation = 45, ha = 'right')


fig.set_figwidth(12)
fig.set_figheight(5)
fig.tight_layout()
fig.savefig(args.outFile)