
odoo.define('pways_advance_hotel_management.hotelDashboard', function (require) {
  'use strict';

  const AbstractAction = require('web.AbstractAction');
  const ajax = require('web.ajax');
  const core = require('web.core');
  const rpc = require('web.rpc');
  const session = require('web.session')
  const web_client = require('web.web_client');
  const _t = core._t;
  const QWeb = core.qweb;
  const ActionMenu = AbstractAction.extend({
    template: 'hotelDashboard',
    events: {
      'click .active_booking': 'view_active_booking',
      'click .action-food': 'view_actions_food',
      'click .action-transports': 'view_action_transports',
      'click .action-hall': 'view_action_hall',
      'click .today-check-in': 'view_today_check_in',
      'click .today-check-out': 'view_today_check_out',
      'click .action-laundry':'view_action_laundry',
      'click .action-booking':'view_action_booking',
      'click .action-staff':'view_action_staff',
      'click .action-driver':'view_action_driver',
      'click .action-staff-attandance':'view_action_attandance',
      'click .action-staff-leave':'view_action_leave',
      'click .action-housekeeping':'view_action_housekeeping',
      'click .action-table-book':'view_action_table_book',
      'click .action-order-food':'view_action_order_food',
      'click .action-amenities':'view_action_amenities',
      'click .action-staff-available':'view_action_staff_available',
      'click .action-inquiry' : 'view_active_booking_inquiry',
    },
    renderElement: function (ev) {
      const self = this;
      $.when(this._super())
        .then(function (ev) {
          rpc.query({
            model: "hotel.booking",
            method: "get_hotel_stats",
          }).then(function (result) {
            $('#active_booking_count').empty().append(result['active_booking_count']);
            $('#food_count').empty().append(result['food_count']);
            $('#transports_count').empty().append(result['transports_count']);
            $('#hall_count').empty().append(result['hall_count']);
            $('#today_check_in').empty().append(result['today_check_in']);
            $('#today_check_out').empty().append(result['today_check_out']);
            $('#laundry_count').empty().append(result['laundry_count']);
            $('#table_count').empty().append(result['table_count']);
            $('#staff_count').empty().append(result['staff_count']);
            $('#driver_count').empty().append(result['driver_count']);
            $('#attendance_count').empty().append(result['attendance_count']);
            $('#leave_count').empty().append(result['leave_count']);
            $('#house_count').empty().append(result['house_count']);
            $('#book_count').empty().append(result['book_count']);
            $('#order_count').empty().append(result['order_count']);
            $('#amenities_count').empty().append(result['amenities_count']);
            $('#staff_available_count').empty().append(result['staff_available_count']);
            $('#company').empty().append(result['company']);
            $('#inquiry_count').empty().append(result['inquiry_count']);

          });
        });
    },
    view_active_booking: function (ev) {
      ev.preventDefault();
      return this.do_action({
        name: _t('Active Appointment'),
        type: 'ir.actions.act_window',
        res_model: 'hotel.booking',
        domain: ['|',['stages', '=', 'Confirm'],['stages', '=', 'check_in']],
        views: [[false, 'list'], [false, 'form']],
        target: 'current'
      });
    },
    view_active_booking_inquiry: function(ev) {
      ev.preventDefault();
      return this.do_action({
        name: _t('Booking'),
        type: 'ir.actions.act_window',
        res_model: 'booking.inquiry',
        domain: [['state','=','draft']],
        views : [[false, 'list'],[false,'form']],
        target: 'current',
      });
    },
    view_actions_food: function (ev) {
      ev.preventDefault();
      return this.do_action({
        name: _t('Food'),
        type: 'ir.actions.act_window',
        res_model: 'hotel.restaurant',
        domain: [['stages', '=', 'Confirm']],
        views: [[false, 'list'], [false, 'form']],
        target: 'current'
      });
    },
    view_action_transports: function (ev) {
      ev.preventDefault();
      return this.do_action({
        name: _t('Transport'),
        type: 'ir.actions.act_window',
        res_model: 'hotel.transport',
        domain: [['stage', '=', 'pending']],
        views: [[false, 'list'], [false, 'form']],
        target: 'current'
      });
    },
    view_action_hall: function (ev) {
      ev.preventDefault();
      return this.do_action({
        name: _t('Hall'),
        type: 'ir.actions.act_window',
        res_model: 'hotel.feast',
        domain: [['stages', '=', 'Confirm']],
        views: [[false, 'list'], [false, 'form']],
        target: 'current'
      });
    },
    view_action_laundry: function (ev) {
      ev.preventDefault();
      return this.do_action({
        name: _t('Laundry'),
        type: 'ir.actions.act_window',
        res_model: 'laundry.service',
        domain: [['stages', '=', 'In Progress']],
        views: [[false, 'list'], [false, 'form']],
        target: 'current'
      });
    },
    view_action_booking: function (ev) {
      ev.preventDefault();
      return this.do_action({
        name: _t('Table Booking'),
        type: 'ir.actions.act_window',
        res_model: 'hotel.restaurant.reservation',
        domain: [['state', '=', 'order']],
        views: [[false, 'list'], [false, 'form']],
        target: 'current'
      });
    },    
    view_action_table_book: function (ev) {
      ev.preventDefault();
      return this.do_action({
        name: _t('Table Available'),
        type: 'ir.actions.act_window',
        res_model: 'table.details',
        domain: [['stages', '=', 'Available']],
        views: [[false, 'list'], [false, 'form']],
        target: 'current'
      });
    },
    view_action_order_food: function (ev) {
      ev.preventDefault();
      return this.do_action({
        name: _t('Order Details'),
        type: 'ir.actions.act_window',
        res_model: 'hotel.reservation.order',
        domain: [['state', '=', 'order']],
        views: [[false, 'list'], [false, 'form']],
        target: 'current'
      });
    },
    view_action_amenities: function (ev) {
      ev.preventDefault();
      return this.do_action({
        name: _t('Amenities Details'),
        type: 'ir.actions.act_window',
        res_model: 'hotel.room.amenities',
        // domain: [['product_id', '=', true]],
        views: [[false, 'list'], [false, 'form']],
        target: 'current'
      });
    },    
    view_action_staff: function (ev) {
      ev.preventDefault();
      return this.do_action({
        name: _t('Hotel Staff'),
        type: 'ir.actions.act_window',
        res_model: 'hr.employee',
        domain: [['is_staff', '=', true]],
        views: [[false, 'list'], [false, 'form']],
        target: 'current'
      });
    },
    view_action_staff_available: function (ev) {
      ev.preventDefault();
      return this.do_action({
        name: _t('Hotel Staff Available'),
        type: 'ir.actions.act_window',
        res_model: 'hr.employee',
        domain: [['is_staff', '=', true],['active','=',true],['is_absent','!=',true]],
        views: [[false, 'list'], [false, 'form']],
        target: 'current'
      });
    },
    view_action_attandance: function (ev) {
      ev.preventDefault();
      let today = new Date();
      let end = new Date(today.setDate(today.getDate()));
      let domain = [['check_in', '=', end]]

      return this.do_action({
        name: _t('Hotel Staff Attendance'),
        type: 'ir.actions.act_window',
        res_model: 'hr.attendance',
        domain: domain,
        views: [[false, 'list'], [false, 'form']],
        target: 'current'
      });
    },
    view_action_leave: function (ev) {
      ev.preventDefault();
      return this.do_action({
        name: _t('Hotel Staff Leave'),
        type: 'ir.actions.act_window',
        res_model: 'hr.leave',
        domain: [['state', '=', 'confirm']],
        views: [[false, 'list'], [false, 'form']],
        target: 'current'
      });
    },
    view_action_housekeeping: function (ev) {
      ev.preventDefault();
      return this.do_action({
        name: _t('Hotel Housekeeping'),
        type: 'ir.actions.act_window',
        res_model: 'hotel.housekeeping',
        domain: [['state', '=', 'Assign']],
        views: [[false, 'list'], [false, 'form']],
        target: 'current'
      });
    },

    view_today_check_in: function (ev) {
      ev.preventDefault();
      let today = new Date();
      let start = new Date(today);
      let end = new Date(today.setDate(today.getDate() + 1));
      start.setHours(0, 0, 0, 0);
      end.setHours(0, 0, 0, 0);
      let domain = [['check_in', '>=', start], ['check_in','<',end], ['stages', '=', 'Booked']]
      return this.do_action({
        name: _t('Check In'),
        type: 'ir.actions.act_window',
        res_model: 'hotel.room.details',
        domain: domain,
        views: [[false, 'list'], [false, 'form']],
        target: 'current'
      });
    },
    view_today_check_out: function (ev) {
      ev.preventDefault();
      let today = new Date();
      let start = new Date(today);
      let end = new Date(today.setDate(today.getDate() + 1));
      start.setHours(0, 0, 0, 0);
      end.setHours(0, 0, 0, 0);
      let domain = [['check_out', '>=', start], ['check_out','<',end], ['stages', '=', 'Booked']]
      return this.do_action({
        name: _t('Check In'),
        type: 'ir.actions.act_window',
        res_model: 'hotel.room.details',
        domain: domain,
        views: [[false, 'list'], [false, 'form']],
        target: 'current'
      });
    },
    get_action: function (ev, name, res_model) {
      ev.preventDefault();
      return this.do_action({
        name: _t(name),
        type: 'ir.actions.act_window',
        res_model: res_model,
        views: [[false, 'tree'], [false, 'form']],
        target: 'current'
      });
    },
  willStart: function () {
       const self = this;
            return this._super()
            .then(function() {});
        },
  });
  // core.action_registry.add('hotel_dashboard', ActionMenu);
  // return hotelDashboard;
  core.action_registry.add('hotel_dashboard', ActionMenu);
  return ActionMenu;
});


   
