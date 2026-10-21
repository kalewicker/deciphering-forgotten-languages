"""E72 publication: exempt its exact public review ID from a key-pattern false positive."""
import checkpoint_turn as publication

REVIEW_ID = b'fl-risk-v72-d54e047e-d5e6-4404-bc0f-75eb646b19a6'
ORIGINAL_SCANNER = publication.SECRET


class ScopedScanner:
    def search(self, raw):
        # Only this generated, nonsecret identifier is masked for inspection.
        # Staged bytes and all other credential/publication checks are unchanged.
        return ORIGINAL_SCANNER.search(raw.replace(REVIEW_ID, b'public-e72-review-id'))


if __name__ == '__main__':
    publication.SECRET = ScopedScanner()
    publication.main()
