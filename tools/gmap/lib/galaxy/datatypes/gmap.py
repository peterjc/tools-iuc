"""
GMAP indexes
"""
import logging
import os
import os.path
import re
import sys
from galaxy.datatypes import data
from galaxy.datatypes.data import Text
from galaxy import util
from galaxy.datatypes.metadata import MetadataElement

log = logging.getLogger(__name__)


class GmapDB(Text):

    """
    A GMAP DB for indexes
    """
    MetadataElement(name="db_name", desc="The db name for this index set",
                    default='unknown', set_in_upload=True, readonly=True)
    MetadataElement(
        name="chromosomes", desc="The chromosomes or contigs", no_value=[], readonly=False)
    MetadataElement(
        name="circular", desc="cirular chromosomes", no_value=[], readonly=False)
    MetadataElement(
        name="chromlength", desc="Chromosome lengths", no_value=[], readonly=False)
    MetadataElement(name="basesize", default="12",
                    desc="The basesize for offsetscomp", visible=True, readonly=True)
    MetadataElement(name="kmers", desc="The kmer sizes for indexes",
                    visible=True, no_value=[''], readonly=True)
    MetadataElement(name="map_dir", desc="The maps directory",
                    default='unknown', set_in_upload=True, readonly=True)
    MetadataElement(name="maps", desc="The names of maps stored for this gmap gmapdb",
                    visible=True, no_value=[''], readonly=True)
    MetadataElement(name="snps", desc="The names of SNP indexes stored for this gmapdb",
                    visible=True, no_value=[''], readonly=True)
    MetadataElement(name="cmet", default=False,
                    desc="Has a cmet index", visible=True, readonly=True)
    MetadataElement(name="atoi", default=False,
                    desc="Has a atoi index", visible=True, readonly=True)

    file_ext = 'gmapdb'
    is_binary = True
    composite_type = 'auto_primary_file'
    allow_datatype_change = False

    def generate_primary_file(self, dataset=None):
        """
        This is called only at upload to write the html file
        cannot rename the datasets here - they come with the default unfortunately
        """
        return '<html><head></head><body>AutoGenerated Primary File for Composite Dataset</body></html>'

    def regenerate_primary_file(self, dataset):
        """
        cannot do this until we are setting metadata
        """
        bn = dataset.metadata.db_name
        log.info("GmapDB regenerate_primary_file %s" % (bn))
        rval = []
        rval.append("GMAPDB: %s" % dataset.metadata.db_name)
        if dataset.metadata.chromosomes:
            rval.append("chromosomes: %s" % dataset.metadata.chromosomes)
        if dataset.metadata.chromlength and len(dataset.metadata.chromlength) == len(dataset.metadata.chromosomes):
            rval.append('chrom\tlength')
            for i, name in enumerate(dataset.metadata.chromosomes):
                rval.append(
                    '%s\t%d' % (dataset.metadata.chromosomes[i], dataset.metadata.chromlength[i]))
        if dataset.metadata.circular:
            rval.append("circular: %s" % dataset.metadata.circular)
        if dataset.metadata.kmers:
            rval.append("kmers: %s" % dataset.metadata.kmers)
        rval.append("cmetindex: %s  atoiindex: %s" %
                    (dataset.metadata.cmet, dataset.metadata.atoi))
        if dataset.metadata.maps and len(dataset.metadata.maps) > 0:
            rval.append('Maps:')
            for i, name in enumerate(dataset.metadata.maps):
                if name.strip() != '':
                    rval.append(' %s' % name)
        f = open(dataset.file_name, 'w')
        f.write("\n".join(rval))
        f.write('\n')
        f.close()

    def set_peek(self, dataset, is_multi_byte=False):
        log.info("GmapDB set_peek %s" % (dataset))
        if not dataset.dataset.purged:
            dataset.peek = "GMAPDB index %s\n chroms %s\n kmers %s cmet %s atoi %s\n maps %s" % (
                dataset.metadata.db_name, dataset.metadata.chromosomes, dataset.metadata.kmers, dataset.metadata.cmet, dataset.metadata.atoi, dataset.metadata.maps)
            dataset.blurb = "GMAPDB %s" % (dataset.metadata.db_name)
        else:
            dataset.peek = 'file does not exist'
            dataset.blurb = 'file purged from disk'

    def display_peek(self, dataset):
        try:
            return dataset.peek
        except:
            return "GMAP index file"

    def sniff(self, filename):
        return False

    def set_meta(self, dataset, overwrite=True, **kwd):
        """
        extra_files_path/<db_name>/GRCh37_19
        extra_files_path/<db_name>/GRCh37_19/GRCh37_19.a2iag12123offsetscomp
        extra_files_path/<db_name>/GRCh37_19/GRCh37_19.a2iag123positions
        extra_files_path/<db_name>/GRCh37_19/GRCh37_19.a2itc12123offsetscomp
        extra_files_path/<db_name>/GRCh37_19/GRCh37_19.a2itc123positions
        extra_files_path/<db_name>/GRCh37_19/GRCh37_19.chromosome
        extra_files_path/<db_name>/GRCh37_19/GRCh37_19.chromosome.iit
        extra_files_path/<db_name>/GRCh37_19/GRCh37_19.chrsubset
        extra_files_path/<db_name>/GRCh37_19/GRCh37_19.contig
        extra_files_path/<db_name>/GRCh37_19/GRCh37_19.contig.iit
        extra_files_path/<db_name>/GRCh37_19/GRCh37_19.genomecomp
        extra_files_path/<db_name>/GRCh37_19/GRCh37_19.maps
        extra_files_path/<db_name>/GRCh37_19/GRCh37_19.metct12123offsetscomp
        extra_files_path/<db_name>/GRCh37_19/GRCh37_19.metct123positions
        extra_files_path/<db_name>/GRCh37_19/GRCh37_19.metga12123offsetscomp
        extra_files_path/<db_name>/GRCh37_19/GRCh37_19.metga123positions
        extra_files_path/<db_name>/GRCh37_19/GRCh37_19.ref12123offsetscomp
        extra_files_path/<db_name>/GRCh37_19/GRCh37_19.ref123positions
        extra_files_path/<db_name>/GRCh37_19/GRCh37_19.version

        Expecting:
        extra_files_path/<db_name>/db_name>.ref<basesize><kmer>3<index>
        extra_files_path/db_name/db_name.ref1[2345]1[2345]3offsetscomp
        extra_files_path/db_name/db_name.ref1[2345]1[2345]3positions
        extra_files_path/db_name/db_name.ref1[2345]1[2345]3gammaptrs
        index maps:
        extra_files_path/db_name/db_name.maps/*.iit
        """
        log.info("GmapDB set_meta %s %s" % (dataset, dataset.extra_files_path))
        chrom_pat = '^(.+).chromosome$'
        # pat = '(.*)\.((ref)|(met)[atgc][atgc]|(a2i)[atgc][atgc])((\d\d)(\d\d))?3positions(\.(.+))?'
        pat = '(.*)\.((ref)|(met)[atgc][atgc]|(a2i)[atgc][atgc])((\d\d)(\d\d))?(\d)(offsetscomp)'
        efp = dataset.extra_files_path
        flist = os.listdir(efp)
        for i, fname in enumerate(flist):
            log.info("GmapDB set_meta %s %s" % (i, fname))
            fpath = os.path.join(efp, fname)
            if os.path.isdir(fpath):
                ilist = os.listdir(fpath)
                # kmers = {'':'default'} # HACK  '' empty key  added so user
                # has default choice when selecting kmer from metadata
                kmers = dict()
                for j, iname in enumerate(ilist):
                    log.info("GmapDB set_meta file %s %s" % (j, iname))
                    ipath = os.path.join(fpath, iname)
                    print >> sys.stderr, "GmapDB set_meta file %s %s %s" % (
                        j, iname, ipath)
                    if os.path.isdir(ipath):  # find maps
                        dataset.metadata.map_dir = iname
                        maps = []
                        snps = []
                        for mapfile in os.listdir(ipath):
                            mapname = mapfile.replace('.iit', '')
                            log.info("GmapDB set_meta map %s %s" %
                                     (mapname, mapfile))
                            print >> sys.stderr, "GmapDB set_meta map %s %s " % (
                                mapname, mapfile)
                            maps.append(mapname)
                            if mapname.find('snp') >= 0:
                                snps.append(mapname)
                        if len(maps) > 0:
                            dataset.metadata.maps = maps
                        if len(snps) > 0:
                            dataset.metadata.snps = snps
                    else:
                        m = re.match(chrom_pat, iname)
                        if m and len(m.groups()) == 1:
                            dataset.metadata.db_name = m.groups()[0]
                            print >> sys.stderr, "GmapDB set_meta file %s %s %s" % (
                                j, iname, ipath)
                            try:
                                fh = open(ipath)
                                dataset.metadata.chromosomes = []
                                dataset.metadata.circular = []
                                dataset.metadata.chromlength = []
                                for k, line in enumerate(fh):
                                    fields = line.strip().split('\t')
                                    print >> sys.stderr, "GmapDB set_meta chrom %s fields %s" % (
                                        line, fields)
                                    if len(fields) > 2:
                                        dataset.metadata.chromosomes.append(
                                            str(fields[0]))
                                        dataset.metadata.chromlength.append(
                                            int(fields[2]))
                                    if len(fields) > 3 and fields[3] == 'circular':
                                        dataset.metadata.circular.append(
                                            str(fields[0]))
                                print >> sys.stderr, "GmapDB set_meta db_name %s chromosomes %s  circular %s" % (
                                    dataset.metadata.db_name, dataset.metadata.chromosomes, dataset.metadata.circular)
                            except Exception as e:
                                log.info(
                                    "GmapDB set_meta error %s %s " % (iname, e))
                                print >> sys.stderr, "GmapDB set_meta file %s Error %s" % (
                                    ipath, e)
                            finally:
                                if fh:
                                    fh.close()
                            continue
                        m = re.match(pat, iname)
                        if m:
                            log.info("GmapDB set_meta m %s %s " % (iname, m))
                            print >> sys.stderr, "GmapDB set_meta iname %s  %s" % (
                                iname, m.groups())
                            assert len(m.groups()) == 10
                            if m.groups()[2] == 'ref':
                                if m.groups()[-1] is not None and m.groups()[-1] != 'offsetscomp':
                                    dataset.metadata.snps.append(
                                        m.groups()[-1])
                                else:
                                    if m.groups()[-3] is not None:
                                        k = int(m.groups()[-3])
                                        kmers[k] = k
                                    if m.groups()[-4] is not None:
                                        dataset.metadata.basesize = int(
                                            m.groups()[-4])
                            elif m.groups()[3] == 'met':
                                dataset.metadata.cmet = True
                            elif m.groups()[4] == 'a2i':
                                dataset.metadata.atoi = True
                dataset.metadata.kmers = kmers.keys()
        self.regenerate_primary_file(dataset)


