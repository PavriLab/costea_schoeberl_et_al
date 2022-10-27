import bbi
import pandas as pd
import numpy as np

def GetMustacheLoops(
    filePath, 
    fdrFilter=None
):
    """
        From a loop file generated by mustache loop caller return a dataframe
        with columns:
        chrom1 | start1 | end1 | chrom2 | start2 | end2 | distance
        
        PARAMETERS
        ----------
        filePath: str 
            path to mustache loops file (.tsv)
        fdrFilter: float/None, default None 
            filter reads based on FDR (false detection rate), loops with 
            FDR < fdrFilter will be selected (optional)
        
        OUTPUT
        ------
        df : dataframe will columns given above
    """
    df = pd.read_csv(filePath, sep='\t')
    if fdrFilter != None and isinstance(fdrFilter, float):
        df = df.query(f"FDR <= {fdrFilter}", 
                      engine="python"
                     ).reset_index(drop = True)
    df = df.drop(["DETECTION_SCALE"], axis=1)
    df = df.rename(columns={"BIN1_CHR": "chrom1", 
                       "BIN1_START": "start1", 
                       "BIN1_END": "end1", 
                       "BIN2_CHROMOSOME": "chrom2", 
                       "BIN2_START": "start2", 
                       "BIN2_END": "end2"})
    df["distance"] = abs(df["start2"] - df["start1"]).astype(int)
    return df

def GetMacs2Peaks(
    filePath, 
    getBed=True,
    dropNonStandardChrom=True
):
    """
        Read the .xls file produced by MACS2 peaks finder and returns the peaks
        data as a pandas dataframe with columns
        chr|start|end|length|abs_summit|pileup|-log10(pvalue)|fold_enrichment\
        |-log10(qvalue)|name
        
        PARAMETERS
        ----------
        filePath: str
            path of the .xls file
        getBed: bool, default True
            to get bed like DataFrame or raw DataFrame
        dropNonStandardChrom: bool, default True
            drop non standard chromosomes
            (chromosomes with 'chr' in name and '_' not in name)
            
        OUTPUT
        ------
        peaks: pandas dataframe
    """
    peaks = pd.read_csv(filePath, comment='#', sep="\t")
    peaks = peaks.rename(columns={'chr': 'chrom'})
    if getBed:
        peaks = peaks[["chrom","start","end"]]
    if dropNonStandardChrom:
        peaks = peaks[peaks["chrom"].str.contains("chr") & ~peaks["chrom"].str.contains("_")]
    peaks = peaks.reset_index(drop=True)
    return peaks


if __name__ == "__main__":
    print(
    """
        This module contains functions to read from different genomics 
        files, such as, coverage from bigWigs, loops from mustache, and 
        chromosight, and peaks from Macs2.
    """
    )