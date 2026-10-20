import unittest
from fl_decipher.result_attribution_v61 import attribute, summarize

CFG = {'main_selector': 'main#main-content', 'container_selector': 'main#main-content > div#main-content.wrapper.category-container > div.row > div.col-md-8.col-sm-7',
       'card_selector': 'article.listing-block', 'heading_selector': 'main#main-content > div.type-bar h2',
       'expected_title': 'You searched for ANITA – Physics World', 'expected_heading': 'Results for: ANITA'}
PRIOR = {'article_exposures': {'https://physicsworld.com/a/test/': ['previous']}, 'captured_article_keys': ['https://physicsworld.com/a/test/']}
CARD = '<article class="listing-block"><div class="listing-block__info"><h3 class="listing-block__title"><a href="/a/test/" title="Title">Title</a></h3><p>Snippet</p><a href="/c/topic/">category</a></div><a class="listing-block__image" href="/a/test/"></a></article>'


def page(cards=CARD, extra=''):
    return ('<html><head><title>You searched for ANITA – Physics World</title></head><body class="search search-results"><nav><a href="/a/test/">nav</a></nav><main id="main-content"><div class="type-bar"><h2>Results for: ANITA</h2></div><div id="main-content" class="wrapper category-container"><div class="row"><div class="col-md-8 col-sm-7">'+cards+'</div></div></div></main>'+extra+'</body></html>').encode()


class ResultAttributionTests(unittest.TestCase):
    def test_complete_card_navigation_duplicates_and_missing_date(self):
        r = attribute(page(), 'https://physicsworld.com/?s=ANITA', CFG, PRIOR); s = summarize(r)
        self.assertEqual((s['structurally_attributed_cards'],s['strict_url_usable_cards'],s['anchor_occurrences_accounted']), (1,1,4))
        self.assertEqual([a['role'] for a in r['anchor_ledger']], ['outside_listing_cards','attributed_title_link','supporting_card_link','attributed_image_duplicate'])
        self.assertEqual(s['cards_without_date_markers'],1)
        self.assertTrue(r['cards'][0]['previously_captured_in_registry'])
        self.assertEqual(r['anchor_ledger'][-1]['text'],'')
        self.assertFalse(r['cards'][0]['article_eligibility_assessed'])

    def test_encoded_url_is_attributable_but_strictly_rejected(self):
        r = attribute(page(CARD.replace('/a/test/','/a/test-%ce%ba/')), 'https://physicsworld.com/', CFG, PRIOR)
        self.assertTrue(r['cards'][0]['structurally_attributed'])
        self.assertFalse(r['cards'][0]['strict_url_usable'])
        self.assertIn('https://physicsworld.com/a/test-%ce%ba/',r['exposure_registry']['all_listing_urls_exposed'])

    def test_conflicting_missing_duplicate_and_external_card_links_fail(self):
        variants = [CARD.replace('class="listing-block__image" href="/a/test/"','class="listing-block__image" href="/a/other/"'),
                    CARD.replace('<p>Snippet</p>',''), CARD.replace('<p>Snippet</p>','<p>Snippet</p><p>Other</p>'),
                    CARD.replace('title="Title"','title="Different"'), CARD.replace('/a/test/','https://evil.test/a/test/'),
                    CARD.replace('</h3>','<a href="/a/test/">extra</a></h3>')]
        for card in variants:
            with self.subTest(card=card): self.assertFalse(attribute(page(card),'https://physicsworld.com/',CFG,PRIOR)['cards'][0]['structurally_attributed'])

    def test_wrong_query_base_and_duplicate_container_fail_closed(self):
        for raw in [page().replace(b'Results for: ANITA',b'Results for: OTHER'),page(extra='<base href="https://evil.test/">'),page(extra='<main id="main-content"></main>'),page().replace(b'class="search search-results"',b'class="search"')]:
            r=attribute(raw,'https://physicsworld.com/',CFG,PRIOR)
            self.assertFalse(r['page_attribution_supported']);self.assertFalse(r['cards'][0]['structurally_attributed'])

    def test_outside_and_nested_cards_retained_as_rejections(self):
        r=attribute(page(extra=CARD),'https://physicsworld.com/',CFG,PRIOR)
        self.assertEqual(len(r['cards']),2);self.assertFalse(r['cards'][1]['structurally_attributed'])
        nested=CARD.replace('<p>Snippet</p>','<p>Snippet</p>'+CARD)
        r=attribute(page(nested),'https://physicsworld.com/',CFG,PRIOR)
        self.assertTrue(all(not c['structurally_attributed'] for c in r['cards']))
        self.assertIn('ambiguous_nested_card_ownership',[a['role'] for a in r['anchor_ledger']])

    def test_duplicate_cards_and_explicit_dates_preserved(self):
        r=attribute(page(CARD+CARD.replace('<p>Snippet</p>','<p>Snippet</p><time datetime="2018-01-01">January</time>')),'https://physicsworld.com/',CFG,PRIOR)
        self.assertEqual(r['cards'][1]['duplicate_of_card_index'],0)
        self.assertEqual(r['cards'][1]['date_markers'][0]['datetime'],'2018-01-01')
        self.assertEqual(summarize(r)['unique_strict_article_urls'],1)
        self.assertEqual(summarize(r)['structurally_attributed_cards'],2)

    def test_exposure_union_and_future_bound_do_not_admit(self):
        r=attribute(page(CARD.replace('/a/test/','/a/new/')),'https://physicsworld.com/',CFG,PRIOR)
        self.assertIn('https://physicsworld.com/a/test/',r['exposure_registry']['article_exposures'])
        self.assertIn('https://physicsworld.com/a/new/',r['exposure_registry']['article_exposures'])
        s=summarize(r)
        self.assertEqual(s['future_challenge']['minimum_window_bag_capacity'],6)
        for key in ['nominations','article_eligibility_assessments','numeric_or_alignment_scores','new_article_captures','research_network_requests']:self.assertEqual(s[key],0)
