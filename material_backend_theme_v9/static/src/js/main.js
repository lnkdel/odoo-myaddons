odoo.define('web.MaterialBackendThemeMenu', function (require) {
    "use strict";

    var core = require('web.core');
    var session = require('web.session');
    var Menu = require('web.Menu');  
    

    Menu.include({

        bind_menu: function () {
            console.log("bind_menu");
            // $('#main-menu').smartmenus();
            var self = this;
             $(".oe_app").click(function(){
         		    var appname = $(this).find('.oe_app_caption').html();
				    $('.app-title').text(appname);
				    $("a[data-action-model]").click(function(){
				        $("#oe_main_menu_placeholder").removeClass("in");
				        var title = $(this).find('.oe_menu_text').html();
				        $('.app-title').text(appname + '/' + title);
				    });
				});
 
            var body = self.$el.parents('body');
            if ($('nav ul li.tnav ul').closest("li").children("ul").length) {
                 $('nav ul li.tnav ul').closest("li").children("ul li a").append('<b class="caret"></b>');
            }
            $('nav#oe_main_menu_navbar ul li ul.oe_secondary_submenu').addClass("tnav");
            body.on('click', '#appsbar_toggle', function (event) {
                event.preventDefault();
                $(this).toggleClass('fa-chevron-left');
                body.find('.oe_appsbar').toggleClass('hide');
                $(".navbar-collapse.collapse.in").removeClass("in");
            });
            //App And Menu Name In Top Title
            $(".o_planner_systray").show();
            

            $(".navbar-toggle").click(function(){
                $("#right_menu_bar").addClass("hide");
                $("#right_menu_bar").addClass("collapse in");
                $("#oe_main_menu_placeholder").removeClass("hide");
                 $(".fa.fa-th.fa-chevron-left").removeClass("fa-chevron-left");
            });

            $("a[data-action-model]").click(function(){
                    $(".navbar-collapse.collapse.in").removeClass("in");
            });
            

            this.$secondary_menus = this.$el.parents().find('.oe_secondary_menus_container');

            this.$secondary_menus.on('click', 'a[data-menu]', this.on_menu_click);
            this.$el.on('click', 'a[data-menu]', function (event) {
                event.preventDefault();
                var menu_id = $(event.currentTarget).data('menu');
                var needaction = $(event.target).is('div#menu_counter');
                core.bus.trigger('change_menu_section', menu_id, needaction);
            });
    
            this.trigger('menu_bound');
    
            // var lazyreflow = _.debounce(this.reflow.bind(this), 200);
            // core.bus.on('resize', this, function() {
            //     if ($(window).width() < 768 ) {
            //         lazyreflow('all_outside');
            //     } else {
            //         lazyreflow();
            //     }
            // });
            // core.bus.trigger('resize');
    
            this.is_bound.resolve();
        },

        /**
        * Opens a given menu by id, as if a user had browsed to that menu by hand
        * except does not trigger any event on the way
        *
        * @param {Number} id database id of the terminal menu to select
        */
        open_menu: function (id) {
            console.log("open_menu");
            var self = this;
            
            this.current_menu = id;
            session.active_id = id;
            var $clicked_menu, $sub_menu, $main_menu;
            $clicked_menu = this.$el.add(this.$secondary_menus).find('a[data-menu=' + id + ']');
            this.trigger('open_menu', id, $clicked_menu);
    
            if (this.$secondary_menus.has($clicked_menu).length) {
                $sub_menu = $clicked_menu.parents('.oe_secondary_menu');
                $main_menu = this.$el.find('a[data-menu=' + $sub_menu.data('menu-parent') + ']');
            } else {
                $sub_menu = this.$secondary_menus.find('.oe_secondary_menu[data-menu-parent=' + $clicked_menu.attr('data-menu') + ']');
                $main_menu = $clicked_menu;
            }
            

            
             
            $('.oe_appsbar').addClass('hide');
            // Change icon to close
            $('#appsbar_toggle').removeClass('fa-chevron-left');
            // Hide all top menus
            $('.oe_application_menu_placeholder > ul').addClass('hide');
            // Find clicked menu top element
            var clicked_menu_top = $('.oe_application_menu_placeholder a[data-menu=' + id + ']');
            // Show clicked app
            if (clicked_menu_top.length > 0) {
                clicked_menu_top.parents(".hide").removeClass('hide');
            } else {
                $('.oe_application_menu_placeholder > ul[data-menu-parent=' + id + ']').removeClass('hide');
            }
            
            // Activate current main menu
            // this.$el.find('.active').removeClass('active');
            // $main_menu.parent().addClass('active');
    
            // Show current sub menu
            // this.$secondary_menus.find('.oe_secondary_menu').hide();
            // $sub_menu.show();
    
            // Hide/Show the leftbar menu depending of the presence of sub-items
            //this.$secondary_menus.parent('.oe_leftbar').toggle(!!$sub_menu.children().length);
    
            // Activate current menu item and show parents
            // this.$secondary_menus.find('.active').removeClass('active');
            // if ($main_menu !== $clicked_menu) {
            //     $clicked_menu.parents().show();
            //     if ($clicked_menu.is('.oe_menu_toggler')) {
            //         $clicked_menu.toggleClass('oe_menu_opened').siblings('.oe_secondary_submenu:first').toggle();
            //     } else {
            //         $clicked_menu.parent().addClass('active');
            //     }
            // }
            // add a tooltip to cropped menu items
            // this.$secondary_menus.find('.oe_secondary_submenu li a span').each(function() {
            //     $(this).tooltip(this.scrollWidth > this.clientWidth ? {title: $(this).text().trim(), placement: 'right'} :'destroy');
            // });
        },

        /**
        * Process a click on a menu item
        *
        * @param {Number} id the menu_id
        * @param {Boolean} [needaction=false] whether the triggered action should execute in a `needs action` context
        */
        menu_click: function(id, needaction) {
            console.log("menu_click");
            
            if (!id) { return; }

            // find back the menuitem in dom to get the action
            var $item = this.$el.find('a[data-menu=' + id + ']');
            if (!$item.length) {
                $item = this.$secondary_menus.find('a[data-menu=' + id + ']');
            }
            var action_id = $item.data('action-id');

            //$item.parents(".hide").removeClass('hide')

            // If first level menu doesnt have action trigger first leaf
            if (!action_id) {
                if(this.$el.has($item).length) {
                    var $sub_menu = this.$secondary_menus.find('.oe_secondary_menu[data-menu-parent=' + id + ']');
                    var $items = $sub_menu.find('a[data-action-id]').filter('[data-action-id!=""]');
                    if($items.length) {
                        action_id = $items.data('action-id');
                        id = $items.data('menu');
                    }
                }
            }
            if (action_id) {
                this.trigger('menu_click', {
                    action_id: action_id,
                    needaction: needaction,
                    id: id,
                    previous_menu_id: this.current_menu // Here we don't know if action will fail (in which case we have to revert menu)
                }, $item);
            } else {
                console.log('Menu no action found web test 04 will fail');
            }
            this.open_menu(id);
        },
        
        /**
        * Change the current top menu
        *
        * @param {int} [menu_id] the top menu id
        * @param {boolean} [needaction] true to redirect to menu's needactions
        */
        on_change_top_menu: function(menu_id, needaction) {
            console.log("on_change_top_menu");
            var self = this;
            // Fetch the menu leaves ids in order to check if they need a 'needaction'
            var $secondary_menu = this.$el.parents().find('.oe_secondary_menu[data-menu-parent=' + menu_id + ']');
            var $menu_leaves = $secondary_menu.children().find('.oe_menu_leaf');
            var menu_ids = _.map($menu_leaves, function (leave) {return parseInt($(leave).attr('data-menu'), 10);});
    
            self.do_load_needaction(menu_ids).then(function () {
                self.trigger("need_action_reloaded");
            });
            this.$el.parents().find(".oe_secondary_menus_container").scrollTop(0,0);
    
            this.menu_click(menu_id, needaction);
        },
        
        reflow: function (behavior) {
            console.log("reflow");
            // var self = this;
            // var $more_container = this.$('#menu_more_container').hide();
            // var $more = this.$('#menu_more');
            // var $systray = this.$el.parents().find('.oe_systray');
            // $more.children('li').insertBefore($more_container);  // Pull all the items out of the more menu
            // // 'all_outside' beahavior should display all the items, so hide the more menu and exit
            // if (behavior === 'all_outside') {
            //     this.$el.find('li').show();
            //     $more_container.hide();
            //     return;
            // }

            // // Hide all menu items
            // var $toplevel_items = this.$el.find('li.tnav').not($more_container).not($systray.find('li')).hide();
            // // Show list of menu items (which is empty for now since all menu items are hidden)
            // self.$el.show();
            // $toplevel_items.each(function () {
            //     // In all inside mode, we do not compute to know if we must hide the items, we hide them all
            //     if (behavior === 'all_inside') {
            //         return false;
            //     }
            //     var remaining_space = self.$el.parent().width() - $more_container.outerWidth();
            //     self.$el.parent().children(':visible').each(function () {
            //         remaining_space -= $(this).outerWidth() + 15;
            //     });

            //     if ($(this).width() > remaining_space) {
            //         return false; // the current item will be appended in more_container
            //     }
            //     $(this).show(); // show the current item in menu bar
            // });
            // $more.append($toplevel_items.filter(':hidden').show());
            // $more_container.toggle(!!$more.children().length || behavior === 'all_inside');
            // // Hide toplevel item if there is only one
            // var $toplevel = self.$el.children("li.tnav:visible");
            // if ($toplevel.length === 1 && behavior != 'all_inside') {
            //     $toplevel.hide();
            // }
        }

    });
});