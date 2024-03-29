#setup
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.colors as clr
import matplotlib.patches as patches
from matplotlib.lines import Line2D
import matplotlib as mpl
import itertools as it
import argparse as ap
import re


parser = ap.ArgumentParser()
parser.add_argument('--sampleinfo', '-i', required=True, nargs='+',
                    help='sampleinfo file(s) that include, name, capture and genome')
parser.add_argument('--regions', '-r', required=True,
                    help='tsv file that includes, name and positions of regions of interest')
parser.add_argument('--igh', nargs=2, type=int,
                    help='start and end coordinate of the IGH locus')
parser.add_argument('--prefix', nargs='*', default=[''], 
                    help='prefix of samplenames that should be included. If left unspecified, all samples in the sampleinfo file are included.')
parser.add_argument('--capture', required=True, 
                    help='capture that should be included.')
parser.add_argument('--genome', required=True, 
                    help='genome that should be included.')
parser.add_argument('--regions1', '-r1', nargs='+', type=str,
                    help='first set of regions that will be intersected with the second set. Please always list from smallest to highest position.')
parser.add_argument('--regions2', '-r2', nargs='+', type=str,
                    help='second set of regions that will be intersected with the first set. Please always list from smallest to highest position.')
parser.add_argument('--selfInt', default=False, action='store_true',
                    help='specifiy if selfinteracting domains are also relevant. Eg capture - 3RR - 3RR.')
parser.add_argument('--noBinNorm', default=False, action='store_true',
                    help='specifiy if interactions should not be normalized by the number of bins in the interacting regions.')
parser.add_argument('--dir', default='../TriCplots',
                    help='specifiy the directory where the processed matrix can be found')
parser.add_argument('--mapq', default='', type=str,
                    help='specify the mapq value that was used in the pipeline if necessary for the filename in TriCplots')
args = parser.parse_args()


def get_colormap(colors, N = 256):
    return clr.LinearSegmentedColormap.from_list('custom', colors, N=N) if len(colors) > 1 else plt.get_cmap(*colors)


def get_bin_index(site, leftBound, rightBound, binsize):
    binbounds = np.arange(leftBound, rightBound, binsize)

    return len(np.where(binbounds < site)[0]) \
           if not (site < binbounds[0] or site > binbounds[-1]) \
           else None


def annotate_contacts(ax, 
                      contacts, 
                      r = 2.5, 
                      linestyle = '--', 
                      edgecolor = 'k',
                      mirror_horizontal = False):
    t = np.array([[1, 0.5], [-1, 0.5]]) if mirror_horizontal else np.array([[-1, 0.5], [1, 0.5]])
    
    for x, y in contacts:
        M = np.array([[x, y]])
        M = np.dot(M, t)
        ax.add_patch(patches.Circle((M[:, 1], M[:, 0]), 
                                    radius = r,
                                    fill = False,
                                    ls = linestyle,
                                    edgecolor = edgecolor,
                                    zorder = 3))

def sum_contacts(m, contact_regions, total_region, binsize, r = 0):
    idxs = []
    contact_sum = 0
    
    for contact_region in it.combinations(contact_regions, 2):
        region_idxs = []
        for start, end in contact_region:
            width = end - start
            
            if r and width < binsize * (2 * r + 1):
                mid = start + (end - start)//2
                midbin = get_bin_index(mid, total_region[0], total_region[1], binsize)
                startbin = midbin - r
                endbin = midbin + r + 1
                
            else:
                startbin = get_bin_index(start, total_region[0], total_region[1], binsize)
                endbin = get_bin_index(end, total_region[0], total_region[1], binsize)

            region_idxs.append((startbin, endbin))
            
        contact_sum += m[region_idxs[0][0]: region_idxs[0][1], region_idxs[1][0]: region_idxs[1][1]].sum()
        idxs.append(region_idxs)
    
    return contact_sum, idxs

