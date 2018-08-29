"""
--modified based on the same file in kb_hisat2
Utility functions to fetch files from various Workspace object types.
Depends on the more general util.py that's here, too.
"""
import re
import fileinput
import os.path
import sys
from pprint import pprint
from SetAPI.SetAPIClient import SetAPI
from AssemblyUtil.AssemblyUtilClient import AssemblyUtil
from ReadsUtils.ReadsUtilsClient import ReadsUtils
from Workspace.WorkspaceClient import Workspace


def fetch_fasta_from_genome(genome_ref, ws_url, callback_url):
    """
    Returns an assembly or contigset as FASTA.
    """
    if not check_ref_type(genome_ref, ['KBaseGenomes.Genome'], ws_url):
        raise ValueError("The given genome_ref {} is not a KBaseGenomes.Genome type!")
    # test if genome references an assembly type
    # do get_objects2 without data. get list of refs
    ws = Workspace(ws_url)
    genome_obj_info = ws.get_objects2({
        'objects': [{'ref': genome_ref}],
        'no_data': 1
    })
    # get the list of genome refs from the returned info.
    # if there are no refs (or something funky with the return), this will be an empty list.
    # this WILL fail if data is an empty list. But it shouldn't be, and we know because
    # we have a real genome reference, or get_objects2 would fail.
    genome_obj_refs = genome_obj_info.get('data', [{}])[0].get('refs', [])

    # see which of those are of an appropriate type (ContigSet or Assembly), if any.
    assembly_ref = list()
    ref_params = [{'ref': x} for x in genome_obj_refs]
    ref_info = ws.get_object_info3({'objects': ref_params})
    for idx, info in enumerate(ref_info.get('infos')):
        if "KBaseGenomeAnnotations.Assembly" in info[2] or "KBaseGenomes.ContigSet" in info[2]:
            assembly_ref.append(";".join(ref_info.get('paths')[idx]))

    if len(assembly_ref) == 1:
        return fetch_fasta_from_assembly(assembly_ref[0], ws_url, callback_url)
    else:
        raise ValueError("Multiple assemblies found associated with the given genome ref {}! "
                         "Unable to continue.")


def fetch_fasta_from_assembly(assembly_ref, ws_url, callback_url):
    """
    From an assembly or contigset, this uses a data file util to build a FASTA file and return the
    path to it.
    """
    allowed_types = ['KBaseFile.Assembly',
                     'KBaseGenomeAnnotations.Assembly',
                     'KBaseGenomes.ContigSet']
    if not check_ref_type(assembly_ref, allowed_types, ws_url):
        raise ValueError("The reference {} cannot be used to fetch a FASTA file".format(assembly_ref))
    au = AssemblyUtil(callback_url)
    return au.get_assembly_as_fasta({'ref': assembly_ref})


def fetch_fasta_from_object(ref, ws_url, callback_url):
    """
    From the object given in ref, if it's either a KBaseGenomes.Genome or a
    KBaseGenomeAnnotations.Assembly, or a KBaseGenomes.ContigSet, this will download and return
    the path to a FASTA file made from its sequence.
    """
    obj_type = get_object_type(ref, ws_url)
    if "KBaseGenomes.Genome" in obj_type:
        return fetch_fasta_from_genome(ref, ws_url, callback_url)
    elif ("KBaseGenomeAnnotations.Assembly" in obj_type or 
          "KBaseGenomeAnnotations.Assembly-5.0" in obj_type or 
          "KBaseGenomes.ContigSet" in obj_type):
        return fetch_fasta_from_assembly(ref, ws_url, callback_url)
    else:
        raise ValueError("Unable to fetch a FASTA file from an object of type {}".format(obj_type))


