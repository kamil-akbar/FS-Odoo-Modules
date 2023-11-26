# -*- coding: utf-8 -*-

{
    'name': "Advance Hotel Management System",
    'summary': """Manage booking reservations, guest check-in/checkout, room assignment, managing room, and billing.
                and front-office , Staffing shifts or leaves or attendance , Banquest Booking, Restuarant, Laundry, Housekeeping, Transport and Amenities
                Hotel Management System
                Online booking
                Online Enquiry
                Hotel Reservation
                Hotel Booking
                Hall Booking,
                Room Booking
                Banquest Booking
                Restuarant Booking
                Manage Housekeeping
                Amenities
                Transport Booking
                Laundry Booking
                Kitchen Order ticket
                hotel property management
                Manage front-office 
                Cloud Software Solution
                On-Premise Hotel Solution
                Hotel Web Booking Engine Software
                Hotel Front Desk System
                Hotel Housekeeping Solution
                Hotel Channel Management System
                Hotel Billing and Invoicing Software
                Hotel Reporting and Analytics Solutions
    """,
    'description': """Manage Hotel, Room Booking, Hall Booking, Restuarant, Laundry, Housekeeping and Amenities""",
    'category': 'Industries',
    'author':'Preciseways',
    'website': "http://www.preciseways.com",
    'depends':['account', 'hr', 'sale','product', 'hr_attendance', 'hr_holidays', 'website_sale'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
        'data/sequence.xml',
        'data/data.xml',
        'reports/booking_report.xml',
        'reports/booking_inquiry_report.xml',
        'reports/room_booked_per_day.xml',
        'reports/booking_draft_report.xml',
        'reports/report_action.xml',
        'reports/kitchen_table_order.xml',
        'data/hotel_email.xml',
        'wizards/booking_report.xml',
        'wizards/booking_invoice_view.xml',
        'wizards/room_cancellation_view.xml',
        'wizards/booking_inquiry_payment.xml',
        'wizards/room_change_view.xml',
        'wizards/booking_payment.xml',
        'wizards/all_booking_report.xml',
        'wizards/room_available_view.xml',
        'views/assets.xml',
        'views/hotel_room_views.xml',
        'views/hotel_floor_views.xml',
        'views/report_action.xml',
        'views/hotel_room_type_views.xml',
        'views/hotel_room_category_views.xml',
        'views/hotel_customer_details_views.xml',
        'views/hotel_room_details_views.xml',
        'views/hotel_booking_views.xml',
        'views/hotel_booking_proof_details_views.xml',
        'views/hotel_room_facilities_views.xml',
        'views/hotel_transport_driver_views.xml',
        'views/hotel_transport_vehicle_views.xml',
        'views/hotel_transport_vehicle_type_views.xml',
        'views/hotel_transport_location_views.xml',
        'views/hotel_transport_views.xml',
        'views/hotel_laundry_service_type_views.xml',
        'views/hotel_laundry_service_details_views.xml',
        'views/hotel_housekeeping_views.xml',
        'views/hotel_staff_views.xml',
        'views/hotel_restaurant_views.xml',
        'views/hotel_restaurant_food_item_views.xml',
        'views/hotel_restaurant_customer_food_order_views.xml',
        'views/hotel_laundry_item_views.xml',
        'views/hotel_restaurant_food_category_views.xml',
        'views/hotel_restaurant_table_details_views.xml',
        'views/hotel_hall_booking_views.xml',
        'views/hotel_hall_views.xml',
        'views/hotel_extra_services_views.xml',
        'views/product_product.xml',
        'views/hotel_room_amenities.xml',
        'views/hotel_restaurant_reservation.xml',
        'views/hotel_bar_view.xml',
        'views/menus.xml',
        'views/website_view.xml',
        'views/website.xml',
        'views/booking_inquiry_view.xml',
        'views/image_view.xml',
        'views/booking_cancellation_template.xml',
        'views/booking_confirmation_template.xml',
        'views/portal_booking_view.xml',
        'views/terms.xml',
    ],
    'assets': {
        'web.assets_frontend': [
          'pways_advance_hotel_management/static/src/scss/website_css.scss',
          'pways_advance_hotel_management/static/src/js/custom.js',
          'pways_advance_hotel_management/static/src/js/product.js',
        ],
        'web.assets_backend': [
            'pways_advance_hotel_management/static/src/css/dashboard.css',
            'pways_advance_hotel_management/static/src/css/style.scss',
            'pways_advance_hotel_management/static/src/css/style.css',
            'pways_advance_hotel_management/static/src/js/hotel.js',
            'pways_advance_hotel_management/static/src/xml/template.xml',
        ],
    },
    'images': ['static/description/banner.png'],
    'application': True,
    'installable': True,
    'price': 170,
    'currency': 'EUR',
    'license': 'OPL-1',
}
