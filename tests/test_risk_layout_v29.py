import importlib.util
from pathlib import Path
import unittest

from fl_decipher.risk_layout_v29 import assemble,grouped_chars,raster_rules,concordance,citations,continuities

SPEC=importlib.util.spec_from_file_location('independent_risk_v29',Path(__file__).resolve().parents[1]/'scripts/verify_risk_layout_v29.py')
REF=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(REF)


def char(text,x=0,base=20,size=10,matrix=None,top=None,bottom=None):
    return {'text':text,'x0':x,'x1':x+5,'top':base-size if top is None else top,'bottom':base if bottom is None else bottom,
            'size':size,'matrix':matrix or [1.,0.,0.,1.,x,100-base],'fontname':'fixture','upright':matrix is None}


def page(chars,number=1,rules=None):
    offset=0;rows=[]
    for i,c in enumerate(chars):
        rows.append(c|{'index':i,'native_start':offset,'native_end':offset+len(c['text'])});offset+=len(c['text'])
    return {'id':f'fixture:{number}','pdf_page_one_based':number,'width':100,'height':100,'chars':rows,'raster_rules':rules or []}


class RiskLayoutTests(unittest.TestCase):
    def check_independent(self,p,raw='',legacy=''):
        result=assemble(p,raw,legacy)
        self.assertTrue(REF.verify_page(p,result,raw,legacy))
        return result

    def test_anchored_baseline_does_not_drift(self):
        p=page([char('a',0,20),char('b',5,21.5),char('c',10,23)])
        result=self.check_independent(p)
        self.assertEqual([l['text'] for l in result['lines']],['ab','c'])

    def test_font_change_stays_on_baseline(self):
        result=self.check_independent(page([char('a'),char('b',5,size=12)]))
        self.assertEqual(len(result['lines']),1)
        self.assertEqual(result['text'],'ab\n')

    def test_superscript_digits_are_retained(self):
        result=self.check_independent(page([char('x',0,20),char('1',5,16,6)]))
        self.assertEqual(result['text'],'x1\n')
        self.assertEqual(len(result['attachments']),1)
        self.assertEqual(result['native_glyph_text'],'x1')

    def test_attachment_chains_are_not_followed(self):
        result=self.check_independent(page([char('a',0,12,4),char('b',5,16,6),char('c',10,20,10)]))
        self.assertEqual(len(result['lines']),2)
        self.assertEqual(len(result['attachments']),1)

    def test_rotated_lane_reading_order(self):
        a=char('a',0,matrix=[0.,1.,-1.,0.,32.,30.],top=60,bottom=70)
        b=char('b',0,matrix=[0.,1.,-1.,0.,32.,40.],top=50,bottom=60)
        result=self.check_independent(page([b,char('X'),a]))
        self.assertEqual([l['text'] for l in result['lines']],['X','ab'])
        self.assertEqual(result['lines'][1]['char_indices'],[2,0])

    def test_inferred_space_has_own_provenance(self):
        result=self.check_independent(page([char('a'),char('b',8)]))
        self.assertEqual(result['text'],'a b\n')
        space=next(p for p in result['pieces'] if p['kind']=='inferred_space')
        self.assertEqual((space['left_char'],space['right_char'],space['gap']),(0,1,3))
        self.assertEqual(result['native_glyph_text'],'ab')

    def test_explicit_unicode_space_is_not_doubled(self):
        result=self.check_independent(page([char('a'),char('\u00a0',5),char('b',15)]))
        self.assertEqual(result['text'],'a\u00a0b\n')
        self.assertFalse(any(p['kind']=='inferred_space' for p in result['pieces']))

    def test_repeated_and_empty_glyphs_have_unique_membership(self):
        result=self.check_independent(page([char('A'),char('',5),char('A',10)]))
        glyphs=[p for p in result['pieces'] if p['kind']=='glyph']
        self.assertEqual([p['char_index'] for p in glyphs],[0,1,2])
        self.assertEqual(glyphs[1]['start'],glyphs[1]['end'])

    def test_unknown_orientation_is_unresolved(self):
        result=self.check_independent(page([char('A'),char('?',matrix=[.5,.5,-.5,.5,10.,80.])]))
        self.assertEqual(result['lines'][-1]['role_hint'],'orientation_unresolved')

    def test_raster_threshold_endpoint_and_row_anchor(self):
        pixels=bytearray([255]*10000)
        for y,a,b in [(54,10,30),(55,10,30),(56,11,31),(58,12,32),(59,13,33)]:
            pixels[y*100+a:y*100+b]=bytes([128])*(b-a)
        rules=raster_rules(bytes(pixels),100,100,100,100)
        self.assertEqual(rules,REF.reference_raster(bytes(pixels),100,100,100,100))
        self.assertEqual([len(r['pixel_runs']) for r in rules],[3,1])
        self.assertEqual(rules[0]['pixel_box'],[10,55,32,59])

    def test_all_unicode_concordances_and_citation_forms(self):
        target='e\u0301te\u0301 ... ÉTÉ'
        found=concordance('été',target)
        self.assertEqual(found,REF.reference_concordance('été',target))
        self.assertEqual(found['status'],'ambiguous')
        self.assertEqual([target[m['start']:m['end']] for m in found['matches']],['e\u0301te\u0301','ÉTÉ'])
        text='[2, 11] [4-6] [ 7 ]'
        self.assertEqual(citations(text),REF.reference_citations(text))
        self.assertEqual([c['key'] for c in citations(text)],['[2,11]','[7]'])

    def test_continuity_excludes_note_and_does_not_join(self):
        pages=[{'pdf_page_one_based':2,'lines':[{'role_hint':'body_or_unresolved','text':'such as-'},{'role_hint':'footnote_candidate','text':'a footnote'}]},
               {'pdf_page_one_based':3,'lines':[{'role_hint':'upper_band_candidate','text':'header'},{'role_hint':'body_or_unresolved','text':'tronomy and geology'}]}]
        result=continuities(pages)
        self.assertEqual(result,REF.reference_continuities(pages))
        self.assertTrue(result[0]['continuation_candidate'])
        self.assertFalse(result[0]['joined_text_created'])
        self.assertEqual((result[0]['left_fragment'],result[0]['right_fragment']),('as-','tronomy'))


if __name__=='__main__':unittest.main()
