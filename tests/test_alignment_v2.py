import copy,json,tempfile,unittest
from pathlib import Path
from fl_decipher.alignment import local_align
from fl_decipher.alignment_v2 import score_matrices,align_matrix,lexical_agreement,without_work,edge_metrics
from fl_decipher.experiment_v2 import validate
from fl_decipher.text import sentences
ROOT=Path(__file__).resolve().parents[1]
BASE={'weights':{'length':.55,'punctuation':.2,'repetition':.2,'anchors':.05},'match_floor':.78,'gap_penalty':.35,'minimum_links':3}
LEX={'structural_weight':.6,'lexical_weight':.4,'match_floor':.72,'gap_penalty':.35,'minimum_links':3}
RULES={'minimum_observations':2,'minimum_source_groups':2,'minimum_candidate_fraction':.8}

class AlignmentV2Tests(unittest.TestCase):
 def test_matrix_baseline_replays_original_algorithm_including_gaps(self):
  f=sentences('aa bb aa. cc dd ee cc ff gg. hh ii jj hh kk ll mm nn oo pp.')
  e=sentences('sun bird sun. sky cat frog sky dog cow. Unrelated extra material? earth sea land earth red green blue white black grey.')
  matrices,_=score_matrices(f,e,BASE,LEX,{},RULES)
  a,b=local_align(f,e,BASE),align_matrix(matrices['structural'],BASE)
  for key in ['strength','links','gaps','minimum_links_met']:self.assertEqual(a[key],b[key])
 def test_overlap_counts_multiplicity_and_abstention_is_neutral(self):
  p=[{'prediction':'the'},{'prediction':'the'},{'prediction':'of'},{'prediction':None}]
  self.assertEqual(lexical_agreement(p,['the','of']),2/3)
  self.assertEqual(lexical_agreement(p,['the','the','of']),1.)
  self.assertEqual(lexical_agreement([{'prediction':None}],['the']),.5)
 def test_anchors_distinguish_identical_structure_without_learning(self):
  lex={'ţu':{'candidates':[{'meaning':'the','count':4,'independent_groups':['a','b'],'candidate_fraction':1.}]}}
  saved=copy.deepcopy(lex)
  f=sentences('ţu na ţu.');good=sentences('the bird the.');bad=sentences('cat dog cat.')
  a,_=score_matrices(f,good,BASE,LEX,lex,RULES);b,_=score_matrices(f,bad,BASE,LEX,lex,RULES)
  self.assertEqual(a['structural'],b['structural']);self.assertGreater(a['lexical'][0][0],b['lexical'][0][0]);self.assertEqual(lex,saved)
 def test_absent_control_removes_every_edition_of_work(self):
  pool={'gad_old':1,'gad_new':2,'other':3};groups={'gad_old':'gad','gad_new':'gad','other':'other'}
  self.assertEqual(without_work(pool,'gad',groups),{'other':3})
 def test_many_to_many_reference_edges_remain_in_denominator(self):
  reference=[{'fl_index':0,'source_index':0},{'fl_index':0,'source_index':1},{'fl_index':1,'source_index':2},{'fl_index':2,'source_index':2}]
  m=edge_metrics([reference[0],reference[2]],reference)
  self.assertEqual(m['reference_edges'],4);self.assertEqual(m['recall'],.5)
 def test_changed_lexicon_rejected_before_execution(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'lexicon.json').write_text('{}')
   b={'input_hashes':{'lexicon.json':'wrong'}};cfg={'development_groups':['a'],'fresh_groups':['b']}
   with self.assertRaisesRegex(ValueError,'changed after freeze'):validate(root,b,cfg)
 def test_frozen_data_and_lexicon_have_no_fresh_training_evidence(self):
  b=json.loads((ROOT/'benchmarks/kamri_alignment_v2.json').read_text());cfg=json.loads((ROOT/'experiments/kamri_alignment_v2.json').read_text())
  docs=validate(ROOT,b,cfg);self.assertEqual(len(docs),15)
  lex=json.loads((ROOT/cfg['lexicon_path']).read_text())
  for entry in lex.values():
   for candidate in entry['candidates']:
    self.assertFalse(set(candidate['independent_groups']) & set(cfg['fresh_groups']))
if __name__=='__main__':unittest.main()