igh = args.igh
binsize = 2000 if args.genome == 'hg38' else 1000
interacting_regions = pd.read_table(args.regions, sep='\t', names=['i', 0, 1], index_col='i').transpose()                 

samplenames = pd.read_csv(args.sampleinfo[0], 
                          sep = '\t', 
                          header = None, 
                          names = ['name', 'capture', 'genome'])
samplenames = samplenames.loc[(samplenames.capture == args.capture) & 
                              (samplenames.genome == args.genome) &
                                samplenames.name.str.contains(args.prefix[0])] \
                         .reset_index(drop = True)
if len(args.sampleinfo) > 1 and len(args.prefix) > 1:
    for i in range(1, len(args.sampleinfo)):
        samplenames2 = pd.read_csv(args.sampleinfo[i], 
                                sep = '\t', 
                                header = None, 
                                names = ['name', 'capture', 'genome'])
        samplenames2 = samplenames2.loc[(samplenames2.capture == args.capture) & 
                                    (samplenames2.genome == args.genome) &
                                    samplenames2.name.str.contains(args.prefix[i])] \
                                .reset_index(drop = True)
        samplenames = pd.concat([samplenames, samplenames2])

# reading matrices and setting capture bins to 0
mats = {}
cbinidx = get_bin_index(interacting_regions[args.capture][0], igh[0], igh[1], binsize)
for name in samplenames.name:
    m = np.loadtxt(f'{args.dir}/{name}{args.mapq}_TriC_interactions_{binsize}_RAW.tab',
                   delimiter = '\t')
    m[cbinidx, :] = 0
    m[:, cbinidx] = 0
    mats[name] = m



contactsums = []
for sample in samplenames.name:
    if sample[-1] == 'h': # Exeption for TriC14 (look at names)
        if sample[-2] == '0' or sample[-2] == '8':
            n = int(sample[-4])
            name = sample[:-5] 
            time = int(sample[-2:-1])
        else:
            n = int(sample[-5])
            name = sample[:-6] 
            time = int(sample[-3:-1])
    elif sample[-2] == '+': # Exeption for TriC12-13 because replicates 1 and 3 are already pooled for d0 samples (look at names)
        n = 1
        name = sample[:-7]
        time = sample[-6:-4]
    else: 
        spl = sample.split('_')
        name = '_'.join(spl[:-2])
        n = spl[-1]
        time = spl[-2]
    m = mats[sample]

    for region1, region2 in it.product(args.regions1, args.regions2):
        if interacting_regions[region1][0] > interacting_regions[region2][0]: 
            print(f'The interaction of region1 {region1} with region2 {region2} was not included because it is in wrong order. Please switch their places if the interaction should be included.')
            continue
        contact_sum, idxs = sum_contacts(m, 
                                         [interacting_regions[region1], 
                                          interacting_regions[region2]], 
                                         igh,
                                         binsize=binsize,
                                         r = 2)
        idxs = idxs[0]
        if not args.noBinNorm:
            region1_bincount = idxs[0][1] - idxs[0][0]
            region2_bincount = idxs[1][1] - idxs[1][0]
            squarebins = region1_bincount * region2_bincount
            pcontacts = contact_sum/squarebins #normalize by number of bins in reg. of interest (=squarebins)
        else: 
            pcontacts = contact_sum
        contactsums.append([name, n, time, region1, region2, pcontacts])


contactsums = pd.DataFrame(contactsums, columns = ['sample', 'replicate', 'treatment_time', 'region1', 'region2', 'pinteractions'])
if not args.selfInt: contactsums = contactsums[contactsums['region1'] != contactsums['region2']]
contactsums = contactsums.sort_values(['sample', 'replicate'])

regcomb = []
for i, row in contactsums.iterrows():
	regcomb.append(row['region1'] + ' - ' + row['region2'])
contactsums['regioncomb'] = regcomb
contactsums = contactsums.sort_index()

# return contactsums