class GmapSnpIndex(Text):

    """
    A GMAP SNP index created by snpindex
    """
    MetadataElement(name="db_name", desc="The db name for this index set",
                    default='unknown', set_in_upload=True, readonly=True)
    MetadataElement(name="snps_name", default='snps',
                    desc="The name of SNP index", visible=True, no_value='', readonly=True)

    file_ext = 'gmapsnpindex'
    is_binary = True
    composite_type = 'auto_primary_file'
    allow_datatype_change = False

    def generate_primary_file(self, dataset=None):
        """
        This is called only at upload to write the html file
        cannot rename the datasets here - they come with the default unfortunately
        """
        return '<html><head></head><body>AutoGenerated Primary File for Composite Dataset</body></html>'

    def regenerate_primary_file(self, dataset):
        """
        cannot do this until we are setting metadata
        """
        bn = dataset.metadata.db_name
        log.info("GmapDB regenerate_primary_file %s" % (bn))
        rval = ['<html><head><title>GMAPDB %s</title></head><p/><H3>GMAPDB %s</H3><p/>cmet %s<br>atoi %s<H4>Maps:</H4><ul>' %
                (bn, bn, dataset.metadata.cmet, dataset.metadata.atoi)]
        for i, name in enumerate(dataset.metadata.maps):
            rval.append('<li>%s' % name)
        rval.append('</ul></html>')
        f = open(dataset.file_name, 'w')
        f.write("\n".join(rval))
        f.write('\n')
        f.close()

    def set_peek(self, dataset, is_multi_byte=False):
        log.info("GmapSnpIndex set_peek %s" % (dataset))
        if not dataset.dataset.purged:
            dataset.peek = "GMAP SNPindex %s on %s\n" % (
                dataset.metadata.snps_name, dataset.metadata.db_name)
            dataset.blurb = "GMAP SNPindex %s on %s\n" % (
                dataset.metadata.snps_name, dataset.metadata.db_name)
        else:
            dataset.peek = 'file does not exist'
            dataset.blurb = 'file purged from disk'

    def display_peek(self, dataset):
        try:
            return dataset.peek
        except:
            return "GMAP SNP index"

    def sniff(self, filename):
        return False

    def set_meta(self, dataset, overwrite=True, **kwd):
        """
        Expecting:
        extra_files_path/snp_name.iit
        extra_files_path/db_name/db_name.ref1[2345]1[2345]3offsetscomp.snp_name
        extra_files_path/db_name/db_name.ref1[2345]1[2345]3positions.snp_name
        extra_files_path/db_name/db_name.ref1[2345]1[2345]3gammaptrs.snp_name
        """
        log.info("GmapSnpIndex set_meta %s %s" %
                 (dataset, dataset.extra_files_path))
        pat = '(.*)\.(ref((\d\d)(\d\d))?3positions)\.(.+)?'
        efp = dataset.extra_files_path
        flist = os.listdir(efp)
        for i, fname in enumerate(flist):
            m = re.match(pat, fname)
            if m:
                assert len(m.groups()) == 6
                dataset.metadata.db_name = m.groups()[0]
                dataset.metadata.snps_name = m.groups()[-1]


