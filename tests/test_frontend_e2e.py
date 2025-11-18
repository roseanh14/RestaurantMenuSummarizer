from playwright.sync_api import sync_playwright


def test_frontend_e2e():
    """Simple end-to-end test for the browser UI.

    It opens the page, fills the form, submits it and then waits
    until either a result card is rendered or an error message is shown.
    """

    base_url = "http://127.0.0.1:5000"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Open the app
        page.goto(base_url, wait_until="networkidle")

        # Fill the form
        page.fill("#url-input", "https://jidelna.webflow.io/")
        page.fill("#date-input", "2025-11-19")

        # Submit the form
        page.click("button[type=submit]")

        # Wait until either a result card OR an error message appears
        page.wait_for_function(
            """
            () => {
                const card = document.querySelector('#result .card');
                const errorText = (document.querySelector('#error')?.textContent || '').trim();
                return !!card || errorText.length > 0;
            }
            """,
            timeout=15000,
        )

        # Check what we actually got
        has_card = page.query_selector("#result .card") is not None
        error_text = (page.text_content("#error") or "").strip()

        # At least one of them must be present
        assert has_card or error_text, (
            "Expected either a rendered result card or an error message, "
            "but neither appeared."
        )

        # If we do have a card, do a couple of basic checks
        if has_card:
            result_text = page.text_content("#result") or ""
            assert "Date:" in result_text
            assert "Source:" in result_text

        browser.close()