def fetch_reads_refs_from_sampleset(ref, ws_url, callback_url, params):
    """
    From the given object ref, return a list of all reads objects that are a part of that
    object. E.g., if ref is a ReadsSet, return a list of all PairedEndLibrary or SingleEndLibrary
    refs that are a member of that ReadsSet. This is returned as a list of dictionaries as follows:
    {
        "ref": reads object reference,
        "condition": condition string associated with that reads object
    }
    The only one required is "ref", all other keys may or may not be present, based on the reads
    object or object type in initial ref variable. E.g. a RNASeqSampleSet might have condition info
    for each reads object, but a single PairedEndLibrary may not have that info.
    If ref is already a Reads library, just returns a list with ref as a single element.
    """
    obj_type = get_object_type(ref, ws_url)
    ws = Workspace(ws_url)
    refs = list()
    refs_for_ws_info = list()
    if "KBaseSets.ReadsSet" in obj_type:
        print("Looking up reads references in ReadsSet object")
        set_client = SetAPI(callback_url)
        reads_set = set_client.get_reads_set_v1({
            "ref": ref,
            "include_item_info": 0
        })
        for reads in reads_set["data"]["items"]:
            refs.append({
                "ref": reads["ref"],
                "condition": reads["label"]
            })
            refs_for_ws_info.append({'ref': reads['ref']})
    elif "KBaseRNASeq.RNASeqSampleSet" in obj_type:
        print("Looking up reads references in RNASeqSampleSet object")
        sample_set = ws.get_objects2({"objects": [{"ref": ref}]})["data"][0]["data"]
        for i in range(len(sample_set["sample_ids"])):
            refs.append({
                "ref": sample_set["sample_ids"][i],
                "condition": sample_set["condition"][i]
            })
            refs_for_ws_info.append({'ref': sample_set['sample_ids'][i]})
    elif ("KBaseAssembly.SingleEndLibrary" in obj_type or
          "KBaseFile.SingleEndLibrary" in obj_type or
          "KBaseFile.SingleEndLibrary-2.0" in obj_type or
          "KBaseFile.SingleEndLibrary-2.1" in obj_type or
          "KBaseAssembly.PairedEndLibrary" in obj_type or
          "KBaseFile.PairedEndLibrary" in obj_type or
          "KBaseFile.PairedEndLibrary-2.0" in obj_type or
          "KBaseFile.PairedEndLibrary-2.1" in obj_type):
        refs.append({"ref": ref})
        refs_for_ws_info.append({'ref': ref})
    else:
        raise ValueError("Unable to fetch reads reference from object {} "
                         "which is a {}".format(ref, obj_type))

    # get object info so we can name things properly
    infos = ws.get_object_info3({'objects': refs_for_ws_info})['infos']

    name_ext = '_alignment'
    if ('alignment_suffix' in params
            and params['alignment_suffix'] is not None):
        ext = params['alignment_suffix'].replace(' ', '')
        if ext:
            name_ext = ext

    unique_names = get_unique_names(infos)
    for k in range(0, len(refs)):
        refs[k]['info'] = infos[k]
        name = unique_names[k] + name_ext
        refs[k]['alignment_output_name'] = name

    return refs


def get_unique_names(infos):
    unique_name_lookup = {}
    names = {}
    for k in range(0, len(infos)):
        name = infos[k][1]
        if name not in unique_name_lookup:
            unique_name_lookup[name] = 1
        else:
            unique_name_lookup[name] += 1
            name = name + '_' + str(unique_name_lookup[name])
        names[k] = name
    return names


def fetch_reads_from_reference(ref, callback_url):
    """
    Fetch a FASTQ file (or 2 for paired-end) from a reads reference.
    Returns the following structure:
    {
        "style": "paired", "single", or "interleaved",
        "file_fwd": path_to_file,
        "name": name of the reads,
        "file_rev": path_to_file, only if paired end,
        "object_ref": reads reference for downstream convenience.
    }
    """
    try:
        print("Fetching reads from object {}".format(ref))
        reads_client = ReadsUtils(callback_url)
        reads_dl = reads_client.download_reads({
            "read_libraries": [ref],
            "interleaved": "false"
        })
        pprint(reads_dl)
        reads_files = reads_dl['files'][ref]['files']
        ret_reads = {
            "object_ref": ref,
            "style": reads_files["type"],
            "file_fwd": reads_files["fwd"],
            "name": reads_files["fwd_name"]
        }
        if reads_files.get("rev", None) is not None:
            ret_reads["file_rev"] = reads_files["rev"]
        return ret_reads
    except:
        print("Unable to fetch a file from expected reads object {}".format(ref))
        raise


def valid_string(s, is_ref=False):
    is_valid = isinstance(s, basestring) and len(s.strip()) > 0
    if is_valid and is_ref:
        is_valid = check_reference(s)
    return is_valid


