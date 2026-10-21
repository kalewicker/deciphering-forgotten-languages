import unittest
from fl_decipher.order_corpus_v76 import tokens, annotate, account


def candidate(uid, group, text, start=0, doc=None):
    return {'uid': uid, 'base_group': group, 'tokens': annotate(text, set()),
            'bindings': [{'document_id': doc or uid, 'start': start, 'end': start+len(text)}]}


class OrderCorpusTests(unittest.TestCase):
    def test_unicode_offsets_and_numeric_fragments(self):
        text = '\u0301A\u0301 β2 3γ δ'
        ts = tokens(text)
        self.assertEqual([t['form'] for t in ts], ['á', 'β', 'γ', 'δ'])
        self.assertEqual(text[ts[0]['start']:ts[0]['end']], 'A\u0301')
        self.assertEqual([t['numeric_neighbor'] for t in ts], [False, True, True, False])

    def test_masks_and_punctuation_are_barriers(self):
        ts = annotate('a b c, d 4 e f g', {'b'})
        self.assertEqual([t['form'] for t in ts if t['pair_from_previous']], ['f', 'g'])

    def test_eight_word_connections_are_transitive(self):
        first = 'a b c d e f g h'
        second = 'i j k l m n o p'
        rows = [candidate('1','A',first), candidate('2','B',first+' '+second),
                candidate('3','C',second)]
        result = account(rows, ['A','B','C','D'])
        self.assertEqual(result['groups'][0]['base_groups'], ['A','B','C'])
        self.assertEqual(len(result['groups']), 2)
        self.assertEqual(len(result['duplicate_witnesses']), 2)

    def test_short_shared_sequences_do_not_merge(self):
        result = account([candidate('1','A','a b c'),candidate('2','B','a b c')],['A','B'])
        self.assertEqual(len(result['groups']), 2)
        self.assertEqual(result['groups'][1]['retained_units'], 0)

    def test_duplicates_and_overlap_no_substitution(self):
        rows = [candidate('1','A','a b c',0,'same'),candidate('2','A','b c',2,'same'),
                candidate('3','A','b c',0,'other'),candidate('4','A','a b c',0,'different')]
        account(rows,['A'])
        self.assertEqual([r['exclusion'] for r in rows],
                         [None,'overlapping_saved_span','duplicate_sequence','duplicate_sequence'])
        self.assertEqual(rows[2]['duplicate_of'], '2')

    def test_capacity_requires_training_floor_and_keeps_zero_groups(self):
        rows = []
        for g in 'ABCD':
            for j in range(2):
                text = ' '.join(g.lower()+chr(97+j)+chr(97+i//26)+chr(97+i%26) for i in range(51))
                rows.append(candidate(g+str(j),g,text))
        result = account(rows,list('ABCDE'))
        self.assertEqual(sum(g['eligible'] for g in result['groups']),4)
        self.assertFalse(result['capacity_pass'])
        self.assertEqual([f['training_pairs'] for f in result['folds']],[300]*4)
        self.assertEqual(result['groups'][-1]['pairs'],0)


if __name__ == '__main__':
    unittest.main()
