import unittest
from bs4 import BeautifulSoup
from fl_decipher.cohort_scope_v52 import accounting, extract_scope

SELECTOR = 'article[id^="post-"] > div.entry-content'


def inspect(content):
    raw = ('<html><body><p>Outside</p><article id="post-1"><div class="entry-content">' + content + '</div></article></body></html>').encode()
    soup = BeautifulSoup(raw, 'html.parser')
    for t in soup.select('script,style,noscript,template,svg,canvas'): t.decompose()
    return extract_scope(raw, soup.body.get_text(' ', strip=True), SELECTOR)


class CohortScopeTests(unittest.TestCase):
    def test_repeated_text_keeps_distinct_dom_derived_positions(self):
        s = inspect('<p>Repeat</p><div><p>Repeat</p></div>')
        spans = [r['body_span'] for r in s['paragraph_inventory']]
        self.assertNotEqual(spans[0], spans[1]); self.assertEqual(s['legacy_direct_paragraphs'][0]['body_mapping_count'], 2)
        self.assertTrue(all(accounting(s).values()))

    def test_inline_nested_and_empty_paragraphs_keep_owner_and_runs(self):
        s = inspect('<p>One <em>inline</em> tail.</p><div><p>Nested</p></div><p></p>')
        self.assertEqual([r['text'] for r in s['paragraph_runs']], ['One inline tail.', 'Nested'])
        self.assertEqual(len(s['paragraph_inventory']), 3)
        self.assertEqual(len(s['added_paragraph_leaf_indices']), 1)
        self.assertTrue(all(accounting(s).values()))

    def test_ancestor_priority_overrides_p_in_all_separate_channels(self):
        s = inspect('<form><p>Form</p></form><figure><p>Caption</p></figure><table><tr><td><p>Cell</p></td></tr></table>'
                    '<blockquote><p>Quote</p></blockquote><ul><li><p>List</p></li></ul><h2>Heading</h2>Loose')
        self.assertEqual(s['channel_leaf_counts'], {'blockquote': 1, 'figure': 1, 'form': 1, 'heading': 1, 'list': 1, 'other': 1, 'table': 1})
        self.assertEqual(s['paragraph_runs'], [])

    def test_new_scope_can_remove_old_included_form_text(self):
        s = inspect('<p>Before <form>Form text</form> after</p>')
        self.assertEqual(s['removed_legacy_leaf_indices'], [1])
        self.assertEqual([r['text'] for r in s['paragraph_runs']], ['Before', 'after'])
        self.assertTrue(all(accounting(s).values()))

    def test_no_join_across_excluded_leaves_or_distinct_paragraph_owners(self):
        s = inspect('<p>1 <span>2</span><figure>excluded</figure> 3</p><p>4</p>')
        self.assertEqual([r['text'] for r in s['paragraph_runs']], ['1 2', '3', '4'])
        self.assertTrue(all(accounting(s).values()))

    def test_nested_p_inventory_does_not_duplicate_selected_leaf_runs(self):
        s = inspect('<p>Outer <p>Inner</p> tail</p>')
        self.assertEqual(len(s['paragraph_inventory']), 2)
        self.assertEqual(s['paragraph_inventory'][0]['nested_p_descendants'], 1)
        self.assertEqual([r['text'] for r in s['paragraph_runs']], ['Outer Inner tail'])
        self.assertTrue(all(accounting(s).values()))

    def test_unicode_and_comments_scripts_preserve_exact_body_coordinates(self):
        s = inspect('<p>é <em>β</em><!--ignore--> 100.000</p><script>96</script>')
        self.assertEqual(s['paragraph_runs'][0]['text'], 'é β 100.000')
        self.assertNotIn('96', s['container_text']); self.assertTrue(all(accounting(s).values()))

    def test_body_mismatch_and_ambiguous_container_fail_closed(self):
        with self.assertRaises(ValueError): extract_scope(b'<html><body>No article</body></html>', 'No article', SELECTOR)
        raw = b'<html><body><article id="post-1"><div class="entry-content"><p>Body</p></div></article></body></html>'
        with self.assertRaises(ValueError): extract_scope(raw, 'wrong', SELECTOR)