class IntervalIndexTree(Text):

    """
    A GMAP Interval Index Tree Map
    created by iit_store
    (/path/to/map)/(mapname).iit
    """
    file_ext = 'iit'
    is_binary = True


class SpliceSitesIntervalIndexTree(IntervalIndexTree):

    """
    A GMAP Interval Index Tree Map
    created by iit_store
    """
    file_ext = 'splicesites.iit'


class IntronsIntervalIndexTree(IntervalIndexTree):

    """
    A GMAP Interval Index Tree Map
    created by iit_store
    """
    file_ext = 'introns.iit'


class SNPsIntervalIndexTree(IntervalIndexTree):

    """
    A GMAP Interval Index Tree Map
    created by iit_store
    """
    file_ext = 'snps.iit'


class TallyIntervalIndexTree(IntervalIndexTree):

    """
    A GMAP Interval Index Tree Map
    created by iit_store
    """
    file_ext = 'tally.iit'


class IntervalAnnotation(Text):

    """
    Class describing a GMAP Interval format:
        >label coords optional_tag
        optional_annotation (which may be zero, one, or multiple lines)
    The coords should be of the form:
        chr:position
        chr:startposition..endposition
    """
    file_ext = 'gmap_annotation'
    """Add metadata elements"""
    MetadataElement(name="annotations", default=0, desc="Number of interval annotations",
                    readonly=True, optional=True, visible=False, no_value=0)

    def set_meta(self, dataset, **kwd):
        """
        Set the number of annotations and the number of data lines in dataset.
        """
        data_lines = 0
        annotations = 0
        for line in open(dataset.file_name):
            line = line.strip()
            if line and line.startswith('>'):
                annotations += 1
                data_lines += 1
            else:
                data_lines += 1
        dataset.metadata.data_lines = data_lines
        dataset.metadata.annotations = annotations

    def set_peek(self, dataset, is_multi_byte=False):
        if not dataset.dataset.purged:
            dataset.peek = data.get_file_peek(
                dataset.file_name, is_multi_byte=is_multi_byte)
            if dataset.metadata.annotations:
                dataset.blurb = "%s annotations" % util.commaify(
                    str(dataset.metadata.annotations))
            else:
                dataset.blurb = util.nice_size(dataset.get_size())
        else:
            dataset.peek = 'file does not exist'
            dataset.blurb = 'file purged from disk'

    def sniff(self, filename):
        """
        Determines whether the file is a gmap annotation file
        Format:
            >label coords optional_tag
            optional_annotation (which may be zero, one, or multiple lines)
        For example, the label may be an EST accession, with the coords
        representing its genomic position.  Labels may be duplicated if
        necessary.
        The coords should be of the form
            chr:position
            chr:startposition..endposition
        The term "chr:position" is equivalent to "chr:position..position".  If
        you want to indicate that the interval is on the minus strand or
        reverse direction, then <endposition> may be less than <startposition>.
        """
        try:
            # >label chr:position[..endposition][ optional_tag]
            pat = '>(\S+)\s((\S+):(\d+)(\.\.(\d+))?(\s.(.+))?$'
            fh = open(filename)
            count = 0
            while True and count < 10:
                line = fh.readline()
                if not line:
                    break  # EOF
                line = line.strip()
                if line:  # first non-empty line
                    if line.startswith('>'):
                        count += 1
                        if re.match(pat, line) is None:  # Failed to match
                            return False
        finally:
            fh.close()
        return False


