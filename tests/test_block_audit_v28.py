import unittest
from fl_decipher.block_audit_v28 import html_map,line_map,concordance,pdf_map,fl_reference,union_size


class BlockAuditTests(unittest.TestCase):
    def test_repeated_html_strings_entities_and_removed_nodes_keep_offsets(self):
        raw=b'<div class="post-body"><p>repeat<em> &amp; repeat </em>repeat</p><p><a href="x">last</a></p><br><img alt="x"><script>evil</script><!-- omit --></div>'
        export='repeat & repeat repeat last\n';m=html_map(raw,export)
        self.assertEqual([a['text'] for a in m['atoms']],['repeat','& repeat','repeat','last'])
        self.assertNotEqual(m['atoms'][0]['dom_path'],m['atoms'][2]['dom_path'])
        self.assertEqual(m['excluded_tags'],{'script':1});self.assertTrue(m['blocks'][-1]['link_only'])
        self.assertEqual([e['tag'] for e in m['zero_text_events']],['br','img'])
        for a in m['atoms']:self.assertEqual(export[a['start']:a['end']],a['text'])
        with self.assertRaises(AssertionError):html_map(raw,export+'changed')

    def test_quote_punctuation_does_not_create_quote_markup(self):
        m=html_map(b'<div class="post-body"><p>an ending quote"</p></div>','an ending quote"\n')
        self.assertTrue(m['blocks'][0]['ends_with_quote']);self.assertEqual(m['blocks'][0]['role'],'paragraph_markup')
        m=html_map(b'<div class="post-body"><blockquote><p>quote</p></blockquote><nav>next</nav></div>','quote next\n')
        self.assertEqual([b['role'] for b in m['blocks']],['quotation_markup','navigation_markup'])

    def test_noncontiguous_owner_runs_and_boundary_crossings_remain_distinct(self):
        m=html_map(b'<div class="post-body"><div>before<p>inside</p>after</div></div>','before inside after\n')
        self.assertEqual(len(m['blocks']),3)
        self.assertEqual(m['blocks'][0]['owner_path'],m['blocks'][2]['owner_path'])
        r=fl_reference({'span':{'start':0,'end':19,'text':'before inside after'}},m,'before inside after\n')
        self.assertTrue(r['crosses_block_runs']);self.assertEqual(len(r['block_ids']),3)
        self.assertEqual(m['joins'],[{'start':6,'end':7,'text':' '},{'start':13,'end':14,'text':' '}])

    def test_concordance_retains_all_occurrences_and_no_token_repairs(self):
        r=concordance('alpha beta','ALPHA, beta; alpha beta')
        self.assertEqual(r['status'],'ambiguous');self.assertEqual(len(r['matches']),2)
        self.assertEqual(concordance('astronomy','as- footnote tronomy')['status'],'unmapped')
        self.assertEqual(concordance('é','e\u0301')['status'],'unique')

    def page(self):
        def word(i,text,top,size=10,upright=True,x0=100):
            return {'word_index':i,'text':text,'top':top,'bottom':top+size,'x0':x0,'x1':x0+40,'size':size,'upright':upright}
        return {'id':'test:pdf:001','work':'test','pdf_page_one_based':1,'width':600,'height':1000,'modal_font_size':10,
                'words':[word(0,'body',100),word(1,'note',800,8),word(2,'65',900),word(3,'margin',100,10,False,10)],
                'horizontal_edges':[{'edge_index':0,'top':780,'bottom':780,'x0':100,'x1':250},
                                    {'edge_index':1,'top':780.5,'bottom':780.5,'x0':100,'x1':250}]}

    def test_geometry_keeps_rotation_numeric_lines_and_candidate_footnotes(self):
        m=line_map(self.page());self.assertEqual(len(m['candidate_rules']),1)
        self.assertEqual(m['candidate_rules'][0]['edge_indices'],[0,1])
        roles={l['text']:l['role_hint'] for l in m['lines']}
        self.assertEqual(roles,{'body':'body_or_unresolved','note':'footnote_candidate','65':'numeric_only_line','margin':'rotated_text'})
        self.assertEqual(sorted(i for l in m['lines'] for i in l['word_indices']),[0,1,2,3])

    def test_line_anchor_does_not_drift_via_neighbor_chaining(self):
        p=self.page();p['words']=[p['words'][0]|{'word_index':i,'text':str(i),'top':100+offset,'x0':100+i*50,'x1':140+i*50} for i,offset in enumerate([0,2.9,5.8])]
        self.assertEqual(len(line_map(p)['lines']),2)

    def test_numeric_marker_inventory_does_not_infer_semantic_loss(self):
        p=self.page();m=pdf_map(p,'body [2, 11] note [2,11] [3–5]','body [2,11] note')
        self.assertEqual(len(m['numeric_citations']),2)
        self.assertTrue(all(c['represented_in_legacy_form'] for c in m['numeric_citations']))
        self.assertEqual(m['numeric_citations'][0]['key'],'[2,11]')

    def test_coverage_union_does_not_double_count_overlapping_matches(self):
        self.assertEqual(union_size([{'start':0,'end':10},{'start':5,'end':12},{'start':20,'end':23}]),15)

    def test_independent_tree_walk_and_geometry_maps_agree(self):
        from scripts.verify_block_audit_v28 import reference_html,reference_page
        raw=b'<div class="post-body">before<p>same<em>same</em></p>after<br><p><a href="x">link</a></p><!--ignore--></div>'
        export='before same same after link\n'
        self.assertEqual(html_map(raw,export),reference_html(raw,export))
        p=self.page();rawpage='body note 65 margin [2, 11]';legacy='body note margin'
        self.assertEqual(pdf_map(p,rawpage,legacy),reference_page(p,rawpage,legacy))


if __name__=='__main__':unittest.main()
