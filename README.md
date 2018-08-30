
# STAR
---

A [KBase](https://kbase.us) module generated by the [KBase SDK](https://github.com/kbase/kb_sdk).


This Module was initialized with a generated example App.  To compile and run the
example App implementation, run:

    cd STAR
    make          (required after making changes to $module_name.spec)
    kb-sdk test   (will require setting test user account credentials in test_local/test.cfg)

For more help on how to modify, register and deploy the example to KBase, see the
[KBase SDK documentation](https://github.com/kbase/kb_sdk).

[Reference website](https://github.com/alexdobin/STAR)
[Reference manual](https://github.com/alexdobin/STAR/blob/master/doc/STARmanual.pdf)

<h3>STAR 2.6.1a</h3>
<h4>Basic STAR workflow consists of 2 steps</h4>
<p>
  -  1. Generating genome indexes files

	- In this step user supplied the reference genome sequences (FASTA files) and annotations GTF file), from which STAR generate genome indexes that are utilized in the 2nd (mapping) step. The genome indexes are saved to disk and need only be generated once for each genome/annotation combination. A limited collection of STAR genomes is available from http://labshare.cshl.edu/shares/gingeraslab/www-data/dobin/STAR/STARgenomes/, however, it is strongly recommended that users generate their own genome indexes with most up-to-date assemblies and annotations.
	- Indexes generating is controlled by a variety of input parameters (Basic or Advanced options).
</p>
<p>
  -  2. Mapping reads to the genome-Align RNA-Seq Reads to the genome with STAR

	- In this step user supplies the genome files generated in the 1st step, as well as the RNA-seq reads (sequences) in the form of FASTA or FASTQ files. STAR maps the reads to the genome, and writes several output files, such as alignments (SAM/BAM), mapping summary statistics, splice junctions, unmapped reads, signal (wiggle) tracks etc. 
	- Output files: Log files, .sam files, .bam files, splice junctions, etc.
	STAR produces multiple output files. All files have standard name, however, you can change the file prefixes using --outFileNamePrefix /path/to/output/dir/prefix. By default, this parameter is ./, i.e. all output files are written in the current directory. 

	- Mapping is controlled by a variety of input parameters (Basic or Advanced options).
</p>
<p>
  -  STAR command line has the following format:

	- STAR --option1-name option1-value(s)--option2-name option2-value(s) ...
	If an option can accept multiple values, they are separated by spaces, and in a few cases - by commas.
</p>

<h4>The basic options to generate genome indexes are as follows</h4>
<p>

    --runThreadN NumberOfThreads
    --runMode genomeGenerate
    --genomeDir /path/to/genomeDir
    --genomeFastaFiles /path/to/genome/fasta1 /path/to/genome/fasta2 ...
    --sjdbGTFfile /path/to/annotations.gtf
    --sjdbOverhang ReadLength-1

   i.e., 
   STAR  --runMode genomeGenerate --runThreadN <# cpus> --genomeDir <genome output directory> --genomeFastaFiles <input Genome FASTA file>

    e.g.,
    root@651068a1ff75:/kb/module# STAR --genomeDir /kb/module/STAR_genome_dir/ --runMode genomeGenerate --runThreadN 4 --genomeFastaFiles /kb/module/work/tmp/star_test_assembly.fa 
    Jun 20 19:57:09 ..... started STAR run
    Jun 20 19:57:09 ... starting to generate Genome files
    Jun 20 19:57:09 ... starting to sort Suffix Array. This may take a long time...
    Jun 20 19:57:09 ... sorting Suffix Array chunks and saving them to disk...
    Jun 20 19:57:10 ... loading chunks from disk, packing SA...
    Jun 20 19:57:10 ... finished generating suffix array
    Jun 20 19:57:10 ... generating Suffix Array index
    Jun 20 19:57:13 ... completed Suffix Array index
    Jun 20 19:57:13 ... writing Genome to disk ...
    Jun 20 19:57:13 ... writing Suffix Array to disk ...
    Jun 20 19:57:13 ... writing SAindex to disk
    Jun 20 19:57:17 ..... finished successfully

    root@651068a1ff75:/kb/module# ls -la STAR_genome_dir/
    total 1530272
    drwxrwxrwx  2 root root       4096 Jun 20 19:57 .
    drwxrwxrwx 35 root root       4096 Jun 20 19:57 ..
    -rw-r--r--  1 root root     262144 Jun 20 19:57 Genome
    -rw-r--r--  1 root root     825003 Jun 20 19:57 SA
    -rw-r--r--  1 root root 1565873619 Jun 20 19:57 SAindex
    -rw-r--r--  1 root root          7 Jun 20 19:57 chrLength.txt
    -rw-r--r--  1 root root          9 Jun 20 19:57 chrName.txt
    -rw-r--r--  1 root root         16 Jun 20 19:57 chrNameLength.txt
    -rw-r--r--  1 root root          9 Jun 20 19:57 chrStart.txt
    -rw-r--r--  1 root root        527 Jun 20 19:57 genomeParameters.txt
</p>


<h4>The basic options to run a mapping job are as follows</h4>
<p>

    --runThreadN NumberOfThreads
    --genomeDir /path/to/genomeDir
    --readFilesIn /path/to/read1 [/path/to/read2 ]

  i.e., 
  STAR --genomeDir <Directory with the Genome Index>  --runThreadN <# cpus> --readFilesIn <FASTQ file> --outFileNamePrefix <OutputPrefix>
  
    e.g.,
    root@651068a1ff75:/kb/module# STAR --genomeDir /kb/module/STAR_genome_dir/ --runMode alignReads --runThreadN 4 --readFilesIn /kb/module/work/tmp/Arabidopsis_thaliana.TAIR10.dna.toplevel.fa --outFileNamePrefix /kb/module/work/tmp/STAR_output_dir/STARtest_
    Jun 20 19:57:32 ..... started STAR run
    Jun 20 19:57:32 ..... loading genome
    Jun 20 19:57:40 ..... started mapping
    Jun 20 19:57:41 ..... finished successfully

    e.g.(for paried-end data),
    qzhang@e6b9c1a37b42:/kb/module$ STAR --genomeDir STAR_genome_dir/  --runThreadN 4 --readFilesIn testReads/small.forward.fq testReads/small.reverse.fq --outFileNamePrefix Experiment1Star_paired
  
    May 31 23:23:27 ..... started STAR run
    May 31 23:23:27 ..... loading genome
    May 31 23:23:28 ..... started mapping
    May 31 23:23:32 ..... finished successfully
</p>

<h4>STAR will create several output files</h4>
<p>

    root@651068a1ff75:/kb/module# ls -la work/tmp/STAR_output_dir/
    total 28
    drwxr-xr-x  7 root root   238 Jun 20 19:57 .
    drwxr-xr-x 18 root root   612 Jun 20 19:37 ..
    -rw-r--r--  1 root root   561 Jun 20 19:57 STARtest_Aligned.out.sam
    -rw-r--r--  1 root root  1807 Jun 20 19:57 STARtest_Log.final.out
    -rw-r--r--  1 root root 15718 Jun 20 19:57 STARtest_Log.out
    -rw-r--r--  1 root root   246 Jun 20 19:57 STARtest_Log.progress.out
    -rw-r--r--  1 root root     0 Jun 20 19:57 STARtest_SJ.out.tab

The most important of which is the "*.Aligned.out.sam". The default output is a SAM file.
</p>

