(function() {
    // Clear previous handlers.
    $(document).on('ghtupdate', function(e, $div) {
        $('.product-quantity').change(function(e) {
           updateInput();
        });

        function updateInput() {
            var serializedEntries = [], $dataInput = $div.find('#id_products');
            $('.product-quantity').each(function(idx, element) {
                var $el = $(element);
                serializedEntries.push({
                    product: $el.attr('data-product-id'),
                    quantity: $el.val()
                });
            });
            $dataInput.val(JSON.stringify(serializedEntries));
        }
    });
})();