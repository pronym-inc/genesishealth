(function() {
    var cart = [];
    // Clear previous handlers.
    $(document).on('ghtupdate', function(e, $div) {
        refreshFromInput();
        $div.on('click', '#add-entry', function(e) {
            var productName = $div.find('#id_product option:selected').html(),
                productData = {name: productName},
                productId;
            $div.find('#entry-form :input').each(function() {
                var val = $(this).val();
                if ($(this).attr('type') == 'number')
                    val = parseInt(val);
                productData[$(this).attr('name')] = val;
                if (this.tagName != 'SELECT') $(this).val('');
            });
            productId = parseInt(productData['product']);
            if (isNaN(productId)) return;
            cart.push(productData);
            refreshItems();
        });

        $div.on('click', '.delete-link', function() {
            var parentRow = $(this).parents('.order-item-row');
            removeEntry(parseInt(parentRow.data('row-idx')));
            return false;
        });

        function refreshFromInput() {
            var data = $div.find('#id_entries').val(),
                parsed;
            cart = [];
            if (data) {
                parsed = JSON.parse(data);
                $.each(parsed, function(idx, entryData) {
                    cart.push(entryData);
                });
            }
            refreshItems();
        }

        function refreshItems() {
            var itemcart = $div.find('#item-cart'),
                content = itemcart.find('.cart-content'),
                template = itemcart.find('.order-item-row.hidden');
            content.html('');
            $.each(cart, function(idx, entryData) {
                if (entryData == null) return;
                var cloned = template.clone();
                // Populate fields.
                $.each(entryData, function (field, value) {
                    cloned.find('[data-ship-field=' + field + ']').html(value + "&nbsp;");
                });
                cloned.removeClass('hidden');
                cloned.data('row-idx', idx);
                content.append(cloned);
                content.append('<br><br>');
            });
            updateInput();
        }

        function removeEntry(idx) {
            cart.splice(idx, 1);
            refreshItems();
        }

        function updateInput() {
            var serializedEntries = [], dataInput = $div.find('#id_entries');
            $.each(cart, function(idx, entryData) {
                if (entryData == null) return;
                serializedEntries.push(entryData);
            });
            dataInput.val(JSON.stringify(serializedEntries));
        }
    });
})();