class SpliceSiteAnnotation(IntervalAnnotation):
    file_ext = 'gmap_splicesites'
    """
    Example:
        >NM_004448.ERBB2.exon1 17:35110090..35110091 donor 6678
        >NM_004448.ERBB2.exon2 17:35116768..35116769 acceptor 6678
        >NM_004448.ERBB2.exon2 17:35116920..35116921 donor 1179
        >NM_004448.ERBB2.exon3 17:35118099..35118100 acceptor 1179
        >NM_004449.ERG.exon1 21:38955452..38955451 donor 783
        >NM_004449.ERG.exon2 21:38878740..38878739 acceptor 783
        >NM_004449.ERG.exon2 21:38878638..38878637 donor 360
        >NM_004449.ERG.exon3 21:38869542..38869541 acceptor 360
    Each line must start with a ">" character, then be followed by an
    identifier, which may have duplicates and can have any format, with
    the gene name or exon number shown here only as a suggestion.  Then
    there should be the chromosomal coordinates which straddle the
    exon-intron boundary, so one coordinate is on the exon and one is on
    the intron.  (Coordinates are all 1-based, so the first character of a
    chromosome is number 1.)  Finally, there should be the splice type:
    "donor" or "acceptor".  You may optionally store the intron distance
    at the end.  GSNAP can use this intron distance, if it is longer than
    its value for --localsplicedist, to look for long introns at that
    splice site.  The same splice site may have different intron distances
    in the database; GSNAP will use the longest intron distance reported
    in searching for long introns.
    """

    def sniff(self, filename):  # TODO
        """
        Determines whether the file is a gmap splice site annotation file
        """
        try:
            # >label chr:position..position  donor|acceptor[ intron_dist]
            pat = '>(\S+\.intron\d+)\s((\S+):(\d+)\.\.(\d+))\s(donor|acceptor)(\s(\d+))?$'
            fh = open(filename)
            count = 0
            while count < 10:
                line = fh.readline()
                if not line:
                    break  # EOF
                line = line.strip()
                if line:  # first non-empty line
                    count += 1
                    if re.match(pat, line) is None:  # Failed to match
                        return False
        finally:
            fh.close()
        return False