def check_reference(ref):
    """
    Tests the given ref string to make sure it conforms to the expected
    object reference format. Returns True if it passes, False otherwise.
    """
    obj_ref_regex = re.compile("^(?P<wsid>\d+)\/(?P<objid>\d+)(\/(?P<ver>\d+))?$")
    ref_path = ref.strip().split(";")
    for step in ref_path:
        if not obj_ref_regex.match(step):
            return False
    return True


def check_ref_type(ref, allowed_types, ws_url):
    """
    Validates the object type of ref against the list of allowed types. If it passes, this
    returns True, otherwise False.
    Really, all this does is verify that at least one of the strings in allowed_types is
    a substring of the ref object type name.
    Ex1:
    ref = "KBaseGenomes.Genome-4.0"
    allowed_types = ["assembly", "KBaseFile.Assembly"]
    returns False
    Ex2:
    ref = "KBaseGenomes.Genome-4.0"
    allowed_types = ["assembly", "genome"]
    returns True
    """
    obj_type = get_object_type(ref, ws_url).lower()
    for t in allowed_types:
        if t.lower() in obj_type:
            return True
    return False


def get_object_type(ref, ws_url):
    """
    Fetches and returns the typed object name of ref from the given workspace url.
    If that object doesn't exist, or there's another Workspace error, this raises a
    RuntimeError exception.
    """
    ws = Workspace(ws_url)
    info = ws.get_object_info3({'objects': [{'ref': ref}]})
    obj_info = info.get('infos', [[]])[0]
    if len(obj_info) == 0:
        raise RuntimeError("An error occurred while fetching type info from the Workspace. "
                           "No information returned for reference {}".format(ref))
    return obj_info[2]


def extract_geneCount_matrix(geneCount_filenames, output_dir):
    """
    extract_expression_matrix: Grind through the ReadsPerGene.out.tab  files and output a single
    TSV file that shows the counts for each gene id across the input files

    STAR outputs read counts per gene into
    ReadsPerGene.out.table with 4 columns which correspond to different strandedness options--
    column 1--gene ID
    column 2--counts for unstranded RNA-seq
    column 3--counts for the 1st read strand aligned with RNA (htseq-count option -s yes)
    column 4--counts for the 2nd read strand aligned with RNA (htseq-count option -s reverse)
    Select the output according to the strandedness of your data. Note, that if you have stranded
    data and choose one of the columns 3 or 4, the other column (4 or 3) will give you the
    count of antisense reads. With --quantMode TranscriptomeSAM GeneCounts, and get both the
    Aligned.toTranscriptome.out.bam and ReadsPerGene.out.tab outputs.

    Assuming each of the geneCount_filenames comes with its upper one level parent,
    i.e., in the pattern of '[reads_name]/ReadsPerGene.out.tab' as the way STAR outputs
    """
    print "\nExtracting geneCount results from these files:"
    pprint(geneCount_filenames)

    counts = dict()

    gene_count_file_paths = [os.path.join(output_dir, gcf) for gcf in geneCount_filenames]

    fin = fileinput.input(files=set(gene_count_file_paths))
    for line in fin:
        if not line or line.startswith("N_"):
            continue
        line_arr = line.split("\t")
        try:
            counts[line_arr[0]][fileinput.filename()] = line_arr[1]
        except KeyError:
            counts[line_arr[0]] = dict()
            counts[line_arr[0]][fileinput.filename()] = line_arr[1]
    fin.close()

    output_filename = os.path.join(output_dir, 'ReadsPerGene_matrix.tsv')
    fout = open(output_filename, 'w')
    # print "feature_ids\t", "\t".join([os.path.dirname(fn) for fn in geneCount_filenames])
    fout.write("feature_ids\t" + "\t".join(
                            [os.path.dirname(fn) for fn in geneCount_filenames]) + "\n")
    for fid in sorted(counts.iterkeys()):
        counts2 = [counts[fid][filename] for filename in gene_count_file_paths]
        # print fid, "\t", "\t".join(counts2)
        fout.write(str(fid) + "\t" + "\t".join(counts2) + "\n")

    fout.close()
    return output_filename

