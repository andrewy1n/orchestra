import { currentRoute, type Route } from "../../router";

class Navigation {
	route: Route = $state(currentRoute());

	reset() {
		this.route = currentRoute();
	}

	listen(): () => void {
		const sync = () => {
			this.route = currentRoute();
		};
		window.addEventListener("hashchange", sync);
		return () => window.removeEventListener("hashchange", sync);
	}
}

export const navigation = new Navigation();