class IntronAnnotation(IntervalAnnotation):
    file_ext = 'gmap_introns'
    """
    Example:
        >NM_004448.ERBB2.intron1 17:35110090..35116769
        >NM_004448.ERBB2.intron2 17:35116920..35118100
        >NM_004449.ERG.intron1 21:38955452..38878739
        >NM_004449.ERG.intron2 21:38878638..38869541
     The coordinates are 1-based, and specify the exon coordinates
     surrounding the intron, with the first coordinate being from the donor
     exon and the second one being from the acceptor exon.
    """

    def sniff(self, filename):  # TODO
        """
        Determines whether the file is a gmap Intron annotation file
        """
        try:
            # >label chr:position
            pat = '>(\S+\.intron\d+)\s((\S+):(\d+)\.\.(\d+)(\s(.)+)?$'
            fh = open(filename)
            count = 0
            while True and count < 10:
                line = fh.readline()
                if not line:
                    break  # EOF
                line = line.strip()
                if line:  # first non-empty line
                    count += 1
                    if re.match(pat, line) is None:  # Failed to match
                        return False
        finally:
            fh.close()
        return False


class SNPAnnotation(IntervalAnnotation):
    file_ext = 'gmap_snps'
    """
    Example:
        >rs62211261 21:14379270 CG
        >rs62211262 21:14379281 AT
        >rs62211263 21:14379298 WN
    Each line must start with a ">" character, then be followed by an
    identifier (which may have duplicates).  Then there should be the
    chromosomal coordinate of the SNP.  (Coordinates are all 1-based, so
    the first character of a chromosome is number 1.)  Finally, there
    should be the two possible alleles.  (Previous versions required that
    these be in alphabetical order: "AC", "AG", "AT", "CG", "CT", or "GT",
    but that is no longer a requirement.)  These alleles must correspond
    to the possible nucleotides on the plus strand of the genome.  If the
    one of these two letters does not match the allele in the reference
    sequence, that SNP will be ignored in subsequent processing as a
    probable error.

    GSNAP also supports the idea of a wildcard SNP.  A wildcard SNP allows
    all nucleotides to match at that position, not just a given reference
    and alternate allele.  It is essentially as if an "N" were recorded at
    that genomic location, although the index files still keep track of
    the reference allele.  To indicate that a position has a wildcard SNP,
    you can indicate the genotype as "WN", where "W" is the reference
    allele.  Another indication of a wildcard SNP is to provide two
    separate lines at that position with the genotypes "WX" and "WY",
    where "W" is the reference allele and "X" and "Y" are two different
    alternate alleles.
    """

    def sniff(self, filename):
        """
        Determines whether the file is a gmap SNP annotation file
        """
        try:
            # >label chr:position ATCG
            pat = '>(\S+)\s((\S+):(\d+)\s([TACGW][TACGN])$'
            fh = open(filename)
            count = 0
            while True and count < 10:
                line = fh.readline()
                if not line:
                    break  # EOF
                line = line.strip()
                if line:  # first non-empty line
                    count += 1
                    if re.match(pat, line) is None:  # Failed to match
                        return False
        finally:
            fh.close()
        return False


