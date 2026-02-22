
# Dictionary mapping domain parts to price selectors
# Updated timestamp for reload
SITE_SELECTORS = {
    'myg.in': {
        'price': 'span[id^="sec_discounted_price_"]',
        'notes': 'Dynamic ID starting with sec_discounted_price_'
    },
    'nandilathgmart.com': {
        'price': '.wd-single-price .price ins .woocommerce-Price-amount bdi',
        'fallback': '.wd-single-price .price .woocommerce-Price-amount bdi',
        'notes': 'WooCommerce structure'
    },
    'pittappillilonline.com': {
        'price': '.price-list h3',
        'notes': 'Price inside h3 of price-list div'
    },
    'reliancedigital.in': {
        'price': 'span.pdp__offerPrice, span.pdp__price',
        'notes': 'Usually pdp__offerPrice'
    },
    'croma.com': {
        'price': '#pdp-product-price',
        'notes': 'Often ID pdp-product-price'
    },
    'amazon.in': {
        'price': ['span.a-price-whole', '.a-price .a-offscreen', '#priceblock_ourprice', '#priceblock_dealprice', '.a-size-medium.a-color-price'],
        'title': 'span#productTitle',
        'notes': 'Desktop selectors with fallbacks'
    },
    'flipkart.com': {
        'price': ['div.hZ3P6w', 'div.Nx9bqj', 'div._30jeq3', 'div.bnqy13'],
        'notes': 'Updated with 2026/2025 selectors'
    },
    'myntra.com': {
        'price': '.pdp-price strong, .pdp-price',
        'notes': 'pdp-price class'
    },
    'ajio.com': {
        'price': '.prod-sp',
        'notes': 'prod-sp class'
    },
    'books.toscrape.com': {
        'price': 'p.price_color',
        'notes': 'Test site'
    }
}
