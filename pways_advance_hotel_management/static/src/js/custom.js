odoo.define('pways_advance_hotel_management.custom', function (require) {
    'use strict';
    const searchParams = new URLSearchParams(window.location.search);
    const checkinInput = document.getElementById("checkin");
    const checkoutInput = document.getElementById("checkout");
    var publicWidget = require('web.public.widget');
    var arrival = $('#arrival_date');
    var departure = $('#departure_date');
    publicWidget.registry.WebsiteSaleCustom = publicWidget.Widget.extend({
        selector: '.o_wsale_products_main_row',
        start: function () {
            this._super.apply(this, arguments);
            if (!searchParams.has('checkin') && !searchParams.has('checkout')) {
                rpc.query({
                    route: '/refrence1/product/',
                }).then(function (result) {

                });
            }
        }
    });

    if (checkinInput && checkoutInput) {
        var today = new Date();
        var tomorrow = new Date();
        tomorrow.setDate(today.getDate() + 1);
        var formattedToday = today.toISOString().slice(0, 10);
        var formattedTomorrow = tomorrow.toISOString().slice(0, 10);

        checkinInput.value = formattedToday;
        checkoutInput.value = formattedTomorrow;
    }
    $('#checkin').on('change', function() {
        var checkinValue = $('#checkin').val();
        var checkinDate = new Date(checkinValue);

        if (!isNaN(checkinDate.getTime())) {
            var checkoutDate = new Date(checkinDate); 
            checkoutDate.setDate(checkinDate.getDate() + 1); 

            var formattedCheckout = checkoutDate.toISOString().slice(0, 10);
            $('#checkout').val(formattedCheckout); 
        } else {
            console.log("Invalid date input");
        }
    });

    $('#pay_now').on('click',function() {
        $('.paynow').click();
    });

    $('#arrival_date').on('change', function() {
        var arrivalValue = $('#arrival_date').val();
        var arrivalDate = new Date(arrivalValue);

        if (!isNaN(arrivalDate.getTime())) {
            var departureDate = new Date(arrivalDate);
            departureDate.setDate(arrivalDate.getDate() + 1);
            var formattedArrival = arrivalDate.toISOString().slice(0, 10);
            var formattedDeparture = departureDate.toISOString().slice(0, 10);
            $('#departure_date').val(formattedDeparture);
        } else {
            console.log("Invalid date input");
        }
    });


    const arrivalDateInput = document.getElementById("arrival_date");
    const departureDateInput = document.getElementById("departure_date");

    if (arrivalDateInput && departureDateInput) {
        var today = new Date();
        var tomorrow = new Date();
        tomorrow.setDate(today.getDate() + 1);
        var formattedToday = today.toISOString().slice(0, 10);
        var formattedTomorrow = tomorrow.toISOString().slice(0, 10);

        arrivalDateInput.value = formattedToday;
        departureDateInput.value = formattedTomorrow;
    }
    $('.quantity').on('change', function(){
        var quantity = parseInt($('.quantity').val());
        var productId = parseInt($('input[name="product_id"]').val());
        rpc.query({
            route: '/refrence2/product/',
            params: { product: productId },
        }).then(function (result) {
            if (result < quantity) {             
                $('.js_check_product').prop('disabled', true);
                $('.js_check_product').addClass('disabled_cart').css('background-color', '#D8D8D8'); 
            } else {
                $('.js_check_product').prop('disabled', false);  
                $('.js_check_product').removeClass('disabled_cart');
                $('.js_check_product').css('background-color', ''); 
            }
        }); 
        
    });
    $('#modal_button').addClass('disabled');
    $('#modal_button').css('backgroundColor', '#D8D8D8');
    var terms_radio = $('#agree_terms');
    terms_radio.on('change', function() {
        if (terms_radio.prop('checked')) {
        $('button[name="o_payment_submit_button"]').prop('disabled', false);
        $('button[name="o_payment_submit_button"]').css('backgroundColor', '#35979c');
        $('#modal_button').removeClass('disabled')
        $('#modal_button').css('backgroundColor', '#35979c');
    }else{
        $('button[name="o_payment_submit_button"]').prop('disabled', true);
        $('button[name="o_payment_submit_button"]').addClass('disabled_cart').css('background-color', '#D8D8D8');
        $('#modal_button').addClass('disabled');
        $('#modal_button').css('backgroundColor', '#D8D8D8');
    } 
    });
    $('button[name="o_payment_submit_button"]').prop('disabled', true);
    $('button[name="o_payment_submit_button"]').addClass('paynow');
    $('button[name="o_payment_submit_button"]').addClass('disabled_cart').css('background-color', '#D8D8D8');
    $('#modal_button').addClass('disabled');
    $('#modal_button').css('backgroundColor', '#D8D8D8');
    var rpc = require('web.rpc');
    var core = require('web.core');
    if (searchParams.has('checkin') && searchParams.has('checkout')) {
        $('#checkin').val(searchParams.get('checkin'));
        $('#checkout').val(searchParams.get('checkout'));
    }
    $('#available_check').on('click', function() {
        var checkin = $('#checkin').val();
        var checkout = $('#checkout').val();
        searchParams.delete("checkin");
        searchParams.delete("checkout");
        searchParams.delete("type");
        searchParams.set("checkin", checkin);
        searchParams.set("checkout",checkout);
        window.location.search = searchParams.toString();
    });
});
