(function() {
    var selectedProductData = {};
    // Clear previous handlers.
    $(document).on('ghtupdate', function(e, $div) {
        refreshFromInput();
        $div.on('click', '#add-product', function(e) {
            var productName = $div.find('#id_product option:selected').html(),
                productData = {name: productName},
                productId;
            $div.find('#product-form :input').each(function() {
                var val = $(this).val();
                if ($(this).attr('type') == 'number')
                    val = parseInt(val);
                productData[$(this).attr('name')] = val;
            });
            productId = parseInt(productData['product']);
            if (isNaN(productId)) return;
            if (selectedProductData[productId])
                selectedProductData[productId].quantity += productData.quantity;
            else
                selectedProductData[productId] = productData;
            refreshItems();
        });

        $div.on('click', '.delete-link', function() {
            var productId = parseInt($(this).parents('.order-item-row').data('product-id'));
            removeProductById(productId);
            return false;
        });

        $div.on('change', '.selected-inline-input', function() {
            var productId = parseInt($(this).parents('.order-item-row').data('product-id')),
                val = $(this).val(),
                fieldName = $(this).attr('name');
            if ($(this).attr('type') == 'number') val = parseInt(val);
            // If they change a quantity to 0, just remove the item.
            if (fieldName == 'quantity' && val == 0) removeProductById(productId); 
            else {
                selectedProductData[productId][fieldName] = val;
                updateInput();
            }
        });

        function refreshFromInput() {
            var data = $div.find('#id_products').val(),
                parsed;
            selectedProductData = {};
            if (data !== "") {
                parsed = JSON.parse(data);
                $.each(parsed, function(idx, entryData) {
                    selectedProductData[entryData.productId] = entryData;
                });
            }
            refreshItems();
        }

        function refreshItems() {
            var cart = $div.find('#item-cart'),
                content = cart.find('.cart-content'),
                template = cart.find('.order-item-row.hidden');
            content.html('');
            $.each(selectedProductData, function(productId, productData) {
                if (productData == null) return;
                var cloned = template.clone();
                // Populate fields.
                $.each(productData, function (field, value) {
                    cloned.find('[name=' + field + ']').val(value);
                });
                cloned.find('.product-name').html(productData.name);
                cloned.data('product-id', productId);
                cloned.removeClass('hidden');
                content.append(cloned);
                content.append('<br><br>');
            });
            updateInput();
        }

        function removeProductById(productId) {
            selectedProductData[productId] = null;
            refreshItems();
        }

        function updateInput() {
            var serializedEntries = [], dataInput = $div.find('#id_products');
            $.each(selectedProductData, function(productId, productData) {
                if (productData == null) return;
                serializedEntries.push(productData);
            });
            dataInput.val(JSON.stringify(serializedEntries));
        }
    });
})();