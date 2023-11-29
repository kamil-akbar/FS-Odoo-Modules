odoo.define('pways_advance_hotel_management.product', function (require) {
    'use strict'; 
    var publicWidget = require('web.public.widget');
    const searchParams = new URLSearchParams(window.location.search);
    require('website_sale.website_sale');
    var checkin = $('#checkin');
    var checkout = $('#checkout');
    var arrival = $('#arrival_date');
    var departure = $('#departure_date')
    var rpc = require('web.rpc');
    var core = require('web.core'); 
    function formatDate(datetimeString, timePortion) {
        return datetimeString + timePortion;
    }

    publicWidget.registry.WebsiteSale.include({ 
        _updateRootProduct($form, productId) {
            this._super(...arguments);
            var timePortionCheckin = ' 14:00:00'; 
            var timePortionCheckout = ' 11:00:00'; 

            if (searchParams.has('checkin') && searchParams.has('checkout')) {   
                this.rootProduct['checkin'] = formatDate(checkin.val(), timePortionCheckin);
                this.rootProduct['checkout'] = formatDate(checkout.val(), timePortionCheckout);
            } else if (checkin.val() && checkout.val()) {
                this.rootProduct['checkin'] = formatDate(checkin.val(), timePortionCheckin);
                this.rootProduct['checkout'] = formatDate(checkout.val(), timePortionCheckout);
            } else if (arrival && departure) {
                this.rootProduct['checkin'] = formatDate(arrival.val(), timePortionCheckin);
                this.rootProduct['checkout'] = formatDate(departure.val(), timePortionCheckout);
            }
        }
    });

    publicWidget.registry.websiteSaleCustom = publicWidget.Widget.extend({
        selector : '#product_detail_main', 
        start: function () { 
            this._super.apply(this, arguments);
            var quantity = parseInt($('.quantity').val());
            var productId = parseInt($('input[name="product_id"]').val());
            var today = new Date();
            var targetDate = new Date('2023-12-11');
            if (today < targetDate) {
                today = targetDate;
            }
            var arrivalDate = new Date(arrival.val());
            var departureDate = new Date(departure.val());

            rpc.query({
                route: '/product/room',
                params: { product : productId, },
                }).then(function (result) {
                if (result < quantity || arrivalDate < today || departureDate < today ) {
                $('.js_check_product').prop('disabled', true);  
                $('.js_check_product').removeClass('disabled_cart');
                $('.js_check_product').css('background-color','#D8D8D8'); 
                } else {
                    $('.js_check_product').prop('disabled', false);
                    $('.js_check_product').addClass('disabled_cart').css('background-color', ); 
                }
            });
    } });

   $('.category-link').on('click', function (e) {
        e.preventDefault();
        const category = $(this).data('category');
        const url = `/room?category=${category}`;
        window.location.href = url;
    });

    // Get the current date
    var today = new Date();

    // Set the target date to December 11, 2023
    var targetDate = new Date('2023-12-11');

    // Check if today is before the target date
    if (today < targetDate) {
        // If before the target date, set today to the target date
        today = targetDate;
    }

    // Add 3 months to the current date
    var allowed_date_max = new Date(today);
    allowed_date_max.setMonth(today.getMonth() + 3);

    // Convert to ISO 8601 format and extract the date part
    allowed_date_max = allowed_date_max.toISOString().split('T')[0];

    var allowed_date_min = new Date().toISOString().split('T')[0];

    // Set the selected date to "today"
    $('#checkin').datetimepicker({
        setDate: today,
        format: 'YYYY-MM-DD',  // Set the desired date format
        // Add any additional DateTimePicker options as needed
    });

    // Set the selected date to "today"
    $('#checkout').datetimepicker({
        setDate: today,
        format: 'YYYY-MM-DD',  // Set the desired date format
        // Add any additional DateTimePicker options as needed
    });

    // Set the selected date to "today"
    $('#arrival_date').datetimepicker({
        setDate: today,
        format: 'YYYY-MM-DD',  // Set the desired date format
        // Add any additional DateTimePicker options as needed
    });

    // Set the selected date to "today"
    $('#departure_date').datetimepicker({
        setDate: today,
        format: 'YYYY-MM-DD',  // Set the desired date format
        // Add any additional DateTimePicker options as needed
    });

    $('#checkin').attr('min', allowed_date_min);
    $('#checkout').attr('min', allowed_date_min);
    $('#arrival_date').attr('min', allowed_date_min);
    $('#departure_date').attr('min', allowed_date_min);

    $('#checkin').attr('max', allowed_date_max);
    $('#checkout').attr('max', allowed_date_max);
    $('#arrival_date').attr('max', allowed_date_max);
    $('#departure_date').attr('max', allowed_date_max);

});

