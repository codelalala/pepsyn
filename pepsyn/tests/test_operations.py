# Copyright 2016 Uri Laserson
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from pytest import raises
from Bio.Seq import Seq
from Bio.Alphabet.IUPAC import protein, unambiguous_dna
import numpy as np

from pepsyn.operations import (
    tile, reverse_translate, remove_site_from_cds, x_to_ggsg,
    disambiguate_iupac_aa)
from pepsyn.codons import (
    FreqWeightedCodonSampler, UniformCodonSampler, ecoli_codon_usage)
from pepsyn.error import PepsynError


protein_seq = Seq(
    'METMSDYSKEVSEALSALRGELSALSAAISNTVRAGSYSAPVAKDCKAGHCDSKAVL', protein)
short_protein_seq = Seq('METMSD', protein)
all_aa_protein_seq = Seq('ACDEFGHIKLMNPQRSTVWY', protein)


class TestTile(object):

    def test_nonoverlapping_perfect(self):
        length = 19
        overlap = 0
        tiles = [t[2] for t in tile(protein_seq, length, overlap)]
        assert len(tiles) == 3
        assert all([len(t) == length for t in tiles])
        assert tiles[0] == Seq('METMSDYSKEVSEALSALR', protein)
        assert tiles[1] == Seq('GELSALSAAISNTVRAGSY', protein)
        assert tiles[2] == Seq('SAPVAKDCKAGHCDSKAVL', protein)
        assert sum(tiles, Seq('', protein)) == protein_seq

    def test_nonoverlapping_imperfect(self):
        length = 25
        overlap = 0
        tiles = [t[2] for t in tile(protein_seq, length, overlap)]
        assert len(tiles) == 3
        assert all([len(t) == length for t in tiles])
        assert tiles[0] == Seq('METMSDYSKEVSEALSALRGELSAL', protein)
        assert tiles[1] == Seq('SAAISNTVRAGSYSAPVAKDCKAGH', protein)
        assert tiles[2] == Seq('VRAGSYSAPVAKDCKAGHCDSKAVL', protein)

    def test_overlapping_perfect(self):
        length = 21
        overlap = 3
        tiles = [t[2] for t in tile(protein_seq, length, overlap)]
        assert len(tiles) == 3
        assert all([len(t) == length for t in tiles])
        assert tiles[0] == Seq('METMSDYSKEVSEALSALRGE', protein)
        assert tiles[1] == Seq('RGELSALSAAISNTVRAGSYS', protein)
        assert tiles[2] == Seq('SYSAPVAKDCKAGHCDSKAVL', protein)

    def test_overlapping_imperfect(self):
        length = 22
        overlap = 3
        tiles = [t[2] for t in tile(protein_seq, length, overlap)]
        assert len(tiles) == 3
        assert all([len(t) == length for t in tiles])
        assert tiles[0] == Seq('METMSDYSKEVSEALSALRGEL', protein)
        assert tiles[1] == Seq('GELSALSAAISNTVRAGSYSAP', protein)
        assert tiles[2] == Seq('GSYSAPVAKDCKAGHCDSKAVL', protein)

    def test_length_longer_than_seq(self):
        # import pytest; pytest.set_trace()
        length = len(protein_seq) + 5
        overlap = 5
        tiles = list(tile(protein_seq, length, overlap))
        assert len(tiles) == 1
        assert tiles[0][2] == protein_seq

    def test_overlap_longer_than_length(self):
        length = 10
        overlap = 15
        with raises(ValueError):
            tiles = list(tile(protein_seq, length, overlap))

    def test_negative_length(self):
        length = -10
        overlap = 5
        with raises(ValueError):
            tiles = list(tile(protein_seq, length, overlap))

    def test_zero_length(self):
        length = 0
        overlap = 5
        with raises(ValueError):
            tiles = list(tile(protein_seq, length, overlap))

    def test_negative_overlap(self):
        length = 20
        overlap = -3
        with raises(ValueError):
            tiles = list(tile(protein_seq, length, overlap))


