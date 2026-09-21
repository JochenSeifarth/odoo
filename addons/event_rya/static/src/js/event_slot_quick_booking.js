import { rpc } from "@web/core/network/rpc";
import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

export class QuickSlotBooking extends Interaction {
    static selector = ".o_rya_quick_slot_booking";

    dynamicContent = {
        _root: { "t-on-click": this.onSlotClick },
    };

    async onSlotClick(ev) {
        ev.preventDefault();
        const modal = await this.waitFor(rpc(ev.currentTarget.dataset.registrationUrl));
        const modalEl = new DOMParser().parseFromString(modal, "text/html").body.firstChild;

        const ticketInputs = modalEl.querySelectorAll(".o_wevent_input_nb_tickets");
        if (ticketInputs.length === 1 && Number(ticketInputs[0].max) === 1) {
            const ticketForm = modalEl.querySelector("form");
            const attendeeModal = await this.waitFor(rpc(
                ticketForm.action,
                Object.fromEntries(new FormData(ticketForm)),
            ));
            const attendeeModalEl = new DOMParser().parseFromString(attendeeModal, "text/html").body.firstChild;
            this.insert(attendeeModalEl, document.body);
            return;
        }

        this.insert(modalEl, document.body);
    }
}

registry
    .category("public.interactions")
    .add("event_rya.quick_slot_booking", QuickSlotBooking);