class TallyAnnotation(IntervalAnnotation):
    file_ext = 'gsnap_tally'
    """
    Output produced by gsnap_tally
    Example:
        >144 chr20:57268791..57268935
        G0
        A1(1@7|1Q-3)
        A2(1@36,1@1|1Q2,1Q-8)
        C2      0.889,0.912,0.889,0.889,0.933,0.912,0.912,0.889,0.889,0.889     -2.66,-2.89,-2.66,-2.66,-3.16,-2.89,-2.89,-2.66,-2.66,-2.66
        C1 T1   0.888,0.9,0.888,0.9,0.913,0.9,0.911,0.888,0.9,0.913     -2.66,-2.78,-2.66,-2.78,-2.91,-2.78,-2.89,-2.66,-2.78,-2.91
    """

    def sniff(self, filename):  # TODO
        """
        Determines whether the file is a gmap splice site annotation file
        """
        try:
            # >total chr:position..position
            pat = '^>(\d+)\s((\S+):(\d+)\.\.(\d+))$'
            pat2 = '^[GATCN]\d.*$'  # BaseCountDeatails
            fh = open(filename)
            count = 0
            while True and count < 10:
                line = fh.readline()
                if not line:
                    break  # EOF
                line = line.strip()
                if line:  # first non-empty line
                    count += 1
                    # Failed to match
                    if re.match(pat, line) is None and re.match(pat2, line) is None:
                        return False
        finally:
            fh.close()
        return False


class GsnapResult(Text):

    """
    The default output format for gsnap.   Can be used as input for gsnap_tally.
    """
    file_ext = 'gsnap'