class TestReverseTranslate(object):

    def test_freq_weighted_sampler(self):
        codon_sampler = FreqWeightedCodonSampler(usage=ecoli_codon_usage)
        dna_seq = reverse_translate(all_aa_protein_seq, codon_sampler)
        assert dna_seq.translate(table=codon_sampler.table) == all_aa_protein_seq

    def test_uniform_sampler(self):
        codon_sampler = UniformCodonSampler()
        dna_seq = reverse_translate(all_aa_protein_seq, codon_sampler)
        assert dna_seq.translate(table=codon_sampler.table) == all_aa_protein_seq


class TestSiteRemoval(object):

    # prefix and suffix are each 10 bases, CDS is 18 bases
    cds_start = 10
    cds_end = 28
    EcoRI = Seq('GAATTC', unambiguous_dna)
    codon_sampler = FreqWeightedCodonSampler(usage=ecoli_codon_usage)

    def test_no_site(self):
        dna_seq = Seq(
            'GAGATCCGGTCCATATCTTATTCAACGCAAGTTGTTAT', unambiguous_dna)
        new_seq = remove_site_from_cds(
            dna_seq, self.EcoRI, self.codon_sampler, self.cds_start,
            self.cds_end)
        assert new_seq.find(self.EcoRI) == -1
        assert new_seq == dna_seq

    def test_with_site_in_cds(self):
        dna_seq = Seq(
            'GAGATCCGGTCCATATCGAATTCAACGCAAGTTGTTAT', unambiguous_dna)
        new_seq = remove_site_from_cds(
            dna_seq, self.EcoRI, self.codon_sampler, self.cds_start,
            self.cds_end)
        orig_trans = dna_seq[self.cds_start:self.cds_end].translate(
            table=self.codon_sampler.table)
        new_trans = new_seq[self.cds_start:self.cds_end].translate(
            table=self.codon_sampler.table)
        assert new_seq.find(self.EcoRI) == -1
        assert new_seq != dna_seq
        assert len(new_seq) == len(dna_seq)
        assert new_seq[:self.cds_start] == dna_seq[:self.cds_start]
        assert new_seq[self.cds_end:] == dna_seq[self.cds_end:]
        assert new_trans == orig_trans

    def test_with_site_on_left_boundary(self):
        dna_seq = Seq(
            'GAGATCCGGAATTCATCTTATTCAACGCAAGTTGTTAT', unambiguous_dna)
        new_seq = remove_site_from_cds(
            dna_seq, self.EcoRI, self.codon_sampler, self.cds_start,
            self.cds_end)
        orig_trans = dna_seq[self.cds_start:self.cds_end].translate(
            table=self.codon_sampler.table)
        new_trans = new_seq[self.cds_start:self.cds_end].translate(
            table=self.codon_sampler.table)
        assert new_seq.find(self.EcoRI) == -1
        assert new_seq != dna_seq
        assert len(new_seq) == len(dna_seq)
        assert new_seq[:self.cds_start] == dna_seq[:self.cds_start]
        assert new_seq[self.cds_end:] == dna_seq[self.cds_end:]
        assert new_trans == orig_trans

    def test_with_site_on_left_boundary(self):
        dna_seq = Seq(
            'GAGATCCGGTCCATATCTTATTCGAATTCAGTTGTTAT', unambiguous_dna)
        new_seq = remove_site_from_cds(
            dna_seq, self.EcoRI, self.codon_sampler, self.cds_start,
            self.cds_end)
        orig_trans = dna_seq[self.cds_start:self.cds_end].translate(
            table=self.codon_sampler.table)
        new_trans = new_seq[self.cds_start:self.cds_end].translate(
            table=self.codon_sampler.table)
        assert new_seq.find(self.EcoRI) == -1
        assert new_seq != dna_seq
        assert len(new_seq) == len(dna_seq)
        assert new_seq[:self.cds_start] == dna_seq[:self.cds_start]
        assert new_seq[self.cds_end:] == dna_seq[self.cds_end:]
        assert new_trans == orig_trans

    def test_with_site_outside_cds(self):
        dna_seq = Seq(
            'GAGATCCGGTCCATATCTTATTCAACGCAAGAATTCAT', unambiguous_dna)
        new_seq = remove_site_from_cds(
            dna_seq, self.EcoRI, self.codon_sampler, self.cds_start,
            self.cds_end)
        assert new_seq.find(self.EcoRI) >= 0
        assert new_seq == dna_seq

    def test_bad_cds_with_site(self):
        # NOTE: CDS is different in this test
        cds_start = 10
        cds_end = 27
        dna_seq = Seq(
            'GAGATCCGGAATTCATCTTATTCAACGAAGTTGTTAT', unambiguous_dna)
        with raises(PepsynError):
            new_seq = remove_site_from_cds(
                dna_seq, self.EcoRI, self.codon_sampler, cds_start, cds_end)


