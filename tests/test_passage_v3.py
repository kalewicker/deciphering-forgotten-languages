import copy,json,tempfile,unittest
from array import array
from pathlib import Path

from fl_decipher.alignment_v2 import align_matrix,edge_metrics,score_matrices
from fl_decipher.experiment_v3 import factorial_differences,validate
from fl_decipher.passage_v3 import PreparedSource,ScoreCache,align,make_block,ordered_units,protected_groups
from fl_decipher.text import sentences

ROOT=Path(__file__).resolve().parents[1]
CFG={'weights':{'length':.55,'punctuation':.2,'repetition':.2,'anchors':.05},'match_floor':.72,'gap_penalty':.35,'merge_penalty':.04,'minimum_fl_atoms':3,'structural_weight':.6,'lexical_weight':.4,'abbreviations':['i.e.','e.g.','Mr.','Dr.']}
RULES={'minimum_observations':2,'minimum_source_groups':2,'minimum_candidate_fraction':.8}


def prepared(fs,es):
 source=PreparedSource(es,[(i,) for i in range(len(es))])
 cache=ScoreCache(fs,source,CFG,[[{'prediction':None} for _ in s.tokens] for s in fs])
 return source,cache


class PassageTests(unittest.TestCase):
 def test_abbreviations_preserve_atomic_ids_and_offsets(self):
  text='A, i.e. B is clear. Dr. Jones agrees.';atoms=sentences(text)
  groups=protected_groups(atoms,text,CFG['abbreviations'])
  self.assertEqual(groups,[(0,1),(2,3)])
  b=make_block(atoms,groups[0])
  for i,span in zip(b.atoms,b.spans):self.assertEqual(text[span[0]:span[1]],atoms[i].text)
  self.assertEqual(b.text,text[atoms[0].start:atoms[1].end])
 def test_abbreviation_protection_does_not_match_word_suffix(self):
  text='A heading notDr. Another sentence.'
  self.assertEqual(protected_groups(sentences(text),text,CFG['abbreviations']),[(0,),(1,)])
 def test_protected_group_survives_only_in_consecutive_original_order(self):
  groups=[(0,1),(2,3)]
  self.assertEqual(ordered_units(groups,[1,0,2,3]),[(1,),(0,),(2,3)])
  self.assertEqual(ordered_units(groups,[2,0,1,3]),[(2,),(0,1),(3,)])
 def test_one_to_one_replays_matrix_algorithm_at_matched_floor(self):
  fs=sentences('aa bb aa. cc dd ee cc ff gg. hh ii jj hh kk ll mm nn oo pp.')
  es=sentences('sun bird sun. sky cat frog sky dog cow. Unrelated extra material? earth sea land earth red green blue white black grey.')
  source,cache=prepared(fs,es)
  baseline={'weights':CFG['weights'],'match_floor':.72,'gap_penalty':.35,'minimum_links':3}
  matrices,_=score_matrices(fs,es,baseline,CFG,{},RULES)
  for method in ['structural','lexical']:
   expected=align_matrix(matrices[method],baseline);result=align([(i,) for i in range(len(fs))],source,cache,CFG,max_block=1,scoring=method)
   self.assertAlmostEqual(expected['strength'],result['strength'])
   self.assertEqual(result['edges'],[{'fl_index':x['fl_index'],'source_index':x['source_index']} for x in expected['links']])
 def test_two_to_one_block_recovers_split_passage(self):
  fs=sentences('ţ0 ţ1. ţ2 ţ3. ţ4 ţ5 ţ6 ţ7. ţ8 ţ9 ţ10 ţ11 ţ12.')
  es=sentences('red blue green white. silver black gold grey. apple pear plum peach cherry.')
  source,cache=prepared(fs,es)
  one=align([(i,) for i in range(4)],source,cache,CFG,max_block=1,scoring='structural')
  multi=align([(i,) for i in range(4)],source,cache,CFG,max_block=2,scoring='structural')
  self.assertGreater(len(multi['edges']),len(one['edges']))
  self.assertEqual({(e['fl_index'],e['source_index']) for e in multi['edges']},{(0,0),(1,0),(2,1),(3,2)})
  self.assertTrue(multi['minimum_links_met'])
 def test_two_to_two_cartesian_extras_are_errors_and_two_atoms_cannot_admit(self):
  fs=sentences('ţa ţb. ţc ţd.');es=sentences('bird cat. dog cow.')
  source,_=prepared(fs,es)
  class FakeCache:
   def block(self,ids):return make_block(fs,ids)
   def row(self,ids,size,scoring):return array('d',[1. if len(ids)==2 and size==2 else 0.]*(len(source.units)-size+1))
  result=align([(0,),(1,)],source,FakeCache(),CFG,max_block=2,scoring='structural')
  reference=[{'fl_index':0,'source_index':0},{'fl_index':1,'source_index':1}]
  m=edge_metrics(result['edges'],reference)
  self.assertEqual(m['proposed_edges'],4);self.assertEqual(m['precision'],.5)
  self.assertFalse(result['minimum_links_met'])
 def test_permutations_recompute_block_feature_order(self):
  fs=sentences('ţu na ţu. ka ka.');es=sentences('the bird the dog dog.')
  source,cache=prepared(fs,es)
  self.assertNotEqual(cache.row((0,1),1,'structural')[0],cache.row((1,0),1,'structural')[0])
 def test_frozen_inputs_and_no_new_training_evidence(self):
  cfg=json.loads((ROOT/'experiments/kamri_passage_v3a.json').read_text());b=json.loads((ROOT/'benchmarks/kamri_passage_v3a.json').read_text())
  docs=validate(ROOT,b,cfg);self.assertEqual(len(docs),18)
  self.assertEqual(sum(len(r['edges']) for r in b['records'] if r['split']=='fresh'),13)
  lex=json.loads((ROOT/cfg['lexicon_path']).read_text())
  for entry in lex.values():
   for candidate in entry['candidates']:self.assertFalse(set(candidate['independent_groups'])&set(cfg['fresh_groups']))
 def test_all_eight_variants_keep_matched_threshold_and_twelve_contrasts(self):
  cfg=json.loads((ROOT/'experiments/kamri_passage_v3a.json').read_text())
  self.assertEqual(len(cfg['variants']),8);self.assertEqual(cfg['match_floor'],.72)
  keys=['fresh_top1','fresh_correct_admissions','fresh_correct_edges','fresh_proposed_edges','fresh_absent_false_admissions','development_conditional_correct_edges']
  summaries=[{'variant':v['id'],**{k:0 for k in keys}} for v in cfg['variants']]
  comparisons=factorial_differences(summaries,cfg['variants'])
  self.assertEqual(len(comparisons),12);self.assertTrue(all(not any(r['deltas'].values()) for r in comparisons))
 def test_empty_alignment_abstains(self):
  source,cache=prepared([],[])
  result=align([],source,cache,CFG,max_block=2,scoring='structural')
  self.assertEqual(result['strength'],0);self.assertFalse(result['minimum_links_met'])

if __name__=='__main__':unittest.main()
