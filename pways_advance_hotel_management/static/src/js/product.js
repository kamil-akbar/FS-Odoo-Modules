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
            rpc.query({
                route: '/product/room',
                params: { product : productId, },
                }).then(function (result) {
                if (result < quantity) {
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
    var today = new Date().toISOString().split('T')[0];
    $('#checkin').attr('min', today);
    $('#checkout').attr('min', today);
    $('#arrival_date').attr('min', today);
    $('#departure_date').attr('min', today);
});