class TestLinkerReplacement(object):

    def test_null_seq(self):
        p = Seq('', protein)
        r = x_to_ggsg(p)
        assert p == r

    def test_no_Xs(self):
        p = Seq('GYTTRS', protein)
        r = x_to_ggsg(p)
        assert p == r

    def test_Xs_prefix(self):
        p = Seq('XXXGYTTRS', protein)
        r = x_to_ggsg(p)
        assert r == Seq('GGSGYTTRS', protein)

    def test_Xs_suffix(self):
        p = Seq('GYTTRSXXXX', protein)
        r = x_to_ggsg(p)
        assert r == Seq('GYTTRSGGSG', protein)

    def test_Xs_infix(self):
        p = Seq('GYTXXXXXTRS', protein)
        r = x_to_ggsg(p)
        assert r == Seq('GYTGGSGGTRS', protein)

    def test_multiple_stretches(self):
        p = Seq('XGYTXXXTRXXS', protein)
        r = x_to_ggsg(p)
        assert r == Seq('GGYTGGSTRGGS', protein)

    def test_single_X(self):
        p = Seq('GYTXTRS', protein)
        r = x_to_ggsg(p)
        assert r == Seq('GYTGTRS', protein)
        p = Seq('XGYTTRS', protein)
        r = x_to_ggsg(p)
        assert r == Seq('GGYTTRS', protein)
        p = Seq('GYTTRSX', protein)
        r = x_to_ggsg(p)
        assert r == Seq('GYTTRSG', protein)

    def test_double_X(self):
        p = Seq('GYTXXTRS', protein)
        r = x_to_ggsg(p)
        assert r == Seq('GYTGGTRS', protein)

    def test_many_single_Xs(self):
        p = Seq('GXYTXTXRXS', protein)
        r = x_to_ggsg(p)
        assert r == Seq('GGYTGTGRGS', protein)

    def test_many_Xs(self):
        p = Seq('GYTXXXXXXXXXTRS', protein)
        r = x_to_ggsg(p)
        assert r == Seq('GYTGGSGGGSGGTRS', protein)


class TestProteinDisambig(object):

    def test_unambig(self):
        proteins = list(disambiguate_iupac_aa(all_aa_protein_seq))
        assert len(proteins) == 1
        assert proteins[0] == all_aa_protein_seq

    def test_B(self):
        ambig = Seq('AABAA', protein)
        disambig = {p.tostring() for p in disambiguate_iupac_aa(ambig)}
        assert disambig == {'AADAA', 'AANAA'}

    def test_X(self):
        ambig = Seq('AAXAA', protein)
        disambig = {p.tostring() for p in disambiguate_iupac_aa(ambig)}
        assert disambig == {'AA{}AA'.format(aa) for aa in all_aa_protein_seq}

    def test_Z(self):
        ambig = Seq('AAZAA', protein)
        disambig = {p.tostring() for p in disambiguate_iupac_aa(ambig)}
        assert disambig == {'AAEAA', 'AAQAA'}

    def test_J(self):
        ambig = Seq('AAJAA', protein)
        disambig = {p.tostring() for p in disambiguate_iupac_aa(ambig)}
        assert disambig == {'AALAA', 'AAIAA'}

    def test_U(self):
        ambig = Seq('AAUAA', protein)
        disambig = {p.tostring() for p in disambiguate_iupac_aa(ambig)}
        assert disambig == {'AACAA'}

    def test_O(self):
        ambig = Seq('AAOAA', protein)
        disambig = {p.tostring() for p in disambiguate_iupac_aa(ambig)}
        assert disambig == {'AAKAA'}

    def test_adjacent_ambig(self):
        ambig = Seq('AAJJAA', protein)
        proteins = set(disambiguate_iupac_aa(ambig))
        assert len(proteins) == 4
        assert proteins == {'AALLAA', 'AALIAA', 'AAILAA', 'AAIIAA'}