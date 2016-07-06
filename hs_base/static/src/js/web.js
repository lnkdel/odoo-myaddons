openerp.hs_base = function(instance){

    // allow drag modal window
    instance.web.Dialog.include({
            open: function () {
                var self = this;
                this._super.apply(this, arguments);
                $(".modal.in").draggable({
                    handle: ".modal-header"
                });
                return this;
            }
        }
    );

    // display database name even not in debug mode.
    instance.web.UserMenu.include({
        do_update:function () {
            this._super();
            var self = this;
            this.update_promise.done(function () {
                if(instance.session.debug)
                    return;
                var topbar_name = self.$el.find('.oe_topbar_name').text();
                topbar_name = _.str.sprintf("%s (%s)",topbar_name,instance.session.db);
                self.$el.find('.oe_topbar_name').text(topbar_name);
            });
        }
    });

};
